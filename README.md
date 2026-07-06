# Trading Bot — Binance USDT-M Futures (Demo / Testnet)

A Python CLI for placing **MARKET** and **LIMIT** orders on **Binance USDT-Margined Futures** demo/testnet, with structured code, file logging, and clear error handling.

> **Default:** Demo virtual funds at `https://demo-fapi.binance.com`. Mainnet is supported with safeguards but uses **real money**.

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Demo API keys** from [Binance Demo Trading](https://www.binance.com/en/demo-trading) (API Management)

### Install

```powershell
cd trading-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional, for pytest
```

### Configure `.env`

```powershell
copy .env.example .env
```

Demo (recommended):

```env
BINANCE_API_KEY=your_demo_api_key
SECRET_KEY=your_demo_api_secret
TRADING_ENV=testnet
BINANCE_FUTURES_BASE_URL=https://demo-fapi.binance.com
CONFIRM_LIVE_TRADING=false
LOG_LEVEL=INFO
```

| Variable | Description |
|----------|-------------|
| `BINANCE_API_KEY` | Futures API key |
| `SECRET_KEY` | API secret |
| `TRADING_ENV` | `testnet` (demo) or `mainnet` |
| `BINANCE_FUTURES_BASE_URL` | `https://demo-fapi.binance.com` or `https://fapi.binance.com` |
| `CONFIRM_LIVE_TRADING` | Must be `true` for mainnet orders |
| `LOG_LEVEL` | Console level (`INFO` default); file always logs `DEBUG` |

---

## CLI commands

| Command | Purpose |
|---------|---------|
| `check_config` | Show and validate `.env` |
| `ping` | Public API connectivity |
| `server_time` | Binance server time |
| `test_auth` | Signed balance call (auth test) |
| `validate_order` | Validate input + exchange filters (no order) |
| `order` | Place MARKET/LIMIT order (`--dry-run` for test endpoint) |
| `smoke_test` | End-to-end demo checks (ping → dry-run orders) |
| `version` | App version |

Windows: use underscores (`check_config`, `smoke_test`, etc.) if hyphens cause issues.

### Quick smoke test

```powershell
.\.venv\Scripts\python.exe cli.py smoke_test
```

Runs: ping → server time → auth → validate → MARKET dry-run → LIMIT dry-run.

### Validate input (original requirement)

```powershell
.\.venv\Scripts\python.exe cli.py validate_order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
.\.venv\Scripts\python.exe cli.py validate_order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 65000
```

### Dry-run order (no trade)

```powershell
.\.venv\Scripts\python.exe cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run
```

### Real demo order

```powershell
.\.venv\Scripts\python.exe cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Expected order output

```
=== Order Request ===
Symbol:   BTCUSDT
Side:     BUY
Type:     MARKET
Quantity: 0.001

=== Order Response ===
Order ID:     12345678
Status:       FILLED
Executed Qty: 0.001
Avg Price:    67234.50

Order placed and filled successfully.
```

---

## CLI arguments (`order` / `validate_order`)

| Argument | Required | Values |
|----------|----------|--------|
| `--symbol` | Yes | e.g. `BTCUSDT` |
| `--side` | Yes | `BUY`, `SELL` |
| `--type` | Yes | `MARKET`, `LIMIT` |
| `--quantity` | Yes | positive decimal |
| `--price` | LIMIT only | positive decimal |
| `--dry-run` | No | `order` only — uses `/fapi/v1/order/test` |

**Exit codes:** `0` success · `1` validation/config · `2` API/network

---

## Project layout

```
trading-bot/
├── bot/
│   ├── client/           # HTTP client, signing, endpoints
│   ├── config.py
│   ├── error_messages.py # User-friendly Binance error hints
│   ├── exceptions.py
│   ├── logging_config.py
│   ├── models.py
│   ├── orders.py
│   ├── smoke_test.py
│   └── validators.py
├── cli/
│   └── main.py
├── cli.py
├── tests/
├── scripts/
│   ├── run_feature4_tests.bat
│   └── run_smoke_test.bat
├── logs/                 # trading_bot.log (gitignored)
├── .env                  # secrets (gitignored)
└── FEATURES.txt
```

---

## Testing

**Offline (no network):**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -v -m "not integration"
```

**Live demo API:**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\ -v -m integration
scripts\run_smoke_test.bat
```

Manual test cases: `tests\FEATURE3_TEST_CASES.txt`, `tests\FEATURE4_TEST_CASES.txt`

---

## Logging

- **Console:** `LOG_LEVEL` (default `INFO`) — summaries only
- **File:** `logs/trading_bot.log` — always `DEBUG`, including full API payloads and order request/response blocks
- Signatures are redacted in all logs

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `-1022` Invalid signature | Wrong secret | Verify `SECRET_KEY` in `.env` |
| `-2015` Invalid API key | Wrong keys or URL | Use Demo keys with `demo-fapi` |
| `-1021` Timestamp | Clock drift | Sync system time; increase `RECV_WINDOW` |
| `-1111` Precision | Bad qty/price step | Match symbol filters |
| `-2019` Margin | Low balance | Add demo funds |
| `-4164` Min notional | Order too small | Increase qty or price |
| Connection timeout | Network | Check firewall and base URL |

CLI errors include hints for common codes. See `logs/trading_bot.log` for full details.

---

## API references

| Topic | Link |
|-------|------|
| USDT-M Futures | [General Info](https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info) |
| New Order | [POST /fapi/v1/order](https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order) |
| Test Order | [POST /fapi/v1/order/test](https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Test-New-Order) |
| Error codes | [Error Codes](https://developers.binance.com/docs/derivatives/usds-margined-futures/error-code) |
| Demo portal | [Demo Trading](https://www.binance.com/en/demo-trading) |
