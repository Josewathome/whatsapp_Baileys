# WhatsApp Profile Lookup Service - Python Refactored

Complete Python refactoring of the WhatsApp profile lookup system following DDD principles.

## 🏗️ Architecture

### Domain-Driven Design Structure

```
whatsapp-service/
├── api/                    # API Layer
│   ├── routes.py          # FastAPI endpoints
│   └── schemas.py         # Request/response models
├── controllers/            # Controllers Layer
│   └── whatsapp_controller.py
├── domain/                 # Domain Layer
│   ├── models.py          # Domain models
│   ├── exceptions.py      # Domain exceptions
│   └── services/          # Business logic services
│       ├── search_service.py
│       ├── exists_service.py
│       ├── status_service.py
│       ├── business_service.py
│       └── avatar_service.py
├── infrastructure/         # Infrastructure Layer
│   ├── baileys/
│   │   └── whatsapp_client.py
│   ├── session/
│   │   └── memory_store.py
│   ├── keydb/
│   │   ├── queue.py
│   │   └── adapters.py
│   └── logging/
│       └── logger.py
├── core/                   # Core Configuration
│   ├── config.py
│   └── types.py
└── main.py                # Application entry point
```

## ✅ Key Features

- **In-Memory Architecture**: No MongoDB, KeyDB, or external databases
- **No Proxy Logic**: Direct WhatsApp Web connections
- **DDD Compliant**: Clean separation of concerns
- **SMK-RK Standard Response**: Proper headers/body/extra format
- **Validator Integration**: Automatic data type detection
- **Baileys Bridge**: Node.js service for WhatsApp connectivity
NB: Pod == session_id
## 🚀 Installation

### Python Service

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn main:app --reload --port 8000
```

### Baileys Bridge (Node.js)

```bash
# In baileys-bridge directory
npm install express
npm install
node baileys_bridge.js
```
```bash
chmod +x setup_bridge.sh
./setup_bridge.sh

```
### Using Docker Compose

---

### Docker Development

```bash
# Start services with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Check running services
docker-compose ps
```

---

### Production Deployment

```bash
# Deploy in production mode
docker-compose -f docker-compose.prod.yml up -d
```

```
## 📡 API Endpoints
### API USAGE:

1. Register session via /session/start-registration
2. Complete registration via /session/complete-registration  
3. Use lookup APIs
4. Monitor via /session/status
### Health Check

```bash
GET /api/v1/health
```
# Start WhatsApp session registration
POST /api/v1/session/start-registration

# Response:
```bash
[
    {
        "headers": {
            "sender": "tw.tools.whatsapp"
        },
        "body": {
            "message": {
                "session_id": "pending_whatsapp-pod-1_b5d60395",
                "qr_code": "data:image/png;base64,iVBORw0Ox7ahaGlFTkSuQmCC",
                "status": "qr_ready",
                "url_path": "http://localhost:8000/api/v1/qrcode?data=gAAAo41j6H9-hr9Cc_IT441Z-C7EGUFs2NrTAdJg%3D%3D",
                "message": "Click Open URL and Get WhatsApp QR code to authenticate",
                "instructions": "Open WhatsApp → Linked Devices → Link a Device",
                "source": "baileys_bridge"
            }
        },
        "extra": {}
    }
]
```

# NEW: Complete registration with phone number
POST /api/v1/session/complete-registration
```bash payload
{
  "session_id": "pending_pod_abc123def",
  "phone_number": "79319999999"
}
```
```bash Response
[
    {
        "headers": {
            "sender": "tw.tools.whatsapp"
        },
        "body": {
            "success": false, # true OR False
            "message": "Registration failed"
        },
        "extra": {}
    }
]

```

# NEW: Check connection status
GET /api/v1/session/status

# Response:
```bash
[
    {
        "headers": {
            "sender": "tw.tools.whatsapp"
        },
        "body": {
            "state": "disconnected",
            "pod": "whatsapp-pod-1",
            "session_phone": null,
            "uptime": 27.969610929489136,
            "healthy": false
        },
        "extra": {}
    }
]
```
# NEW: Restart connection
```bash
POST /api/v1/session/restart
```

### Single Lookup

```bash
POST /api/v1/lookup
Content-Type: application/json

{
  "phone": "79319999999",
  "session_id": "pending_whatsapp-pod-1_6e283f6d",
}
```

