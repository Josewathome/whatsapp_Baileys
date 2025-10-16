from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import APIRouter, Request
import urllib.parse
from app.infrastructure.encryption.encrypt import decrypt_from_url
import logging
from datetime import datetime
from app.core.config import settings

router = APIRouter()

# Global variable to track authentication status
authentication_status = {
    "authenticated": False,
    "last_checked": None
}

@router.get("/qrcode", response_class=HTMLResponse)
async def show_qr(request: Request):
    """
    Displays the QR code directly in the browser.
    """
    data = request.query_params.get("data")
    if not data:
        return HTMLResponse("<h3>❌ Missing 'data' query parameter</h3>", status_code=400)

    decoded_data = urllib.parse.unquote(data)
    qr_data = decrypt_from_url(decoded_data)
    base_url = settings.BASE_URL
    version = settings.VERSION_VALUE
    
    # Detect format
    if qr_data.startswith('data:image/png;base64,'):
        print(f"The QR DATA STRING : {qr_data}")
        print("✅ Found PNG QR code format")
    elif qr_data.startswith('data:image/svg+xml;base64,'):
        print("⚠️ Found SVG QR code format")
    else:
        return HTMLResponse(f"<h3>❌ Invalid QR data format</h3><p>{qr_data[:100]}...</p>", status_code=400)

    # Build the status URL
    status_url = f"{base_url}/api/{version}/qrcode/status"
    
    # Use .format() instead of f-strings to avoid any escaping issues
    html_content = '''<!DOCTYPE html>
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
        .status {{
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .waiting {{
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        .success {{
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .popup {{
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 1000;
            text-align: center;
            border: 4px solid #25D366;
        }}
        .popup-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }}
        .popup-success {{
            color: #25D366;
            font-size: 24px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 WhatsApp Registration</h2>
        <div class="qr-code">
            <img src="{qr_image_data}" alt="QR Code" style="width:300px;height:300px;">
        </div>
        <p>Scan this QR code using WhatsApp → Linked Devices → Link a Device</p>
        
        <div id="status" class="status waiting">
            ⏳ Waiting for authentication...
        </div>
    </div>

    <div id="popupOverlay" class="popup-overlay"></div>
    <div id="successPopup" class="popup">
        <div class="popup-success">✅</div>
        <h3>Authentication Complete!</h3>
        <p>QR code has been successfully authenticated.</p>
        <button onclick="closePopup()" style="background: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-top: 15px;">OK</button>
    </div>

    <script>
        (function() {{
            var isAuthenticated = false;
            var STATUS_URL = '{status_endpoint}';
            
            console.log('Page loaded successfully');
            console.log('Status URL: ' + STATUS_URL);

            window.showSuccessPopup = function() {{
                document.getElementById('popupOverlay').style.display = 'block';
                document.getElementById('successPopup').style.display = 'block';
            }};
            
            window.closePopup = function() {{
                document.getElementById('popupOverlay').style.display = 'none';
                document.getElementById('successPopup').style.display = 'none';
            }};

            function checkAuthentication() {{
                if (isAuthenticated) {{
                    console.log('Already authenticated');
                    return;
                }}

                console.log('Checking status at: ' + new Date().toISOString());

                fetch(STATUS_URL)
                    .then(function(response) {{
                        console.log('Got response, status: ' + response.status);
                        return response.json();
                    }})
                    .then(function(data) {{
                        console.log('Data received:', data);
                        
                        if (data.authenticated) {{
                            isAuthenticated = true;
                            document.getElementById('status').innerHTML = '✅ Authentication Complete!';
                            document.getElementById('status').className = 'status success';
                            window.showSuccessPopup();
                            console.log('Authentication successful!');
                        }} else {{
                            console.log('Not authenticated, retrying in 1 second');
                            setTimeout(checkAuthentication, 1000);
                        }}
                    }})
                    .catch(function(error) {{
                        console.error('Fetch error:', error);
                        setTimeout(checkAuthentication, 1000);
                    }});
            }}
            
            console.log('Starting polling...');
            checkAuthentication();
        }})();
    </script>
</body>
</html>'''.format(qr_image_data=qr_data, status_endpoint=status_url)

    return HTMLResponse(content=html_content)

@router.get("/qrcode/status")
async def get_qr_code_status():
    """
    Endpoint to check QR code authentication status
    """
    return JSONResponse(content=authentication_status)

@router.post("/stop/qrcode")
async def stop_qr_code():
    """
    This endpoint would be called by your external system when authentication is complete
    """
    authentication_status["authenticated"] = True
    authentication_status["last_checked"] = datetime.now().isoformat()
    
    print("✅ QR Code authentication completed - status updated")
    logging.info("QR Code authentication status updated to True")
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Authentication status updated", 
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    )

@router.post("/qrcode/reset")
async def reset_qr_code():
    """
    Endpoint to reset authentication status
    """
    authentication_status["authenticated"] = False
    authentication_status["last_checked"] = datetime.now().isoformat()
    
    return JSONResponse(
        status_code=200,
        content={"message": "QR code status reset", "status": "reset"}
    )