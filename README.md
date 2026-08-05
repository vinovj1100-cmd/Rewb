# Secure Wildberries Supplier Orders Fetcher

A production-oriented Python utility that retrieves order data from the official Wildberries Statistics API (`/api/v1/supplier/orders`). It provides both a command-line interface and a Streamlit web interface suitable for Streamlit Community Cloud.

## Key Improvements over the Original Script

| Area | Original Issue | Enhancement |
|------|----------------|-------------|
| Syntax | `if name == "__main__"` (NameError) | Corrected to `if __name__ == "__main__"` |
| Authentication | Basic presence check | Length validation; token never logged |
| Time zone | UTC with trailing Z | Moscow time (Europe/Moscow) as required by the API |
| Pagination | Single request only | Automatic cursor-based pagination using `lastChangeDate` (flag=0) |
| Rate limits | Fixed 0.5 s sleep | Respects 429 + `Retry-After` / `X-Ratelimit-Retry`; 61 s inter-page delay |
| Retries | None | Exponential backoff + jitter via `tenacity` (5 attempts) |
| Logging | `print` statements | Structured logging; credentials never emitted |
| File security | World-readable Excel | Output directory `0o700`, files `0o600` |
| TLS | Default | Explicit `session.verify = True` |
| User-Agent | Absent | Identifies the client for support diagnostics |
| Columns | Limited mapping | Includes recommended `srid`, `gNumber`, price fields, cancellation data |
| Configuration | Hard-coded 30 days | Fully configurable via environment variables / Streamlit Secrets |
| Error handling | Minimal | Distinct handling for 401/403/429/5xx |
| Deployment | CLI only | Streamlit web UI (`app.py`) ready for Community Cloud |

## Important: Streamlit Cloud Dependency Files

| File | Purpose on Streamlit Cloud |
|------|----------------------------|
| **`requirements.txt`** | Python packages installed with **pip** (streamlit, requests, pandas, …) |
| **`packages.txt`** | System packages installed with **apt-get** (leave empty unless you need native libraries) |

The previous error occurred because Python package names were placed in `packages.txt`. That file is reserved for APT packages only.

## Prerequisites

- Python 3.9+
- A Wildberries API token with the **Statistics** category enabled  
  (Seller Portal → Profile → Settings → API Access)

## Local Installation

```bash
cd wb_orders_project
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set WB_API_TOKEN=...
```

### Run as CLI
```bash
python wb_orders_fetcher.py
```

### Run as Streamlit app (local)
```bash
streamlit run app.py
```

## Streamlit Community Cloud Deployment

1. Push the repository to GitHub.
2. In the Streamlit Cloud dashboard set:
   - **Main file path**: `app.py`
3. Add the secret:
   - Settings → Secrets → paste:
     ```toml
     WB_API_TOKEN = "your_actual_token_here"
     ```
4. Ensure the repository contains:
   - `requirements.txt` (Python packages)
   - `packages.txt` (empty or only real APT packages)
   - `app.py` (Streamlit entry point)
   - `wb_orders_fetcher.py` (core logic)

## Configuration

| Variable / Secret | Default | Description |
|-------------------|---------|-------------|
| `WB_API_TOKEN`    | —       | Required. Statistics-category token |
| `DAYS_BACK`       | 30      | Look-back window (1–90) – CLI only |
| `FLAG`            | 0       | 0 = incremental / paginated; 1 = full day – CLI only |
| `OUTPUT_DIR`      | ./output| Excel output directory – CLI only |
| `LOG_LEVEL`       | INFO    | Logging level – CLI only |

In the Streamlit UI the look-back period and flag are controlled by sidebar widgets.

## Security Notes

- Never commit a real `.env` or token to the repository.
- On Streamlit Cloud always use **Secrets** management.
- The core library never logs the token value.
- TLS verification is enforced on every request.

## API Behaviour Summary

- Endpoint: `GET https://statistics-api.wildberries.ru/api/v1/supplier/orders`
- Data refreshed approximately every 30 minutes.
- Retention: up to 90 days.
- `flag=0` (default): records where `lastChangeDate >= dateFrom` (max ~80 000 rows). Subsequent pages advance `dateFrom`.
- `flag=1`: all orders whose order date equals the calendar day of `dateFrom`.
- Recommended unique identifier: `srid`.
- Typical rate limit: 1 request per minute.

## Licence

Reference implementation for educational and internal operational use. Comply with Wildberries API Terms of Service and applicable data-protection regulations.
