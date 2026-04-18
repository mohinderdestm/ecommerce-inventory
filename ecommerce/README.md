# Smart Inventory & Order Management Platform

A production-style full-stack application built with **FastAPI**, **Motor (async MongoDB)**, **JWT**, and **React + Vite**.
Backend follows a strict three-layer architecture: **Repository → Service → Route**.

---

## Project Structure

```
ecommerce-inventory/
│
├── ecommerce/                          ← Backend (FastAPI + MongoDB)
│   ├── .env                               ← Secrets — NEVER commit
│   ├── .env.example                       ← Safe template
│   ├── .gitignore
│   ├── requirements.txt
│   ├── README.md
│   │
│   ├── app/
│   │   ├── main.py                        ← FastAPI entry point, all route registration, lifespan
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                  ← Env vars via pydantic-settings (MONGO_URL, SECRET_KEY etc.)
│   │   │   ├── database.py                ← Motor async client, Atlas connection, all indexes on startup
│   │   │   ├── security.py                ← bcrypt password hashing, JWT create/decode
│   │   │   └── log_config.py              ← Structured logging setup
│   │   │
│   │   ├── models/                        ← MongoDB document shapes + enums
│   │   │   ├── user.py                    ← UserRole (admin/customer/supplier/warehouse_staff)
│   │   │   ├── product.py                 ← ProductStatus, ProductUnit, document builders
│   │   │   ├── variant.py                 ← Variant document builder + SKU generator
│   │   │   ├── supplier.py                ← SupplierStatus, PaymentTerms
│   │   │   ├── warehouse.py               ← WarehouseStatus, TransferStatus
│   │   │   └── sales_order.py             ← SalesOrderStatus, VALID_TRANSITIONS, order/item builders
│   │   │
│   │   ├── schemas/                       ← Pydantic request/response validation
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── variant.py
│   │   │   ├── supplier.py
│   │   │   ├── warehouse.py
│   │   │   └── sales_order.py
│   │   │
│   │   ├── repositories/                  ← Pure MongoDB operations, zero business logic
│   │   │   ├── user_repository.py
│   │   │   ├── category_repository.py
│   │   │   ├── product_repository.py
│   │   │   ├── variant_repository.py      ← Separate variants collection + aggregation pipeline
│   │   │   ├── supplier_repository.py
│   │   │   ├── warehouse_repository.py    ← Also handles warehouse_stock + stock_transfers
│   │   │   └── sales_order_repository.py
│   │   │
│   │   ├── services/                      ← All business logic
│   │   │   ├── user_service.py            ← Auto-creates supplier profile on supplier registration
│   │   │   ├── category_service.py
│   │   │   ├── product_service.py         ← Enriches search results with variant summary via aggregation
│   │   │   ├── variant_service.py         ← SKU generation, uniqueness checks
│   │   │   ├── supplier_service.py        ← Bidirectional product-supplier linking
│   │   │   ├── warehouse_service.py       ← Stock management, warehouse-to-warehouse transfers
│   │   │   └── sales_order_service.py     ← Full workflow: draft→confirm→pack→ship→deliver/cancel/return
│   │   │
│   │   ├── api/v1/routes/                 ← Thin HTTP layer, maps requests → services
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── categories.py
│   │   │   ├── products.py
│   │   │   ├── variants.py
│   │   │   ├── suppliers.py
│   │   │   ├── warehouses.py
│   │   │   └── sales_orders.py
│   │   │
│   │   └── utils/
│   │       ├── dependencies.py            ← get_current_user, require_roles(), require_admin,
│   │       │                                 require_admin_or_warehouse_staff
│   │       └── sku_generator.py           ← Auto-generates NIK-SHO-2604XXXX style SKUs
│   │
│   └── static/                            ← React build output (served by FastAPI at /)
│       ├── index.html
│       └── assets/
│
└── frontend/                              ← React + Vite source
    ├── package.json
    ├── vite.config.js                     ← Proxies /api → :8000 in dev, builds → auth-service/static
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx                        ← Router, CartProvider, ToastProvider, PrivateLayout guard
        ├── App.css                        ← Complete design system (dark theme, CSS variables)
        ├── index.css                      ← Imports Inter font only
        ├── api.js                         ← Fetch wrapper with ApiError class, auto-redirect on 401
        │
        ├── context/
        │   ├── AuthContext.jsx            ← Global auth state, verifies token with /auth/me on load
        │   └── CartContext.jsx            ← Cart state with localStorage persistence
        │
        ├── hooks/
        │   └── useDebounce.js             ← Debounce hook (used in search inputs)
        │
        ├── components/
        │   ├── Navbar.jsx                 ← Top bar, role badge, avatar, cart button (customers only)
        │   ├── Sidebar.jsx                ← Collapsible nav with role-based link visibility
        │   ├── Cart.jsx                   ← Sliding cart drawer with qty controls
        │   ├── Toast.jsx                  ← Toast notification system (success/error/info/warning)
        │   └── UI.jsx                     ← StatusBadge, Alert, Spinner, Skeleton, Empty,
        │                                     Modal, ConfirmDialog, ColorSwatch, Pagination,
        │                                     OrderStatus, StatCard
        │
        └── pages/
            ├── Login.jsx
            ├── Register.jsx               ← All 4 roles (customer/supplier/warehouse_staff/admin)
            ├── Dashboard.jsx              ← Stats: products, suppliers, warehouses, orders by status
            ├── Products.jsx               ← Grid with search, status chips, modal, edit/delete,
            │                                 Add to Cart for customers, variant selection in modal
            ├── Suppliers.jsx              ← Table with debounced search, create/edit modal, confirm delete
            ├── SalesOrders.jsx            ← Expandable order cards with inline workflow actions
            ├── CreateOrder.jsx            ← Auto pre-fills from cart, clears cart on success
            ├── Warehouses.jsx             ← Warehouse cards + stock modal + stock update form
            └── OtherPages.jsx             ← Categories, Variants, Profile pages
```

