# Secure Wildberries Supplier Orders Fetcher

A production-oriented Python utility that retrieves order data from the official Wildberries Statistics API (`/api/v1/supplier/orders`) and stores it in a securely permissioned Excel workbook.

## Key Improvements over the Original Script

| Area | Original Issue | Enhancement |
|------|----------------|-------------|
| Syntax | `if name == "__main__"` (NameError) | Corrected to `if __name__ == "__main__"` |
| Authentication | Basic presence check | Length validation + clear error messages; token never logged |
| Time zone | UTC with trailing Z | Moscow time (Europe/Moscow) as required by the API |
| Pagination | Single request only | Automatic cursor-based pagination using `lastChangeDate` (flag=0) |
| Rate limits | Fixed 0.5 s sleep | Respects 429 + `Retry-After` / `X-Ratelimit-Retry`; 61 s inter-page delay |
| Retries | None | Exponential backoff + jitter via `tenacity` (5 attempts) |
| Logging | `print` statements | Structured logging (console + optional file); credentials never emitted |
| File security | World-readable Excel | Output directory `0o700`, files `0o600` |
| TLS | Default | Explicit `session.verify = True` |
| User-Agent | Absent | Identifies the client for support diagnostics |
| Columns | Limited mapping | Includes recommended `srid`, `gNumber`, price fields, cancellation data |
| Configuration | Hard-coded 30 days | Fully configurable via environment variables |
| Error handling | Minimal | Distinct handling for 401/403/429/5xx |

## Prerequisites

- Python 3.9+
- A Wildberries API token with the **Statistics** category enabled  
  (Seller Portal → Profile → Settings → API Access)

## Installation

```bash
cd wb_orders_project
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and replace the placeholder with your real token:

   ```
   WB_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. Optional variables (defaults shown):

   | Variable     | Default     | Description                                      |
   |--------------|-------------|--------------------------------------------------|
   | `DAYS_BACK`  | 30          | Look-back window (1–90 days)                     |
   | `FLAG`       | 0           | 0 = incremental / paginated; 1 = full calendar day |
   | `OUTPUT_DIR` | ./output    | Directory for Excel reports                      |
   | `LOG_LEVEL`  | INFO        | DEBUG / INFO / WARNING / ERROR / CRITICAL        |
   | `LOG_FILE`   | (empty)     | Optional path for persistent log file            |

**Security note:** Never commit the `.env` file. Add it to `.gitignore`.

## Usage

```bash
python wb_orders_fetcher.py
```

On success the script writes a file similar to:

```
./output/wb_client_orders_20260806_011300.xlsx
```

with owner-only read/write permissions.

## API Behaviour Summary (official documentation)

- Endpoint: `GET https://statistics-api.wildberries.ru/api/v1/supplier/orders`
- Data refreshed approximately every 30 minutes.
- Retention: up to 90 days.
- `flag=0` (default): returns records where `lastChangeDate >= dateFrom` (max ~80 000 rows per response). Subsequent pages advance `dateFrom` to the last record’s `lastChangeDate`.
- `flag=1`: returns all orders whose order date equals the calendar day of `dateFrom`.
- Recommended unique identifier: `srid`.
- Typical rate limit for this method: 1 request per minute.

## Security Checklist Implemented

- [x] Secrets loaded only from environment / `.env`
- [x] Token never appears in logs or error messages
- [x] TLS certificate verification enforced
- [x] Output files and directories created with restrictive Unix permissions
- [x] User-Agent supplied for operational transparency
- [x] Input validation on configuration values
- [x] Graceful, non-leaking error handling for authentication and rate-limit failures

## Extending the Project

- Add sales endpoint (`/api/v1/supplier/sales`) by cloning the fetch routine.
- Store results in a database instead of Excel by replacing `save_secure_excel`.
- Integrate with a secret manager (HashiCorp Vault, AWS Secrets Manager, etc.) by replacing the `load_config` token retrieval.

## Licence

This utility is provided as a reference implementation for educational and internal operational use. Ensure compliance with Wildberries API Terms of Service and local data-protection regulations.
