from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from backend.services.upstox_service import upstox_service, UPSTOX_INSTRUMENTS

router = APIRouter(prefix="/api/upstox", tags=["Upstox Market Data"])

class TokenPayload(BaseModel):
    access_token: str

@router.get("/status")
def get_status():
    """Returns the Upstox OAuth configuration and authentication status."""
    return upstox_service.get_connection_status()

@router.get("/auth-url")
def get_auth_url():
    """Generates the official Upstox OAuth authorization dialog URL."""
    return {"auth_url": upstox_service.get_auth_url()}

@router.get("/callback")
def oauth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    Handles Upstox OAuth 2.0 callback, exchanges auth code for token,
    and returns a success response for browser popups/redirects.
    """
    if error:
        html = f"""
        <html>
            <body style="background:#0b0e14;color:#ef4444;font-family:sans-serif;padding:40px;text-align:center;">
                <h2>Upstox Authorization Failed</h2>
                <p>Error: {error}</p>
                <button onclick="window.close()" style="background:#1e293b;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;">Close Window</button>
            </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=400)

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    try:
        token_data = upstox_service.exchange_code_for_token(code)
        user_name = token_data.get("user_name", "Authorized User")
        html = f"""
        <html>
            <head><title>Upstox Connected</title></head>
            <body style="background:#0b0e14;color:#10b981;font-family:sans-serif;padding:40px;text-align:center;">
                <h2 style="color:#10b981;">✓ Upstox Connected Successfully!</h2>
                <p style="color:#94a3b8;">Logged in as <b>{user_name}</b></p>
                <p style="color:#64748b;font-size:14px;">You can now close this window and return to TradeMind.</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{ type: "UPSTOX_AUTH_SUCCESS", user: "{user_name}" }}, "*");
                        setTimeout(function() {{ window.close(); }}, 1500);
                    }} else {{
                        setTimeout(function() {{ window.location.href = "/"; }}, 2000);
                    }}
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)
    except Exception as e:
        html = f"""
        <html>
            <body style="background:#0b0e14;color:#ef4444;font-family:sans-serif;padding:40px;text-align:center;">
                <h2>Token Exchange Failed</h2>
                <p>{str(e)}</p>
                <button onclick="window.close()" style="background:#1e293b;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;">Close Window</button>
            </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=500)

@router.post("/token")
def set_manual_token(payload: TokenPayload):
    """Allows manual access token configuration if provided directly."""
    upstox_service.save_token({"access_token": payload.access_token.strip(), "user_name": "Direct Token"})
    return upstox_service.get_connection_status()

@router.post("/disconnect")
def disconnect_upstox():
    """Disconnects Upstox session and clears stored tokens."""
    upstox_service.clear_token()
    return {"status": "DISCONNECTED", "message": "Upstox token cleared."}

@router.get("/instruments")
def get_supported_instruments():
    """Returns verified Upstox instrument keys supported by TradeMind."""
    return upstox_service.get_supported_instruments()

@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """Fetches live market quote for a supported symbol."""
    inst_info = UPSTOX_INSTRUMENTS.get(symbol.upper())
    if not inst_info:
        raise HTTPException(status_code=404, detail=f"Instrument {symbol} not supported.")
    
    quote = upstox_service.get_market_quote(inst_info["instrument_key"])
    if not quote:
        raise HTTPException(status_code=503, detail="Upstox quote unavailable. Ensure valid access token.")
    return quote

@router.get("/ws-url")
def get_ws_url():
    """Returns authorized WebSocket URL for live market-data feed."""
    url = upstox_service.get_ws_auth_url()
    if not url:
        raise HTTPException(status_code=503, detail="Could not authorize WebSocket. Check Upstox token.")
    return {"authorized_ws_url": url}
