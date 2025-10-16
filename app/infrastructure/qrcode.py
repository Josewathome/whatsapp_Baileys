import base64
import webbrowser
import tempfile
import os
from app.infrastructure.encryption.encrypt import encrypt_for_url, decrypt_from_url


def display_qr_from_api(token):


    # Decrypt the token
    data = decrypt_from_url(token)

    # Accept both PNG and SVG QR data formats
    if data.startswith('data:image/png;base64,'):
        qr_data_url = data
        print("✅ Found PNG QR code format")
    elif data.startswith('data:image/svg+xml;base64,'):
        qr_data_url = data
        print("⚠️ Found SVG QR code format")
    else:
        print(f"❌ Invalid QR data format. Got: {data[:50]}...")
        return

    # Build the HTML content
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
            h2 {{
                color: #25D366;
                margin-bottom: 20px;
            }}
            .qr-code {{
                border: 3px solid #25D366;
                border-radius: 10px;
                padding: 15px;
                background: white;
                margin: 20px 0;
            }}
            .instructions {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                text-align: left;
            }}
            .status {{
                background: #e8f5e8;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📱 WhatsApp Registration</h2>

            <div class="status">
                <strong>Status:</strong> <span>Ready to Scan</span>
            </div>

            <div class="qr-code">
                <img src="{qr_data_url}" alt="WhatsApp QR Code" style="width: 300px; height: 300px;">
            </div>

            <div class="instructions">
                <h3>📋 How to Scan:</h3>
                <ol>
                    <li>Open <strong>WhatsApp</strong> on your phone</li>
                    <li>Tap <strong>Settings</strong> (⚙️) → <strong>Linked Devices</strong></li>
                    <li>Tap <strong>Link a Device</strong></li>
                    <li>Point your camera at the QR code above</li>
                    <li>Wait for confirmation</li>
                </ol>

                <div style="margin-top: 15px; padding: 10px; background: #d4edda; border-radius: 5px;">
                    <strong>✅ Real QR Code:</strong> This is a scannable QR code!
                </div>
            </div>

            <div style="margin-top: 15px; color: #666; font-size: 12px;">
                Session will expire in 5 minutes
            </div>
        </div>
    </body>
    </html>
    """

    # Save to temporary file (delete=False so we can open it later)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file = f.name

    print("🎯 Opening QR code in browser...")
    print("📱 Scan this QR code with WhatsApp to authenticate")
    webbrowser.open(f'file://{temp_file}')

    # Wait for user confirmation and then clean up
    try:
        input("Press Enter to close and delete the temporary file...")
    except KeyboardInterrupt:
        print("\nClosing QR display...")
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
            print("✅ Temporary file cleaned up")
        else:
            print("⚠️ Temporary file was already removed.")