---

## Modules Status

| # | Module | Backend | Frontend |
|---|---|---|---|
| 1 | Authentication & User Management | ✅ | ✅ |
| 2 | Product Catalog + Variants | ✅ | ✅ |
| 3 | Supplier Management | ✅ | ✅ |
| 4 | Warehouse Management + Stock Transfers | ✅ | ✅ |
| 5 | Inventory Movement Tracking | ⏳ | ⏳ |
| 6 | Purchase Order Management | ⏳ | ⏳ |
| 7 | Sales Order Management | ✅ | ✅ |
| 8 | Alerts & Notifications | ⏳ | ⏳ |
| 9 | Reports & Analytics | ⏳ | ⏳ |
| 10 | Audit Logs | ⏳ | ⏳ |

**Bonus:** Cart system (Add to Cart → Cart drawer → Create Order with pre-filled items)

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account

### Backend

```bash
cd auth-service

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Create .env from template and fill in your values
copy .env.example .env

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

# Development (with hot reload, proxies /api to :8000)
npm run dev        # → http://localhost:3000

# Build for production (outputs to auth-service/static/)
npm run build      # then visit http://127.0.0.1:8000
```

### URLs

| | URL |
|---|---|
| React dev server | http://localhost:3000 |
| FastAPI + built React | http://127.0.0.1:8000 |
| Swagger API docs | http://127.0.0.1:8000/api/docs |
| ReDoc | http://127.0.0.1:8000/api/redoc |
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

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | ❌ | Register (auto-creates supplier profile if role=supplier) |
| POST | `/api/v1/auth/login` | ❌ | Login, returns JWT |
| GET  | `/api/v1/auth/me` | ✅ | Get current user |

