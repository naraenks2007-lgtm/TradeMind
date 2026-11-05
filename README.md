# TradeMind AI – Intelligent Market Hypothesis & Long-Term Memory Engine

TradeMind is a quantitative trading intelligence platform built for Indian equities (NIFTY 50, BANK NIFTY, RELIANCE, TCS, INFY). It pairs deterministic Python-calculated technical indicators with **Groq LLM** for hypothesis generation and **Vectorize Hindsight** for experiential long-term memory.

## Architectural Principles & Decisions

1. **No LLM Training on Raw Stock Numbers**:
   - Smaller, specialized **tabular Machine Learning models** (Scikit-Learn `RandomForestClassifier` for Direction, `GradientBoostingRegressor` for Volatility, and volume-flow models for Sentiment) handle numerical predictive modeling.
   - **Groq LLM** is strictly utilized for **reasoning, thesis formulation, and explanation**, synthesizing ML probabilities with historical market memories.

2. **No Framework Over-Engineering**:
   - Deterministic calculations, technical indicators, order execution, P&L math, and data loading remain in clean **FastAPI & Python standard libraries**.
   - Multi-step orchestration is focused where it delivers value: the autonomous closed-loop workflow.

3. **The Compelling AI Loop**:
   Demonstrates a complete 6-stage closed loop:
   ```
   Market Data comes in
     → Tabular ML analyzes it (Direction, Volatility, Sentiment)
     → Hindsight recalls what happened before (Historical memory bank)
     → Groq explains the decision (Reasoning & quantitative hypothesis)
     → Paper Trading measures the result (₹1,00,000 simulated capital, slippage & fee model)
     → Hindsight remembers the lesson & replies (Experiential retention & conversational reply)
   ```

---

TradeMind was coordinated using **Band Desktop** across five specialized development agents:

- **Architect Agent (`naraenks2007/architect-agent`)**: Designed system architecture, data schemas, and memory loops.
- **Backend Agent (`naraenks2007/backend-agent`)**: Implemented FastAPI backend, Groq integration (`llm_service.py`), and Hindsight SDK client (`hindsight_service.py`).
- **Frontend Agent (`naraenks2007/frontend-agent`)**: Built React 18 dashboard, candlestick charting, indicator overlays, and comparison lab.
- **Data Agent (`naraenks2007/data-agent`)**: Built automated historical market data ingestion (`yfinance`), CSV validation, and indicator math.
- **Reviewer Agent (`naraenks2007/reviewer-agent`)**: Conducted end-to-end verification, eliminated look-ahead bias, and audited security.

> **Note on Band AI:** Band Desktop is used strictly as a development orchestration tool. It is not bundled or embedded into the production TradeMind application. Detailed logs can be found in [`docs/BAND_DEVELOPMENT_LOG.md`](docs/BAND_DEVELOPMENT_LOG.md).

---

## 2. Market Data Architecture

TradeMind does not use empty datasets or arbitrary hardcoded chart values. Real 1-year historical daily OHLCV datasets are provided in `data/historical/`:

| Instrument | Symbol / Ticker | Records | Date Range | Data Source |
|------------|-----------------|---------|------------|-------------|
| **NIFTY 50** | `^NSEI` | 246 rows | 2025-11-04 to 2026-11-03 | Historical (yfinance demonstration feed) |
| **BANK NIFTY** | `^NSEBANK` | 246 rows | 2025-11-04 to 2026-11-03 | Historical (yfinance demonstration feed) |
| **RELIANCE** | `RELIANCE.NS` | 247 rows | 2025-11-04 to 2026-11-03 | Historical (yfinance demonstration feed) |
| **TCS** | `TCS.NS` | 247 rows | 2025-11-04 to 2026-11-03 | Historical (yfinance demonstration feed) |
| **INFY** | `INFY.NS` | 247 rows | 2025-11-04 to 2026-11-03 | Historical (yfinance demonstration feed) |
| **DEMO NIFTY** | `DEMO_NIFTY_FALLBACK` | 120 rows | 2026-05-22 to 2026-11-05 | Synthetic Demonstration Fallback (Offline) |

### Scripts:
- **Data Downloader:** `python scripts/download_market_data.py`
- **Data Validator:** `python scripts/validate_market_data.py`
- **Custom Uploads:** Users can upload arbitrary OHLCV CSV files through the web dashboard or `POST /api/market/upload`.

---

## 3. Deterministic Indicators & Groq LLM Integration

TradeMind enforces a strict anti-hallucination rule: **the LLM is never allowed to invent technical indicator numbers**.
All indicators are computed in Python via `ta` and pandas:
- **RSI (14)**
- **EMAs (20, 50, 200)**
- **MACD (12, 26, 9)** line, signal, and histogram
- **Bollinger Bands (20, 2 std dev)**
- **ATR (14)** and Volatility state

### Groq LLM Configuration (`backend/services/llm_service.py`)
- Official SDK: `from groq import Groq`
- Model: `openai/gpt-oss-120b` (configurable in `.env`)
- Structured JSON output validated using **Pydantic**:
  - `instrument`
  - `market_direction` (`BULLISH` | `BEARISH` | `NEUTRAL`)
  - `hypothesis`
  - `supporting_evidence`
  - `confidence` (0.0 to 1.0)
  - `entry_assumption`
  - `stop_loss_assumption`
  - `target_assumption`
  - `invalidation_conditions`
  - `risk_explanation`

---

## 4. Vectorize Hindsight – Experiential Long-Term Memory

