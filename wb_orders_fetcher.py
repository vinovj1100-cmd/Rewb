#!/usr/bin/env python3
"""
Secure Wildberries Supplier Orders Fetcher

Fetches order data from the official Wildberries Statistics API
(https://statistics-api.wildberries.ru/api/v1/supplier/orders),
applies robust error handling, rate-limit compliance, pagination,
and stores results in a securely permissioned Excel file.

Security features:
  - Secrets loaded exclusively from environment / .env (never hardcoded)
  - Token presence and basic integrity validation
  - Sensitive values never written to logs
  - TLS verification enforced
  - Output files created with restrictive permissions (owner read/write only)
  - Configurable logging with no credential leakage
  - Automatic retry with exponential backoff and respect for Retry-After headers
  - Input validation for date parameters
"""

from __future__ import annotations

import logging
import os
import stat
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://statistics-api.wildberries.ru"
ENDPOINT = "/api/v1/supplier/orders"
URL = f"{BASE_URL}{ENDPOINT}"

# Official recommendation: identify orders primarily by srid
USEFUL_COLUMNS: Dict[str, str] = {
    "srid": "Order_SRID",
    "gNumber": "Basket_GNumber",
    "date": "Order_Date",
    "lastChangeDate": "Last_Updated",
    "warehouseName": "Dispatch_Warehouse",
    "countryName": "Client_Country",
    "oblastOkrugName": "Client_Region",
    "regionName": "Client_Region_Name",
    "supplierArticle": "Your_SKU",
    "nmId": "WB_Article",
    "barcode": "Product_Barcode",
    "category": "Product_Category",
    "subject": "Product_Subcategory",
    "brand": "Brand",
    "techSize": "Ordered_Size",
    "priceWithDisc": "Price_Paid_By_Client",
    "finishedPrice": "Finished_Price",
    "discountPercent": "Discount_Percentage",
    "spp": "WB_Discount",
    "isCancel": "Is_Cancelled",
    "cancelDate": "Cancel_Date",
    "incomeID": "Supply_ID",
    "sticker": "Sticker_ID",
}

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
USER_AGENT = "WB-Orders-Fetcher/2.0 (secure-local-integration; contact=local-admin)"