### Users

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/api/v1/users/` | Admin | List users (paginated, filter by role/status) |
| GET | `/api/v1/users/{id}` | Self / Admin | Get user |
| PUT | `/api/v1/users/{id}` | Self / Admin | Update profile; Admin can change role/status |
| PUT | `/api/v1/users/{id}/password` | Self | Change password |
| DELETE | `/api/v1/users/{id}` | Admin | Delete user |

### Products & Categories

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/api/v1/categories/` | Any | List categories |
| POST | `/api/v1/categories/` | Admin | Create category/subcategory |
| PUT/DELETE | `/api/v1/categories/{id}` | Admin | Update/delete (blocked if has children/products) |
| GET | `/api/v1/products/` | Any | Search products (q, category, supplier, status, price range) |
| POST | `/api/v1/products/` | Admin/Supplier | Create product (SKU auto-generated) |
| PUT/DELETE | `/api/v1/products/{id}` | Admin/Supplier | Update/delete |
| GET | `/api/v1/products/{id}/variants/` | Any | List variants for product |
| POST | `/api/v1/products/{id}/variants/` | Admin/Supplier | Add variants (bulk) |
| PUT/DELETE | `/api/v1/products/{id}/variants/{variant_id}` | Admin/Supplier | Update/delete variant |

### Suppliers

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/api/v1/suppliers/` | Any | List/search suppliers |
| POST | `/api/v1/suppliers/` | Admin | Create supplier |
| PUT | `/api/v1/suppliers/{id}` | Admin | Update supplier |
| DELETE | `/api/v1/suppliers/{id}` | Admin | Delete (blocked if has products linked) |
| PATCH | `/api/v1/suppliers/{id}/rating` | Admin | Update rating (0–5) |
| POST | `/api/v1/suppliers/{id}/products` | Admin | Link products to supplier |
| DELETE | `/api/v1/suppliers/{id}/products` | Admin | Unlink products |
| GET | `/api/v1/suppliers/by-product/{product_id}` | Any | Get all suppliers for a product |

### Warehouses

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/api/v1/warehouses/` | Admin/Staff | List warehouses (staff see only assigned) |
| POST | `/api/v1/warehouses/` | Admin | Create warehouse |
| PUT/DELETE | `/api/v1/warehouses/{id}` | Admin | Update/delete (blocked if has stock) |
| POST | `/api/v1/warehouses/{id}/staff` | Admin | Assign staff |
| DELETE | `/api/v1/warehouses/{id}/staff` | Admin | Remove staff |
| POST | `/api/v1/warehouses/{id}/stock` | Admin/Staff* | Add/reduce stock |
| GET | `/api/v1/warehouses/{id}/stock` | Admin/Staff* | Stock summary |
| POST | `/api/v1/warehouses/{id}/transfer` | Admin/Staff* | Transfer stock between warehouses |
| GET | `/api/v1/warehouses/transfers/list` | Admin/Staff | Transfer history |
| GET | `/api/v1/warehouses/stock/product/{id}` | Admin/Staff | Product stock across all warehouses |

*Staff can only operate warehouses they are assigned to.

### Sales Orders

| Method | Endpoint | Role | Description |
|---|---|---|---|
| POST | `/api/v1/sales-orders/` | Customer/Admin/Staff | Create order (Draft) |
| GET | `/api/v1/sales-orders/` | Any | List orders (customers see own only) |
| GET | `/api/v1/sales-orders/summary` | Any | Order counts + values by status |
| GET | `/api/v1/sales-orders/{id}` | Any | Get order detail |
| POST | `/api/v1/sales-orders/{id}/confirm` | Admin/Staff | Validate stock + reserve |
| POST | `/api/v1/sales-orders/{id}/pack` | Admin/Staff | Mark packed |
| POST | `/api/v1/sales-orders/{id}/ship` | Admin | Mark shipped |
| POST | `/api/v1/sales-orders/{id}/deliver` | Admin | Mark delivered |
| POST | `/api/v1/sales-orders/{id}/cancel` | Admin/Customer/Staff | Cancel + release stock |
| POST | `/api/v1/sales-orders/{id}/return` | Admin/Staff | Return + restore stock |

