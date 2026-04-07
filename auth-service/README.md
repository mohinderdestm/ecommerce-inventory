# Smart Inventory & Order Management Platform — Backend

A production-style backend built with **FastAPI**, **Motor (async MongoDB)**, and **JWT**.
Designed with a clean three-layer architecture: **Repository → Service → Route**.

---

## Project Structure

```
auth-service/
│
├── app/
│   ├── main.py                          ← FastAPI app entry point, route registration, lifespan
│   │
│   ├── core/                            ← Infrastructure / cross-cutting concerns
│   │   ├── config.py                    ← All env variables via pydantic-settings (.env)
│   │   ├── database.py                  ← Motor async client, Atlas connection, all indexes
│   │   ├── security.py                  ← bcrypt hashing, JWT create/decode
│   │   └── log_config.py               ← Logging setup (structured, level from DEBUG flag)
│   │
│   ├── models/                          ← Raw MongoDB document shape + enums
│   │   ├── user.py                      ← UserRole, UserStatus, build_user_document()
│   │   └── product.py                   ← ProductStatus, ProductUnit, build_product_document(),
│   │                                       build_category_document()
│   │
│   ├── schemas/                         ← Pydantic request/response validation schemas
│   │   ├── user.py                      ← UserRegisterRequest, UserLoginRequest, UserResponse,
│   │   │                                   UserUpdateRequest, PasswordChangeRequest, TokenResponse
│   │   └── product.py                   ← ProductCreateRequest, ProductUpdateRequest, ProductResponse,
│   │                                       CategoryCreateRequest, CategoryUpdateRequest,
│   │                                       CategoryResponse, ImageMetadata, ProductListResponse
│   │
│   ├── repositories/                    ← MongoDB operations only — zero business logic
│   │   ├── user_repository.py           ← CRUD + find_by_email/username, list with pagination
│   │   ├── category_repository.py       ← CRUD + name uniqueness, children check, slug
│   │   └── product_repository.py        ← CRUD + SKU lookup, flexible search with filters
│   │
│   ├── services/                        ← All business logic lives here
│   │   ├── user_service.py              ← Register, login, update, change-password, delete
│   │   ├── category_service.py          ← Category CRUD with safety checks (children, products)
│   │   └── product_service.py           ← Product CRUD, SKU auto-generation, price validation
│   │
│   ├── api/v1/routes/                   ← Thin HTTP layer — maps requests to service calls
│   │   ├── auth.py                      ← POST /auth/register, /auth/login, GET /auth/me
│   │   ├── users.py                     ← GET/PUT/DELETE /users/, /users/{id}
│   │   ├── categories.py                ← CRUD /categories/
│   │   └── products.py                  ← CRUD /products/ with search and SKU lookup
│   │
│   └── utils/
│       ├── dependencies.py              ← get_current_user, require_roles(), require_admin
│       └── sku_generator.py             ← Auto-generates SKUs: NIK-SHO-2604XXXX
│
├── static/
│   └── index.html                       ← Minimal dark UI (register, login, profile, users)
│
├── .env                                 ← Your secrets 
├── .env.example                         ← Safe template with placeholder values
├── .gitignore                           ← Excludes .env, venv, __pycache__, etc.
├── requirements.txt                     ← All Python dependencies pinned
└── README.md                            ← This file
```

---

## Modules Implemented

| # | Module | Status |
|---|---|---|
| 1 | Authentication & User Management | ✅ Done |
| 2 | Product Catalog Management | ✅ Done |
| 3 | Supplier Management | ⏳ Pending |
| 4 | Warehouse Management | ⏳ Pending |
| 5 | Inventory Movement Tracking | ⏳ Pending |
| 6 | Purchase Order Management | ⏳ Pending |
| 7 | Sales Order Management | ⏳ Pending |
| 8 | Alerts & Notifications | ⏳ Pending |
| 9 | Reports & Analytics | ⏳ Pending |
| 10 | Audit Logs | ⏳ Pending |

---

## Local Setup

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (or local MongoDB on port 27017)

### Steps

```bash
# 1. Enter the project directory
cd auth-service

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
# Then fill in your real values

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

### URLs
| Page | URL |
|---|---|
| Swagger (API docs) | http://127.0.0.1:8000/api/docs |
| ReDoc | http://127.0.0.1:8000/api/redoc |
| Simple UI | http://127.0.0.1:8000 |
| Health check | http://127.0.0.1:8000/health |

---

## Environment Variables

```env
MONGO_URL = mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/
DB_NAME = ecommerce_db

