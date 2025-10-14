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

## 🚀 Installation

### Python Service

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
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

```bash
docker-compose up --build
```

## 📡 API Endpoints

### Single Lookup

```bash
POST /api/v1/lookup
Content-Type: application/json

{
  "phone": "79319999999"
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
    "phone": "79319999999",
    "status": "Hey there!",
    "is_business": "Нет",
    "has_avatar": "Да"
  },
  "extra": {
    "status_set_at": "2024-01-15T10:30:00Z",
    "avatar_hidden": "Нет",
    "preview_url": "https://..."
  }
}
```

### Batch Lookup

```bash
POST /api/v1/batch
Content-Type: application/json

{
  "query": ["79319999999", "testuser@gmail.com", "79858601908"]
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

### Health Check

```bash
GET /api/v1/health
```

## 🔧 Configuration

Create `.env` file:

```env
SERVICE_NAME=tw.tools.whatsapp
MODE=prod
HOST=0.0.0.0
PORT=8000

COUNT_USE_FOR_RELOAD=1000
SESSION_TIMEOUT=600
MAX_FAILURES_IN_ROW=30

VALIDATOR_URL=http://validator-service/api/v1/validate
BAILEYS_BRIDGE_URL=http://localhost:3000
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

## 🔄 Migration Changes

### Removed
- ❌ MongoDB session storage
- ❌ KeyDB/Redis external queue
- ❌ Proxy systems
- ❌ Payment integrations
- ❌ Winston/Pino logging
- ❌ External persistence

### Added
- ✅ In-memory session store
- ✅ In-memory queue
- ✅ Python native logging
- ✅ DDD architecture
- ✅ SMK-RK response format
- ✅ Validator integration
- ✅ Baileys HTTP bridge

## 📊 Response Format

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

# Test batch with validator
curl -X POST http://localhost:8000/api/v1/batch \
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