---

## Roles & Permissions

| Action | Admin | Customer | Supplier | Warehouse Staff |
|---|---|---|---|---|
| Register / Login | ✅ | ✅ | ✅ | ✅ |
| View/update own profile | ✅ | ✅ | ✅ | ✅ |
| Browse products | ✅ | ✅ | ✅ | ✅ |
| Add to cart | ❌ | ✅ | ❌ | ❌ |
| Create sales order | ✅ | ✅ | ❌ | ✅ |
| Create/update product | ✅ | ❌ | ✅ | ❌ |
| Delete product | ✅ | ❌ | ❌ | ❌ |
| Manage categories | ✅ | ❌ | ❌ | ❌ |
| Manage suppliers | ✅ | ❌ | ❌ | ❌ |
| Create warehouse | ✅ | ❌ | ❌ | ❌ |
| Update stock / transfer | ✅ | ❌ | ❌ | ✅ (assigned only) |
| Confirm/pack orders | ✅ | ❌ | ❌ | ✅ |
| Ship/deliver orders | ✅ | ❌ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ | ❌ |

---

## MongoDB Collections

| Collection | Purpose | Key Indexes |
|---|---|---|
| `users` | All user accounts | `email` (unique), `username` (unique), `role` |
| `categories` | Product categories + subcategories | `slug` (unique), `parent_id`, `is_active` |
| `products` | Product catalog | `sku` (unique), `category_id`, `status`, text index |
| `variants` | Product variants (separate collection) | `variant_id` (unique), `sku` (unique), `product_id` |
| `suppliers` | Supplier profiles | `email`, `gst_number`, `status` |
| `warehouses` | Warehouse locations | `name` (unique), `status`, `staff_ids` |
| `warehouse_stock` | Stock per warehouse × product × variant | compound unique on (warehouse, product, variant) |
| `stock_transfers` | Transfer history | `from_warehouse_id`, `to_warehouse_id`, `status` |
| `sales_orders` | Customer orders with full history | `order_number` (unique), `customer_id`, `status` |

---

## Order Workflow

```
Draft → Confirmed → Packed → Shipped → Delivered
                                         ↓
                  ↓ (any stage)        Returned
               Cancelled
```

- **Draft** — Created, no stock impact
- **Confirmed** — Stock validated and reserved (deducted from warehouse)
- **Packed** — Physically prepared
- **Shipped** — Dispatched to customer
- **Delivered** — Successfully received
- **Cancelled** — Reserved stock released back to warehouse
- **Returned** — Stock restored to warehouse

---

## Cart Flow (Customer)

```
Browse Products → Add to Cart (card button or modal)
                       ↓
              Cart drawer (qty controls, remove, total)
                       ↓
              "Proceed to Order" → CreateOrder page
              (items pre-filled, enter warehouse ID + shipping)
                       ↓
              Create Order (Draft) → cart cleared
                       ↓
              Admin/Staff confirms → stock reserved → fulfillment
```

---

## SKU Format

```
<BRAND_PREFIX>-<CATEGORY_PREFIX>-<YYMM><RANDOM4>

Example: NIK-SHO-26041A3X
         ^^^  ^^^  ^^^^ ^^^^
         │    │    │    └─ 4 random alphanumeric chars
         │    │    └─ Year + Month
         │    └─ First 3 letters of category
         └─ First 3 letters of brand

Variant SKU: NIK-SHO-26041A3X-BLA-8G-256G
                               ^^^  ^^  ^^^^
                               Color RAM  ROM
```

---

## Architecture

```
HTTP Request
    ↓
Route  → validates via Pydantic schema → calls Service
    ↓
Service → applies business rules → calls Repository
    ↓
Repository → executes MongoDB query → returns dict
    ↓
← Response serialized via Pydantic response model
```

**Rules:**
- Repositories never contain business logic
- Services never call MongoDB directly
- Routes never contain business logic
- Every new module adds one file per layer (model, schema, repository, service, route)