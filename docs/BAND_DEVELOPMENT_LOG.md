# Band AI Development Workflow Log – TradeMind

## Overview
This document records the development collaboration conducted via **Band Desktop** for the TradeMind hackathon project.

> **IMPORTANT ARCHITECTURAL DISCLAIMER**
> Band Desktop is strictly a **development collaboration tool** used to coordinate specialized development agents during the engineering lifecycle. It is **not** embedded or integrated into the deployed runtime of TradeMind, nor are any mock Band API endpoints or SDKs created in the application.

---

## 1. Multi-Agent Development Room: `TradeMind Development`
- **Platform:** Band Desktop / Band Daemon v0.4.18
- **Workspace:** `d:\TradeMind`
- **Room Name:** `TradeMind Development`
- **Room ID:** `9fac1071-24cb-4e7a-845e-be9e1d71ebe6`
- **Saved Team ID:** `a872e911-190b-4529-a45d-95f3e2ff1660`

### Registered Development Agents & Roles

| Agent | Band Handle / ID | Core Responsibility |
|-------|------------------|---------------------|
| **Architect Agent** | `naraenks2007/architect-agent`<br>`b9ccab8f-a4ce-46c9-aabf-43380e3d5065` | Application architecture, data flow schemas, task planning, and memory-loop design. |
| **Backend Agent** | `naraenks2007/backend-agent`<br>`d1512a4c-b48c-4d0e-aea3-274653ff325a` | FastAPI endpoints, Groq LLM integration (`llm_service.py`), Hindsight memory client (`hindsight_service.py`), and paper trading engine. |
| **Frontend Agent** | `naraenks2007/frontend-agent`<br>`267a3c91-3948-4f21-8b6e-a79655c55c0e` | React 18 + Vite dashboard, interactive candlestick charts, indicator overlays, Memory Explorer, and Comparison Lab. |
| **Data Agent** | `naraenks2007/data-agent`<br>`628b128a-9435-41a2-afae-c5330522bdc1` | Historical Indian stock market data acquisition (`yfinance`), CSV validation, technical indicator math (Python-calculated), and user CSV upload pipeline. |
| **Reviewer Agent** | `naraenks2007/reviewer-agent`<br>`8041bede-22af-4bea-a39f-cf408a4690e0` | End-to-end testing, schema validation, lookahead bias prevention, security audit, and documentation verification. |

---

## 2. Chronological Agent Decision Log

### Phase 1: Architecture & Data Ingestion (Architect Agent & Data Agent)
- **Decision (Data Agent):** Downloaded 1-year daily OHLCV historical data for 5 Indian instruments:
  - NIFTY 50 (`^NSEI` -> `data/historical/NIFTY_50.csv`)
  - BANK NIFTY (`^NSEBANK` -> `data/historical/BANK_NIFTY.csv`)
  - RELIANCE (`RELIANCE.NS` -> `data/historical/RELIANCE.csv`)
  - TCS (`TCS.NS` -> `data/historical/TCS.csv`)
  - INFY (`INFY.NS` -> `data/historical/INFY.csv`)
- **Decision (Data Agent):** Built `scripts/validate_market_data.py` enforcing strict OHLC price consistency (High >= Low, High >= Open/Close, non-empty, chronological sort, no duplicate timestamps). All 5 datasets verified with 100% pass rate.
- **Decision (Architect Agent):** Added synthetic demonstration dataset `data/synthetic/DEMO_NIFTY_FALLBACK.csv` explicitly labeled as synthetic fallback for offline/disconnected environments. Clearly stated that yfinance is historical demonstration data, not an official NSE real-time feed.

### Phase 2: Groq LLM Integration (Backend Agent & Architect Agent)
- **Decision (Architect Agent):** Enforce strict anti-hallucination discipline: **never allow LLM to invent technical indicator values**. All indicators (RSI 14, EMA 20/50/200, MACD, Bollinger Bands, ATR, Supertrend) must be computed deterministically in Python and injected into the LLM context.
- **Decision (Backend Agent):** Integrated official `groq` Python SDK. Verified available models with user's Groq key. Selected default model `openai/gpt-oss-120b`, with graceful fallback to available models. Structured output validated via Pydantic model `TradingHypothesis`.

### Phase 3: Hindsight Long-Term Memory (Backend Agent & Architect Agent)
- **Decision (Backend Agent):** Integrated official `hindsight-client` Python SDK (v1.2.0).
- **Decision (Architect Agent):** Implemented the 3 core Hindsight operations:
  - `retain`: Stores timestamped market conditions, indicators, hypothesis, and trade outcome.
  - `recall`: Retrieves semantically and temporally relevant past trading experiences.
  - `reflect`: Synthesizes historical lessons and mistake patterns before generating a new hypothesis.
- **Decision (Reviewer Agent):** Enforced honest service degradation: if Hindsight API key is missing or server is unreachable, system reports explicit offline status and fallback metrics; never mock or fabricate memory responses.

### Phase 4: Memory vs No-Memory Experiment Lab (Backend Agent & Reviewer Agent)
- **Decision (Reviewer Agent):** Eliminate look-ahead bias completely. When running historical scenarios through:
  - **Agent A (No Memory):** Receives solely current market snapshot and technical indicator values.
  - **Agent B (With Memory):** Receives current snapshot + previous experiences recalled from Hindsight.
- **Decision (Architect Agent):** Compare both agents on identical timestamps and evaluate: Directional accuracy, Confidence calibration, Win rate, Return, and Repeated mistake frequency. Include disclaimer that experimental past results do not guarantee future performance.

### Phase 5: Paper Trading & Frontend Dashboard (Frontend Agent & Backend Agent)
- **Decision (Backend Agent):** Built virtual paper trading engine starting with ₹1,00,000 simulated capital. Supported BUY/SELL orders, stop-loss, take-profit, transaction costs (0.03% brokerage + STT simulation), and slippage modeling (0.02%).
- **Decision (Frontend Agent):** Created React dashboard featuring TradingView/Lightweight candlestick charting, indicator selector, hypothesis reasoning breakdown, real-time Memory Explorer, and CSV file upload modal.