# ---------------------------------------------------------------------------
# Logging setup (no secrets ever logged)
# ---------------------------------------------------------------------------


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configure structured logging that never emits credentials."""
    logger = logging.getLogger("wb_orders")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Restrictive permissions on log file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        try:
            os.chmod(log_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        except OSError:
            pass

    return logger


# ---------------------------------------------------------------------------
# Configuration loader with validation
# ---------------------------------------------------------------------------


def load_config() -> Dict[str, Any]:
    """Load and validate configuration from environment variables."""
    load_dotenv()

    token = os.getenv("WB_API_TOKEN", "").strip()
    if not token or token == "your_actual_wildberries_token_here":
        raise ValueError(
            "WB_API_TOKEN is missing or still set to the placeholder value. "
            "Create a .env file from .env.example and supply a valid Statistics-category token."
        )
    if len(token) < 20:
        raise ValueError("WB_API_TOKEN appears too short to be a valid Wildberries token.")

    days_back = int(os.getenv("DAYS_BACK", "30"))
    if not 1 <= days_back <= 90:
        raise ValueError("DAYS_BACK must be between 1 and 90 (API retention limit).")

    flag = int(os.getenv("FLAG", "0"))
    if flag not in (0, 1):
        raise ValueError("FLAG must be 0 (incremental) or 1 (full day).")

    output_dir = Path(os.getenv("OUTPUT_DIR", "./output")).resolve()
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE") or None

    return {
        "token": token,
        "days_back": days_back,
        "flag": flag,
        "output_dir": output_dir,
        "log_level": log_level,
        "log_file": log_file,
    }


# ---------------------------------------------------------------------------
# Secure HTTP client with retries
# ---------------------------------------------------------------------------


class RateLimitError(Exception):
    """Raised when the API returns HTTP 429."""

    def __init__(self, retry_after: float = 60.0):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after:.1f}s")


class APIError(Exception):
    """Generic non-retriable API error."""


def _extract_retry_after(response: requests.Response) -> float:
    """Parse Retry-After or X-Ratelimit-Retry headers."""
    for header in ("Retry-After", "X-Ratelimit-Retry", "X-RateLimit-Retry"):
        value = response.headers.get(header)
        if value:
            try:
                return float(value)
            except ValueError:
                continue
    return 60.0


@retry(
    retry=retry_if_exception_type((requests.exceptions.RequestException, RateLimitError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=120) + wait_random(0, 2),
    reraise=True,
)
def _perform_request(
    session: requests.Session,
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
    logger: logging.Logger,
) -> List[Dict[str, Any]]:
    """Execute a single authenticated request with proper error handling."""
    response = session.get(url, headers=headers, params=params, timeout=(10, 60))

    if response.status_code == 401:
        raise APIError(
            "Authentication failed (401). Token is invalid, expired, or lacks "
            "Statistics category permissions."
        )
    if response.status_code == 403:
        raise APIError(
            "Access forbidden (403). Verify token type and selected data categories."
        )
    if response.status_code == 429:
        retry_after = _extract_retry_after(response)
        logger.warning("Rate limit exceeded (429). Waiting %.1f seconds before retry.", retry_after)
        time.sleep(retry_after)
        raise RateLimitError(retry_after)
    if response.status_code >= 500:
        logger.warning("Server error %s. Will retry.", response.status_code)
        response.raise_for_status()
    if response.status_code != 200:
        raise APIError(f"Unexpected status {response.status_code}: {response.text[:300]}")

    data = response.json()
    if not isinstance(data, list):
        raise APIError("API returned non-list JSON payload.")
    return data


# ---------------------------------------------------------------------------
# Core fetch logic with pagination
# ---------------------------------------------------------------------------


def fetch_all_orders(
    token: str,
    days_back: int,
    flag: int,
    logger: logging.Logger,
) -> List[Dict[str, Any]]:
    """
    Retrieve orders from the Wildberries Statistics API.

    For flag=0 the API may return up to ~80 000 rows per call.
    Subsequent pages are obtained by advancing dateFrom to the
    lastChangeDate of the final record of the previous page.
    """
    # Build dateFrom in Moscow time (API requirement)
    now_moscow = datetime.now(MOSCOW_TZ)
    date_from_dt = (now_moscow - timedelta(days=days_back)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    date_from = date_from_dt.isoformat()

    headers = {
        "Authorization": token,
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    session = requests.Session()
    session.verify = True  # Enforce TLS certificate validation

    all_orders: List[Dict[str, Any]] = []
    current_date_from = date_from
    page = 1

    logger.info(
        "Starting fetch: dateFrom=%s, flag=%d, days_back=%d",
        current_date_from,
        flag,
        days_back,
    )

    while True:
        params = {"dateFrom": current_date_from, "flag": flag}
        logger.info("Requesting page %d (dateFrom=%s) ...", page, current_date_from)

        try:
            batch = _perform_request(session, URL, headers, params, logger)
        except APIError as exc:
            logger.error("Non-retriable API error: %s", exc)
            raise
        except Exception as exc:
            logger.error("Request failed after retries: %s", exc)
            raise

        if not batch:
            logger.info("Empty response received — all available data retrieved.")
            break

        all_orders.extend(batch)
        logger.info("Page %d returned %d rows (total so far: %d)", page, len(batch), len(all_orders))

        # Pagination only meaningful for flag=0
        if flag == 1 or len(batch) < 1000:
            # Heuristic: small batch likely means end of data
            break

        # Advance cursor using lastChangeDate of the final record
        last_record = batch[-1]
        next_date = last_record.get("lastChangeDate")
        if not next_date or next_date <= current_date_from:
            logger.info("No further lastChangeDate progression possible. Stopping.")
            break

        current_date_from = next_date
        page += 1

        # Respect the documented 1-request-per-minute limit for this endpoint
        logger.debug("Sleeping 61 seconds to honour rate limit ...")
        time.sleep(61)

    session.close()
    logger.info("Fetch complete. Total rows: %d", len(all_orders))
    return all_orders


# ---------------------------------------------------------------------------
# Data transformation & secure persistence
# ---------------------------------------------------------------------------


def transform_to_dataframe(orders: List[Dict[str, Any]]) -> pd.DataFrame:
    """Select and rename relevant columns, preserving only existing fields."""
    if not orders:
        return pd.DataFrame()

    df = pd.DataFrame(orders)
    existing = {src: dst for src, dst in USEFUL_COLUMNS.items() if src in df.columns}
    if not existing:
        # Fallback: keep all columns if mapping is empty
        return df

    return df[list(existing.keys())].rename(columns=existing)


def save_secure_excel(df: pd.DataFrame, output_dir: Path, logger: logging.Logger) -> Path:
    """Write DataFrame to Excel with restrictive file permissions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(output_dir, stat.S_IRWXU)  # 0o700
    except OSError:
        pass

    timestamp = datetime.now(MOSCOW_TZ).strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"wb_client_orders_{timestamp}.xlsx"

    df.to_excel(filename, index=False, engine="openpyxl")

    # Restrict file to owner read/write only
    try:
        os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError as exc:
        logger.warning("Could not set restrictive permissions on %s: %s", filename, exc)

    logger.info("Saved %d rows to %s (permissions restricted to owner)", len(df), filename)
    return filename


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Orchestrate configuration, fetch, transform and secure save."""
    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = setup_logging(config["log_level"], config["log_file"])
    logger.info("Wildberries Orders Fetcher started (secure mode)")

    try:
        orders = fetch_all_orders(
            token=config["token"],
            days_back=config["days_back"],
            flag=config["flag"],
            logger=logger,
        )

        if not orders:
            logger.info("No orders found for the requested period.")
            return 0

        df = transform_to_dataframe(orders)
        save_secure_excel(df, config["output_dir"], logger)
        logger.info("Process completed successfully.")
        return 0

    except APIError as exc:
        logger.error("API error: %s", exc)
        return 2
    except Exception as exc:
        logger.exception("Unexpected failure: %s", exc)
        return 3


if __name__ == "__main__":
    sys.exit(main())
