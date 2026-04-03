# Auth & User Microservice

Authentication and User Management service for the Smart Inventory Platform.
Built with **FastAPI** + **Motor (async MongoDB)** + **JWT**.

---

## Features

| Feature | Details |
|---|---|
| Registration | Email + username uniqueness enforced, password strength validated |
| Login | Returns signed JWT; prevents user enumeration |
| JWT Auth | HS256, configurable expiry, decoded on every protected request |
| RBAC | Admin / Customer / Supplier — enforced via FastAPI dependencies |
| Password | bcrypt hashed, change-password endpoint |
| User CRUD | Admins can list, update role/status, delete. Users can update own profile |
| Audit timestamps | `created_at`, `updated_at`, `last_login` on every user document |
| Simple UI | Served at `/` — register, login, view profile, list users |
| Swagger docs | Available at `/api/docs` |

---

## Project Structure

```
auth-service/
├── app/
│   ├── main.py                  ← FastAPI app, lifespan, route mounting
│   ├── core/
│   │   ├── config.py            ← All settings via pydantic-settings + .env
│   │   ├── database.py          ← Motor async client, indexes, connect/disconnect
│   │   ├── security.py          ← bcrypt hashing, JWT create/decode
│   │   └── logging.py           ← Logging setup
│   ├── models/
│   │   └── user.py              ← UserRole enum, UserStatus enum, document builder
│   ├── schemas/
│   │   └── user.py              ← All Pydantic request/response schemas
│   ├── repositories/
│   │   └── user_repository.py   ← All MongoDB operations (no business logic)
│   ├── services/
│   │   └── user_service.py      ← Business logic (register, login, update, etc.)
│   ├── api/v1/routes/
│   │   ├── auth.py              ← /auth/register, /auth/login, /auth/me
│   │   └── users.py             ← /users/ CRUD (list, get, update, delete)
│   └── utils/
│       └── dependencies.py      ← get_current_user, require_roles, require_admin
├── static/
│   └── index.html               ← Simple test UI
├── .env.example
├── requirements.txt
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- MongoDB running on Atlas Cloud

### Steps

```bash
# 1. Clone / enter the project
cd auth-service

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
# Edit .env — change SECRET_KEY to something long and random

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

The service will be available at:
- UI → http://localhost:8000
- Swagger → http://localhost:8000/api/docs
- Health → http://localhost:8000/health

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URL` | `mongodb:...` | MongoDB connection string |
| `DATABASE_NAME` | `ecommerce_db` | Database name |
| `SECRET_KEY` | *(change this!)* | JWT signing secret — min 32 chars |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token TTL in minutes |
| `DEBUG` | `False` | Enables DEBUG log level |

---

## API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | ❌ | Register a new user |
| POST | `/api/v1/auth/login` | ❌ | Login, get JWT |
| GET | `/api/v1/auth/me` | ✅ | Get current user profile |

### Users

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/api/v1/users/` | ✅ | Admin | List all users (paginated, filterable) |
| GET | `/api/v1/users/{id}` | ✅ | Self or Admin | Get user by ID |
| PUT | `/api/v1/users/{id}` | ✅ | Self or Admin | Update name/phone; Admin can change role/status |
| PUT | `/api/v1/users/{id}/password` | ✅ | Self only | Change password |
| DELETE | `/api/v1/users/{id}` | ✅ | Admin | Delete user |

---

## Request / Response Examples

### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass1",
  "full_name": "John Doe",
  "phone": "+91-9876543210",
  "role": "customer"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass1"
}
```
Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { ... }
}
```

### Protected Request
```http
GET /api/v1/auth/me
Authorization: Bearer eyJ...
```

---

## Roles and Permissions

| Action | Admin | Customer | Supplier |
|---|---|---|---|
| Register / Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| Update own name/phone | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |
| View any user | ✅ | ❌ | ❌ |
| List all users | ✅ | ❌ | ❌ |
| Change user role/status | ✅ | ❌ | ❌ |
| Delete any user | ✅ | ❌ | ❌ |

---

## Password Rules
- Minimum 8 characters
- At least one uppercase letter
- At least one digit

---

## Architecture Notes

- **Repository layer** (`user_repository.py`) — only talks to MongoDB, no logic
- **Service layer** (`user_service.py`) — all business rules live here
- **Route layer** (`routes/`) — thin; just maps HTTP ↔ service calls
- **Dependencies** (`dependencies.py`) — `get_current_user` and `require_roles()` are reusable guards injected via `Depends()`