Official SDK integration (`hindsight-client` v1.2.0) implementing the 3 core memory verbs:
1. **`retain`**: Ingests market conditions, technical snapshots, hypotheses, and paper-trade outcomes into the long-term memory bank.
2. **`recall`**: Executes sub-second parallel hybrid search (semantic + BM25 + entity graph) to retrieve relevant past experiences when evaluating new setups.
3. **`reflect`**: Performs analytical reasoning across accumulated trade outcomes to synthesize lessons before executing new positions.

> **Honest Degradation:** If `HINDSIGHT_API_KEY` is not configured, TradeMind honestly displays `Offline: HINDSIGHT_API_KEY not configured in .env` and operates in deterministic mode. It never mocks or simulates fake Hindsight memory responses.

---

## 5. Memory vs. No-Memory Experiment Lab

The Comparison Lab runs identical historical market scenarios through two agents without look-ahead bias:
- **Agent A (No Memory):** Standard rule-based technical setup evaluation.
- **Agent B (With Hindsight Memory):** Evaluates identical technicals but incorporates recalled historical lessons (e.g., avoiding overbought RSI traps or low-volatility squeezes).

### Benchmark Comparison Metrics:
- **Directional Accuracy (%)**
- **Win Rate (%)**
- **Simulated Cumulative Return (%)**
- **Repeated Known Mistakes Count**

---

## 6. Paper Trading Engine

Simulated trading environment with **₹1,00,000 initial capital**:
- Virtual Buy and Sell orders with quantity, entry, stop-loss, and target.
- Live mark-to-market unrealized and realized P&L calculation.
- Realistic execution costs: **0.03% brokerage & taxes** and **0.02% slippage model**.
- Automatically reflects trade outcomes into Hindsight memory upon position close.
- Account reset button to restore balance to ₹1,00,000.

---

## Persistent AI Chat Workspace

### Chat memory and file analysis

The chat accepts explicit save commands such as `save today petrol price is 100`, `store ...`, or `remember ...`. User-stated facts are retained in Hindsight with the saved timestamp in the Asia/Kolkata timezone and indexed in the session-scoped SQLite database so questions such as `what is the petrol price I said?` can return the original value and save time. The local index provides recall continuity if Hindsight is temporarily unavailable; the chat reports that fallback honestly.

The chat attachment control supports text-based PDFs, CSV files, and PNG/JPG/JPEG/WEBP images up to 10 MB. PDF text is extracted with pypdf, CSVs are profiled with pandas, and images are analysed using Groq's vision model. Scanned/image-only PDFs currently need OCR and are reported as unsupported when no selectable text is present.

The chat has a persisted dark/light theme toggle. Simple greetings and general questions no longer require market snapshot construction; market-specific prompts still use the market-data and technical-analysis pipeline.


The AI chat includes session-scoped conversation history, automatic titles, new conversations, resume/delete controls, and a 3D animated assistant orb. Conversations and assistant replies are stored in SQLite at `data/conversations.sqlite3` by default; the Groq response, market context, and recalled Hindsight memories are stored with each assistant message.

For deployments with persistent volumes, set `TRADEMIND_CHAT_DB_PATH` to a file path on the mounted volume (for example, `/var/data/conversations.sqlite3` on a service with a disk mounted at `/var/data`). Without a persistent volume, platforms with ephemeral filesystems may discard SQLite data during redeploys or instance replacement.

The current app has no user login, so the API scopes conversations using a browser-generated `X-TradeMind-Session` identifier stored in local storage. This separates browser sessions but is not account authentication; add authenticated user IDs before exposing multi-user private chat as a production SaaS feature.

## 8. Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Environment Configuration
Copy the template and configure your keys:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
PORT=8000
HOST=0.0.0.0
```

### 2. Backend Installation & Verification
```bash
# Install Python dependencies
pip install -r requirements.txt

# Download / Refresh market data
python scripts/download_market_data.py

# Validate all market data files
python scripts/validate_market_data.py

# Run end-to-end backend test suite
python scripts/test_backend.py
```

### 3. Frontend Build & Launch
```bash
# Build frontend
cd frontend
npm install
npm run build
cd ..

# Start application server (serves API and built frontend on port 8000)
python backend/main.py
```
Open **`http://localhost:8000`** in your browser.

*(For frontend development with Vite hot reload: run `npm run dev` in `frontend/` on port 3000).*


## Adaptive Hindsight Learning

TradeMind's chat pipeline can learn from explicit user feedback and bring fresh public market headlines into later analysis.

- **User-taught memory:** messages that clearly express a durable trading preference, correction, or trade lesson are classified by Groq and retained in Hindsight with instrument and browser-session tags. Casual chat is not intentionally retained as a lesson.
- **Learning in future analysis:** market chat and hypothesis generation can retrieve relevant instrument-tagged Hindsight experiences. The chat response exposes recalled memories so users can see what influenced the answer.
- **Market context ingestion:** market questions trigger a fetch of public Google News RSS headlines for the selected instrument. Headline, publisher, publication date and source URL are retained in Hindsight and passed to the market-analysis prompt as unverified external context. Results are cached in-process for 15 minutes.
- **Evidence discipline:** headlines are treated as reported claims, not verified price data. TradeMind should distinguish headlines from broker/market-data values and explain conflicts. RSS availability and publisher coverage can vary.
- **User control and safety:** only explicit preference/correction/outcome-like replies are candidates for durable learning. This feature does not train model weights; it improves future responses through retrieval-augmented context. Market analysis is informational, not a guarantee or an instruction to place a live order.

## Application-wide theme

Use the **Day / Night** control in the main header to switch the entire dashboard, including terminal, workflow, portfolio, memory views, modals and chat. The selection is stored in browser local storage as `trademind.app.theme`.
