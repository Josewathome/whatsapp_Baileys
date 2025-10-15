from fastapi.responses import HTMLResponse
from fastapi import APIRouter,Request
import urllib.parse
from app.infrastructure.encryption.encrypt import decrypt_from_url
from typing import List
import logging
from datetime import datetime
import httpx
router = APIRouter()

@router.get("/qrcode", response_class=HTMLResponse)
async def show_qr(request: Request):
    """
    Displays the QR code directly in the browser.
    Example:
    http://localhost:8000/api/v1/qrcode?data=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0i...
    """
    data = request.query_params.get("data")
    if not data:
        return HTMLResponse("<h3>❌ Missing 'data' query parameter</h3>", status_code=400)

    decoded_data = urllib.parse.unquote(data)
    qr_data = decrypt_from_url(decoded_data)
    

    # Detect format
    if qr_data.startswith('data:image/png;base64,'):
        print(f"The QR DATA STRING : {qr_data}")
        print("✅ Found PNG QR code format")
    elif qr_data.startswith('data:image/svg+xml;base64,'):
        print("⚠️ Found SVG QR code format")
    else:
        return HTMLResponse(f"<h3>❌ Invalid QR data format</h3><p>{qr_data[:100]}...</p>", status_code=400)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhatsApp QR Code Scanner</title>
        <style>
            body {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: Arial, sans-serif;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 400px;
            }}
            .qr-code {{
                border: 3px solid #25D366;
                border-radius: 10px;
                padding: 15px;
                background: white;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📱 WhatsApp Registration</h2>
            <div class="qr-code">
                <img src="{qr_data}" alt="QR Code" style="width:300px;height:300px;">
            </div>
            <p>Scan this QR code using WhatsApp → Linked Devices → Link a Device</p>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
