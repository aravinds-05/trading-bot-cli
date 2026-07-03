# Run Instructions

This guide provides step-by-step instructions for setting up and running the Binance Futures Testnet Trading Bot.

## 1. Prerequisites
- **Python 3.9+** installed on your system.
- A Binance Futures Testnet Account. You can create one [here](https://testnet.binancefuture.com/).

## 2. Setup & Installation

1. **Clone the repository** and navigate into the directory:
   ```bash
   git clone <repository_url>
   cd trading_bot
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 3. Environment Variables

The bot requires API credentials to authenticate with the Binance Testnet.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your keys:
   ```ini
   BINANCE_API_KEY="your_testnet_api_key_here"
   BINANCE_API_SECRET="your_testnet_api_secret_here"
   ```

*(Note: Do **NOT** use your mainnet Binance keys. These must be keys generated specifically on the testnet).*

## 4. Running the Bot

The bot is operated entirely via a rich Command Line Interface (CLI).

### Interactive Mode (Recommended)
The interactive mode acts as a wizard, prompting you for input with strict validation and colored feedback.

```bash
python3 main.py interactive
```

### Scripting / Automated Mode
You can bypass the interactive prompts by passing your order parameters as flags. This is ideal for cron jobs or automated scripts.

> [!TIP]
> **Supported Symbols (Assets)**
> While `BTCUSDT` is used as the default, the Binance Futures Testnet supports many other crypto assets. Try swapping `BTCUSDT` for:
> - `ETHUSDT` (Ethereum)
> - `SOLUSDT` (Solana)
> - `BNBUSDT` (Binance Coin)
> - `XRPUSDT` (Ripple)

**Market Order (Buy):**
```bash
python3 main.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

**Limit Order (Sell):**
```bash
python3 main.py place-order --symbol ETHUSDT --side SELL --type LIMIT --quantity 1.0 --price 35000
```

**Skip Confirmation Prompt:**
Append the `--yes` or `-y` flag to skip the `[y/N]` terminal confirmation entirely:
```bash
python3 main.py place-order --symbol ETHUSDT --side BUY --type MARKET --quantity 0.1 --yes
```

## 5. Running Tests

The project includes an automated test suite verifying validation logic, API signing, and mock order execution.

```bash
pytest tests/ -v
```

## 6. Checking Logs

All actions are logged securely and formatted as structured JSON for easy ingestion by observability tools (like Datadog or ELK).

```bash
# View the last 20 log entries
tail -n 20 logs/trading_bot.log
```

Every order logs its **request**, the raw **API response**, and (for MARKET orders)
the **confirmed fill**, plus any **errors** — satisfying the "requests, responses,
and errors" logging requirement.

> **Note on MARKET fills:** Binance returns an immediate ACK (`status: NEW`,
> `executedQty: 0`) because fills settle asynchronously. The bot polls the order
> once placed and surfaces the real `executedQty` / `avgPrice`, so MARKET orders
> display as `FILLED` with the actual fill price.

## 7. Sample Logs (Deliverable)

Reference logs from real testnet runs are included in [`sample_logs/`](sample_logs/):

- `sample_logs/market_order.log` — one MARKET order (request → response → confirmed fill)
- `sample_logs/limit_order.log` — one LIMIT order (request → response)
