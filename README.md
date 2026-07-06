# Trading Bot — Binance Futures Testnet (USDT-M)

A small Python CLI for placing **MARKET** and **LIMIT** orders on **Binance USDT-Margined Futures Testnet**. The project separates the API client layer (`bot/`) from the command-line interface (`cli.py`), with file logging and structured error handling.

> **Scope:** Testnet only. Do not use mainnet API keys with this tool.

---

## Setup

### 1. Prerequisites

- **Python 3.10+**
- A **Binance Futures Testnet** account and API key pair  
  Create keys at: [https://testnet.binancefuture.com/](https://testnet.binancefuture.com/)

### 2. Clone the repository

```bash
git clone https://github.com/vermashobhit1994/trading-bot.git
cd trading-bot
```

### 3. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install httpx python-dotenv typer
```

### 5. Configure environment variables

Copy the example env file and fill in your **testnet** credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_testnet_api_key
SECRET_KEY=your_testnet_secret_key
BINANCE_FUTURES_BASE_URL=https://demo-fapi.binance.com
```

| Variable | Description |
|----------|-------------|
| `BINANCE_API_KEY` | Futures Testnet API key |
| `SECRET_KEY` | Futures Testnet API secret |
| `BINANCE_FUTURES_BASE_URL` | REST base URL (default: `https://demo-fapi.binance.com`) |

`.env` is gitignored and must never be committed.

### 6. Create the logs directory (optional)

Logs are written to `logs/trading_bot.log` at runtime. The directory is created automatically if missing.

---

## How to run — examples

All commands are run from the project root with the virtual environment activated.

### Show CLI help

```bash
python cli.py --help
python cli.py order --help
```

### MARKET order — BUY

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### MARKET order — SELL

```bash
python cli.py order --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### LIMIT order — BUY (price required)

```bash
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 65000
```

### LIMIT order — SELL

```bash
python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
```

### Expected output

On success, the CLI prints:

1. **Order request summary** — symbol, side, type, quantity, price (if LIMIT)
2. **Order response details** — `orderId`, `status`, `executedQty`, `avgPrice` (when returned by the API)
3. **Success or failure message**

Example:

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

Order placed successfully.
```

Detailed request/response data and errors are also written to `logs/trading_bot.log`.

---

## CLI arguments

| Argument | Required | Values | Notes |
|----------|----------|--------|-------|
| `--symbol` | Yes | e.g. `BTCUSDT` | USDT-M perpetual symbol |
| `--side` | Yes | `BUY`, `SELL` | Order side |
| `--type` | Yes | `MARKET`, `LIMIT` | Order type |
| `--quantity` | Yes | positive decimal | Contract quantity |
| `--price` | LIMIT only | positive decimal | Ignored for MARKET orders |

---

## Project layout

```
trading-bot/
├── bot/
│   ├── client.py          # Signed HTTP client for Binance Futures API
│   ├── orders.py          # Order placement logic
│   ├── validators.py      # Input validation
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # CLI entry point
├── logs/                  # Runtime logs (gitignored)
├── .env                   # Local secrets (gitignored)
└── .env.example           # Env template
```

---

## Assumptions

### Environment & API

- You use **Futures Testnet** API keys, not mainnet. Testnet and mainnet keys are separate.
- The default REST base URL is **`https://demo-fapi.binance.com`** per [Binance USDT-M Futures docs](https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info). If your testnet account was created on the legacy portal (`testnet.binancefuture.com`), you may need to adjust `BINANCE_FUTURES_BASE_URL` accordingly.
- Your system clock is reasonably accurate. Signed requests include a millisecond `timestamp`; large clock drift can cause `-1021` errors.

### Trading

- **USDT-M perpetual futures only** (symbols like `BTCUSDT`, not coin-margined pairs).
- Account is in **one-way position mode** (`positionSide` = `BOTH`). Hedge mode (`LONG` / `SHORT`) is not supported unless extended later.
- **LIMIT** orders use **`timeInForce=GTC`** (Good Till Cancel).
- **MARKET** orders do not require a price.
- Quantity and price must satisfy Binance **exchange filters** (min quantity, step size, tick size, min notional). Invalid precision returns API errors such as `-1111` or `-4164`.
- You have **sufficient testnet margin** in your Futures Testnet wallet. Fund via the testnet portal if orders fail with insufficient margin (`-2019`).

### Software

- Python **3.10+** is installed and available as `python` or `python3`.
- Dependencies are installed in an isolated virtual environment.
- Outbound HTTPS access to the Binance Futures Testnet API is allowed from your network.
- API secrets are stored only in `.env` on your machine and are never logged or committed to git.

---

## API references

| Topic | Documentation |
|-------|---------------|
| General info & testnet | [USDT-M Futures — General Info](https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info) |
| Place order | [New Order — POST /fapi/v1/order](https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order) |
| Exchange filters | [Exchange Information](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information) |
| Error codes | [Error Codes](https://developers.binance.com/docs/derivatives/usds-margined-futures/error-code) |
| Testnet portal | [https://testnet.binancefuture.com/](https://testnet.binancefuture.com/) |

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `-1022` Invalid signature | Wrong secret or bad signing | Verify `SECRET_KEY` in `.env` |
| `-2015` Invalid API key | Wrong key or wrong environment | Use Futures Testnet keys |
| `-1021` Timestamp outside recvWindow | Clock drift | Sync system time |
| `-1111` Precision error | Qty/price step size | Adjust quantity or price to symbol filters |
| `-2019` Margin insufficient | Low testnet balance | Add testnet funds via the portal |
| Connection timeout | Network / firewall | Check internet and API URL |

Check `logs/trading_bot.log` for full request and response details.
