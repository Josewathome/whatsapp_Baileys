
---

# WhatsApp Profile Lookup Service - Python (DDD Refactor)

**Enterprise-ready WhatsApp profile lookup service implemented in Python with Domain-Driven Design principles.** Designed for high-throughput backend systems requiring real-time WhatsApp status and profile resolution.

## 🏗️ System Overview

* **Architecture**: Domain-Driven Design (DDD) for maintainable, testable, and scalable backend.
* **Python Service**: FastAPI-based REST endpoints, asynchronous processing, and in-memory session management.
* **Baileys Bridge**: Node.js service providing WhatsApp Web connectivity via HTTP.
* **Scalability**: Stateless Python services, designed for containerized deployment (Docker/Kubernetes).
* **Security & Standards**: JWT-compatible headers, role-based access patterns, SMK-RK compliant API responses.

### Core Components

| Layer               | Responsibility                                                          |
| ------------------- | ----------------------------------------------------------------------- |
| **api/**            | HTTP endpoints, request/response validation, FastAPI integration        |
| **controllers/**    | Orchestrates domain services, handles multi-step workflows              |
| **domain/**         | Core business logic: lookup, status, avatar, and business info services |
| **infrastructure/** | External adapters: WhatsApp client, queues, session store, logging      |
| **core/**           | Configuration, environment management, shared types                     |
| **main.py**         | Entry point, dependency injection, application bootstrap                |

---

## ⚡ Key Capabilities

* Session-based WhatsApp profile lookups without external databases.
* Real-time connection status monitoring and session management.
* Single and batch lookups with structured response standard.
* Automatic validation and type detection integrated via internal service.
* AI/automation ready: can be extended with asynchronous processing pipelines.

---

## 🚀 Deployment & Runtime

**Dockerized deployment preferred** for production. Python service is stateless, Baileys bridge handles external WhatsApp connections. Designed for horizontal scaling.

* Dev: `docker-compose -f docker-compose.dev.yml up -d`
* Prod: `docker-compose -f docker-compose.prod.yml up -d` (configure `.env`)

> Note: Endpoint and setup commands are in `/docs/SETUP.md` to keep the main README focused on architecture and purpose.

---

## 📡 API Highlights

* `/lookup` — single phone number resolution
* `/controller` — batch lookup orchestration
* `/session/start-registration` & `/complete-registration` — manage WhatsApp sessions
* `/session/status` — connection health monitoring
* `/session/restart` — reconnect session

All responses follow SMK-RK standard:

```json
{
  "headers": {"sender": "tw.tools.whatsapp"},
  "body": {...},
  "extra": {...}
}
```

---

## 💡 Design Principles

* **DDD Separation**: Each layer has clear responsibilities. No logic leaks into infrastructure or controllers.
* **Asynchronous & Event-driven**: Lookup and status services built to handle concurrent sessions.
* **No External DB Dependencies**: All state is in-memory or ephemeral for rapid scaling and failover.
* **Extensible Architecture**: New domain services can be added without touching existing routes or controllers.
* **Operational Awareness**: Built-in health checks, session monitoring, and structured logging.

---

## 🔧 Extending the Service

1. Add a new domain service in `domain/services/`.
2. Inject into `main.py`.
3. Add FastAPI route in `api/routes.py`.
4. Use structured SMK-RK response format.

---

## 🔐 Security & Operational Notes

* Baileys bridge should run behind private network or internal firewall.
* Sensitive environment variables handled via `.env`.
* Validator service must be internal-only.
* JWT / OAuth2 authentication can be added at the controller layer without changing domain logic.

---

## 📄 License & Ownership

* Proprietary: SMK-RK LLC
* Developed as part of production-grade automation backend.

---