**Response:**
```json
{
  "headers": {
    "sender": "tw.tools.whatsapp"
  },
  "body": {
    "result_code": "FOUND",
    "phone": "254722699426",
    "is_exists": "Да",
    "status_hidden": "Нет",
    "is_business": "Нет",
    "has_avatar": "Да",
    "avatar_hidden": "Нет"
  },
  "extra": {
    "image_url": "https://...",
    "preview_url": "https://..."
  }
}
```

### controller Lookup / Batch Lookup

```bash
POST /api/v1/controller
Content-Type: application/json

{
  "query": ["79319999999", "testuser@gmail.com", "79858601908"],
  "session_id": "pending_whatsapp-pod-1_6e283f6d"
}
```

**Response:**
```json
{
  "results": [
    {
      "headers": {"sender": "tw.tools.whatsapp"},
      "body": {...},
      "extra": {...}
    },
    {
      "headers": {"sender": "tw.tools.whatsapp"},
      "body": {"message": "Type email not supported"},
      "extra": {...}
    }
  ]
}
```


### **Step 5: Monitor System**
```bash
# Check health - ENHANCED with more details
curl http://localhost:8000/api/v1/health

# Check session status - NEW
curl http://localhost:8000/api/v1/session/status

# Restart if needed - NEW
curl -X POST http://localhost:8000/api/v1/session/restart
```



## 🔧 Configuration

Create `.env` file:

```env
SERVICE_NAME=tw.tools.whatsapp
MODE=dev
HOST=0.0.0.0
PORT=8000
PORT_BAILY=3000
POD_NAME=whatsapp-pod-1

COUNT_USE_FOR_RELOAD=1000
SESSION_TIMEOUT=600
MAX_FAILURES_IN_ROW=30

VALIDATOR_URL=http://validator-service/api/v1/validate # If you dont have one set up leave it as it is
```

## 🌉 Baileys Bridge

The Baileys Bridge is a lightweight Node.js HTTP service that wraps the Baileys library.

### Why?

Baileys is a Node.js library and cannot be used directly in Python. The bridge:
- Runs Baileys in Node.js
- Exposes HTTP endpoints
- Python service calls these endpoints

### Endpoints

- `POST /onWhatsApp` - Check if number exists
- `POST /fetchStatus` - Get status message
- `POST /getBusinessProfile` - Get business info
- `POST /profilePictureUrl` - Get avatar URL
- `GET /health` - Health check


All responses follow SMK-RK standard:

```python
{
    "headers": {
        "sender": "tw.tools.whatsapp"  # Service identifier
    },
    "body": {
        # Main business logic data
        "result_code": "FOUND",
        "phone": "79319999999",
        ...
    },
    "extra": {
        # Additional metadata
        ...
    }
}
```

## 🧪 Testing

```bash
# Test single lookup
curl -X POST http://localhost:8000/api/v1/lookup \
  -H "Content-Type: application/json" \
  -d '{"phone": "79319999999"}'

# Test controller with validator
curl -X POST http://localhost:8000/api/v1/controller \
  -H "Content-Type: application/json" \
  -d '{"query": ["79319999999", "test@email.com"]}'

# Health check
curl http://localhost:8000/api/v1/health
```

## 📝 Development

### Running in Development Mode

```bash
# Python service with auto-reload
MODE=dev python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Services

1. Create service in `domain/services/`
2. Inject dependencies in `main.py`
3. Add routes in `api/routes.py`

## 🐳 Docker Deployment

```dockerfile
# Build
docker build -t whatsapp-service .

# Run
docker run -p 8000:8000 \
  -e MODE=prod \
  -e BAILEYS_BRIDGE_URL=http://baileys:3000 \
  whatsapp-service
```

## 📚 Project Structure Explained

- **api/**: HTTP layer - FastAPI routes and schemas
- **controllers/**: Orchestration - coordinates services
- **domain/**: Business logic - pure domain services
- **infrastructure/**: External adapters - storage, queues, clients
- **core/**: Configuration and shared types

## 🔐 Security Notes

- No authentication implemented (add as needed)
- Validator service should be on internal network
- Baileys bridge should not be publicly exposed
- Use environment variables for sensitive data

## 📄 License

Proprietary - SMK-RK LLC

## 🤝 Support

For issues or questions, contact SMK-RK technical team.