SECRET_KEY = <your-64-char-hex-secret-key>
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DEBUG = False
```

---

## API Reference

### Authentication — `/api/v1/auth`

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| POST | `/auth/register` | ❌ | Register new user |
| POST | `/auth/login` | ❌ | Login, returns JWT token |
| GET | `/auth/me` | ✅ | Get current logged-in user |

### Users — `/api/v1/users`

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/users/` | Admin | List all users (paginated, filterable by role/status) |
| GET | `/users/{id}` | Self or Admin | Get user by ID |
| PUT | `/users/{id}` | Self or Admin | Update name/phone; Admin can change role/status |
| PUT | `/users/{id}/password` | Self only | Change own password |
| DELETE | `/users/{id}` | Admin | Delete user |

### Categories — `/api/v1/categories`

| Method | Endpoint | Role | Description |
|---|---|---|---|
| POST | `/categories/` | Admin | Create category or subcategory |
| GET | `/categories/` | Any | List categories (filter by `parent_id` for subcategories) |
| GET | `/categories/{id}` | Any | Get category by ID |
| PUT | `/categories/{id}` | Admin | Update category |
| DELETE | `/categories/{id}` | Admin | Delete category (blocked if has subcategories or products) |

### Products — `/api/v1/products`

| Method | Endpoint | Role | Description |
|---|---|---|---|
| POST | `/products/` | Admin / Supplier | Create product (SKU auto-generated if not provided) |
| GET | `/products/` | Any | Search and list products (see filters below) |
| GET | `/products/sku/{sku}` | Any | Get product by SKU |
| GET | `/products/{id}` | Any | Get product by ID |
| PUT | `/products/{id}` | Admin / Supplier | Update product |
| DELETE | `/products/{id}` | Admin | Delete product |

#### Product Search Filters (`GET /products/`)
| Query Param | Type | Description |
|---|---|---|
| `q` | string | Search across name, SKU, brand, description |
| `category_id` | string | Filter by category |
| `supplier_id` | string | Filter by supplier |
| `status` | string | active / inactive / discontinued / out_of_stock |
| `min_price` | float | Minimum selling price |
| `max_price` | float | Maximum selling price |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

---

## Roles & Permissions

| Action | Admin | Customer | Supplier |
|---|---|---|---|
| Register / Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| Update own profile | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |
| View / search products | ✅ | ✅ | ✅ |
| View categories | ✅ | ✅ | ✅ |
| Create / update product | ✅ | ❌ | ✅ |
| Delete product | ✅ | ❌ | ❌ |
| Manage categories | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ |

---

## MongoDB Collections

| Collection | Indexes |
|---|---|
| `users` | `email` (unique), `username` (unique), `role` |
| `categories` | `slug` (unique), `parent_id`, `is_active` |
| `products` | `sku` (unique), `category_id`, `status`, `supplier_ids`, text index on name/brand/description |

---

## SKU Format

SKUs are auto-generated in the format:

```
<BRAND_PREFIX>-<CATEGORY_PREFIX>-<YYMM><RANDOM4>

Example: NIK-SHO-26041A3X
         ^^^  ^^^  ^^^^ ^^^^
         │    │    │    └─ 4 random alphanumeric chars
         │    │    └─ Year + Month (2604 = April 2026)
         │    └─ First 3 letters of category
         └─ First 3 letters of brand
```

You can also supply your own SKU in the request — auto-generation only happens when the `sku` field is left empty.

---

## Architecture Notes

The entire codebase follows a strict three-layer pattern:

```
HTTP Request
    ↓
Route (app/api/v1/routes/)
    → validates input via Pydantic schema
    → calls Service method
        ↓
    Service (app/services/)
        → applies business rules
        → raises HTTPException for violations
        → calls Repository method(s)
            ↓
        Repository (app/repositories/)
            → executes MongoDB queries
            → returns plain dicts
            ↓
        ← returns data
    ← returns data
← HTTP Response (serialized via Pydantic response model)
```

**Rule:** Repositories never contain business logic. Services never call MongoDB directly. Routes never contain business logic.
