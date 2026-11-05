import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.main import app

def run_tests():
    client = TestClient(app)
    print("==================================================")
    print("RUNNING TRADEMIND END-TO-END BACKEND TEST SUITE")
    print("==================================================\n")

    # 1. Health check
    print("[1] Testing /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print(f"    Health Status: {health_data['status']}")
    print(f"    Groq: {health_data['groq'].get('connected')} (Model: {health_data['groq'].get('model')})")
    print(f"    Hindsight: {health_data['hindsight'].get('status_message')}")
    print(f"    Historical Datasets: {health_data['market_data'].get('historical_instruments_count')}")

    # 2. Instruments list
    print("\n[2] Testing /api/market/instruments...")
    res = client.get("/api/market/instruments")
    assert res.status_code == 200
    instruments = res.json()
    print(f"    Found {len(instruments)} instruments:")
    for inst in instruments:
        print(f"    - {inst['symbol']} ({inst['name']}) | Last: {inst['last_timestamp']} | Price: ₹{inst['latest_close']}")

    # 3. Market OHLCV and Indicators
    print("\n[3] Testing /api/market/NIFTY_50...")
    res = client.get("/api/market/NIFTY_50")
    assert res.status_code == 200
    market_data = res.json()
    print(f"    Symbol: {market_data['symbol']} | Price: ₹{market_data['current_price']} ({market_data['change_pct']}%)")
    print(f"    Candles: {market_data['candle_count']} | Source: {market_data['data_source']}")
    print(f"    Indicators: RSI={market_data['indicators']['rsi']}, EMA20=₹{market_data['indicators']['ema20']}, Trend={market_data['indicators']['trend_summary']}")

    # 4. Hypothesis Generation (Groq LLM)
    print("\n[4] Testing /api/hypothesis/generate with Groq LLM...")
    res = client.post("/api/hypothesis/generate", json={"instrument_id": "NIFTY_50", "include_memory": True})
    assert res.status_code == 200, f"Hypothesis generation failed: {res.text}"
    hypo = res.json()
    print(f"    Instrument: {hypo['instrument']}")
    print(f"    Direction: {hypo['market_direction']} | Confidence: {hypo['confidence']}")
    print(f"    Hypothesis: {hypo['hypothesis'][:120]}...")
    print(f"    Levels: Entry=₹{hypo['entry_assumption']}, SL=₹{hypo['stop_loss_assumption']}, Target=₹{hypo['target_assumption']}")
    print(f"    Evidence items: {len(hypo['supporting_evidence'])}")
    print(f"    Invalidation conditions: {len(hypo['invalidation_conditions'])}")

    # 5. Paper Trading Execution & State
    print("\n[5] Testing Paper Trading Engine...")
    port_res = client.get("/api/paper-trading/portfolio")
    assert port_res.status_code == 200
    port = port_res.json()
    print(f"    Initial Capital: ₹{port['initial_capital']:,} | Available: ₹{port['available_cash']:,}")

    # Place a virtual buy order
    order_res = client.post("/api/paper-trading/order", json={
        "instrument": "RELIANCE",
        "side": "BUY",
        "quantity": 10,
        "stop_loss": 1280.0,
        "target": 1360.0,
        "notes": "Testing automated paper order placement"
    })
    assert order_res.status_code == 200, f"Order failed: {order_res.text}"
    order = order_res.json()
    print(f"    Executed Order: {order['order_id']} | {order['side']} {order['quantity']} {order['instrument']} @ ₹{order['entry_price']} (Fee: ₹{order['fee_incurred']})")

    # Close order to simulate reflection loop
    close_res = client.post(f"/api/paper-trading/order/{order['order_id']}/close")
    assert close_res.status_code == 200
    closed = close_res.json()
    print(f"    Closed Order: {closed['order_id']} | Realized PnL: ₹{closed['realized_pnl']} | Status: {closed['status']}")

    # 6. Memory vs No-Memory Experiment Lab
    print("\n[6] Testing /api/experiment/comparison...")
    exp_res = client.get("/api/experiment/comparison?instrument=NIFTY_50&scenarios=5")
    assert exp_res.status_code == 200, f"Experiment failed: {exp_res.text}"
    exp = exp_res.json()
    print(f"    Evaluated Scenarios: {exp['total_scenarios_evaluated']}")
    print(f"    Agent A (No Memory): Accuracy={exp['agent_a_metrics']['directional_accuracy_pct']}%, Return={exp['agent_a_metrics']['total_return_pct']}%, Mistakes={exp['agent_a_metrics']['repeated_mistakes_count']}")
    print(f"    Agent B (With Memory): Accuracy={exp['agent_b_metrics']['directional_accuracy_pct']}%, Return={exp['agent_b_metrics']['total_return_pct']}%, Mistakes={exp['agent_b_metrics']['repeated_mistakes_count']}")
    print(f"    Summary: {exp['summary_analysis'][:140]}...")

    # 7. Compelling AI Loop (Market Data -> Tabular ML -> Hindsight Recall -> Groq Reasoning -> Paper Trade -> Hindsight Reply)
    print("\n[7] Testing Compelling AI Loop (/api/loop/run)...")
    loop_res = client.post("/api/loop/run?instrument=NIFTY_50")
    assert loop_res.status_code == 200, f"Loop failed: {loop_res.text}"
    loop_data = loop_res.json()
    print(f"    Loop ID: {loop_data['loop_id']} ({loop_data['execution_time_seconds']}s)")
    print(f"    Step 1 (Market Data): {loop_data['step1_market_data']['current_price']} | Trend: {loop_data['step1_market_data']['indicators']['trend_regime']}")
    print(f"    Step 2 (Tabular ML): Direction={loop_data['step2_ml_analysis']['direction']['direction']} ({loop_data['step2_ml_analysis']['direction']['confidence']*100:.0f}%) | Volatility={loop_data['step2_ml_analysis']['volatility']['volatility_regime']} ({loop_data['step2_ml_analysis']['volatility']['predicted_volatility_pct']}%)")
    print(f"    Step 3 (Hindsight Recall): Recalled {loop_data['step3_hindsight_recall']['recalled_items_count']} memory lessons")
    print(f"    Step 4 (Groq Reason): {loop_data['step4_groq_explanation']['hypothesis'][:110]}...")
    print(f"    Step 5 (Paper Result): {loop_data['step5_paper_trading_result']['verdict']} | Net PnL: Rs. {loop_data['step5_paper_trading_result']['net_realized_pnl']}")
    print(f"    Step 6 (Hindsight Reply): {loop_data['step6_hindsight_lesson_reply']['hindsight_reply'][:120]}...")
    print(f"    Verdict: {loop_data['summary_verdict']}")

    print("\n==================================================")
    print("ALL BACKEND TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
