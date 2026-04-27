# Smart Inventory & Order Management Platform

A production-style backend system built with **Python**, **FastAPI**, and **MongoDB** for managing products, warehouses, suppliers, stock movement, purchase orders, sales orders, alerts, and business analytics.

This project is designed to simulate a real-world inventory and operations platform used by growing businesses. It focuses on clean API design, scalable architecture, business workflows, reporting, and team collaboration.

## Overview

The **Smart Inventory & Order Management Platform** helps businesses manage their day-to-day inventory operations across multiple warehouses and user roles.

It supports:

- Product and category management
- Supplier and procurement workflows
- Warehouse stock tracking
- Inventory movement and stock ledger
- Purchase and sales order processing
- Alerts and notifications
- Reports and analytics
- Authentication, authorization, and audit logs

This project is intentionally large and modular, making it a strong assignment for interns to work on both independently and collaboratively.

## Project Objective

Build a scalable backend application using **FastAPI** and **MongoDB** that enables a business to:

- Manage products, categories, suppliers, and warehouses
- Track stock across multiple warehouse locations
- Create and manage purchase orders and sales orders
- Record inward and outward inventory movement
- Detect low-stock situations and generate alerts
- Provide dashboards and reports for management
- Support authentication, authorization, and audit logging
- Expose clean REST APIs with proper validation and documentation

## Why This Project

This project gives interns hands-on exposure to real backend engineering challenges, including:

- API design with FastAPI
- MongoDB schema design for real-world systems
- Authentication and role-based authorization
- Background jobs and scheduled tasks
- Data validation and error handling
- Aggregation pipelines and analytics queries
- Pagination, filtering, and search
- Logging, testing, and documentation
- Git-based collaboration and modular architecture

It is complex enough to resemble an industry-grade backend system while still being divisible into smaller modules for multiple contributors.

## User Roles

The system should support multiple roles with role-based permissions:

- **Admin**
- **Inventory Manager**
- **Warehouse Staff**
- **Finance Staff**
- **Viewer**

## Core Modules

### 1. Authentication and User Management

Build a secure authentication and authorization system.

**Features**
- User registration and login
- JWT-based authentication
- Role-based access control

### 2. Product Catalog Management

Manage product-related information and metadata.

**Features**
- Create, update, delete, and fetch products
- Product categories and subcategories
- SKU generation
- Product pricing
- Search by name, SKU, category, or supplier
- Product image metadata storage

**Suggested Product Fields**
- Product ID
- Name
- SKU
- Description
- Category
- Brand
- Supplier IDs
- Cost price
- Selling price
- Reorder level
- Tax percentage
- Unit
- Status
- Created by
- Updated by

### 3. Supplier Management

Manage supplier details and supplier-related procurement information.

**Features**
- Add and update supplier details
- Supplier contact information
- Supplier rating
- Supplier-product mapping
- Supplier status
- Supplier performance summary

**Suggested Supplier Fields**
- Supplier name
- Contact person
- Phone
- Email
- Address
- GST or tax ID
- Payment terms
- Active status

### 4. Sales Order Management

Support customer-side order processing and fulfillment.

**Features**
- Create sales orders
- Add products and quantities
- Validate stock before confirming
- Reserve stock
- Fulfill and dispatch orders
- Handle cancelled orders
- Handle returns
- Generate order summaries

**Possible Statuses**
- Draft
- Confirmed
- Packed
- Shipped
- Delivered
- Cancelled
- Returned

### 5. Warehouse Management

Support multiple warehouses and warehouse-specific stock visibility.

**Features**
- Add warehouses
- Define warehouse addresses
- Assign staff to warehouses
- Track stock per warehouse
- Warehouse-level stock summary
- Enable stock transfer between warehouses

### 6. Inventory Movement Tracking

Track all inventory changes across the system.

**Features**
- Record stock inward
- Record stock outward
- Record returns
- Record damaged or expired inventory
- Track warehouse-to-warehouse transfers
- Maintain inventory ledger for every product

**Movement Data Should Include**
- Product ID
- Warehouse ID
- Movement type
- Quantity
- Reference type such as purchase order or sales order
- Reference ID
- Performed by
- Timestamp
- Remarks

### 7. Purchase Order Management

Handle procurement workflows from suppliers.

**Features**
- Create draft purchase orders
- Add multiple items to an order
- Approve or reject purchase orders
- Track order status
- Mark partial and full receipt
- Attach invoice or bill metadata
- Update inventory when items are received

**Possible Statuses**
- Draft
- Submitted
- Approved
- Rejected
- Partially Received
- Completed
- Cancelled

### 8. Alerts and Notifications

Automate operational and business-critical notifications.

**Features**
- Low-stock alerts
- Unfulfilled sales order alerts
- Notification logs
- Email simulation 

This module can be implemented using scheduled background jobs.

### 9. Reports and Analytics

Provide management-level visibility into inventory and operations.

**Features**
- Stock summary by warehouse
- Low-stock report
- Top-selling products
- Supplier-wise purchase report
- Dead stock report
- Monthly inward vs outward report

This module is especially useful for learning advanced **MongoDB aggregation pipelines**.

### 10. Audit Logs

Track critical actions performed in the system.

**Examples**
- Who created or updated a product
- Who approved a purchase order
- Who changed stock quantities
- Who cancelled an order

**Audit Log Fields**
- User ID
- Action
- Entity type
- Entity ID
- Old value
- New value
- Timestamp
- IP address or request metadata

## Technical Requirements

The platform should be built with the following expectations:

- **FastAPI** for REST API development
- **MongoDB** for data storage
- **Pydantic** for request and response validation
- **JWT** authentication
- Async endpoints where appropriate
- Clean and modular folder structure
- Environment-based configuration
- Logging and monitoring support
- Exception handling
- Swagger documentation
- Unit tests and integration tests
- Seed scripts for dummy data

## Suggested Tools

- FastAPI
- MongoDB
- Motor or PyMongo
- Pydantic
- Passlib or bcrypt
- Python-Jose for JWT
- Pytest
- Celery or APScheduler for background tasks
- Redis for caching or queueing (optional)

## Suggested Architecture

A possible project structure:

```bash
app/
├── main.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── logging.py
├── api/
│   └── v1/
│       └── routes/
│           ├── auth.py
│           ├── users.py
│           ├── products.py
│           ├── suppliers.py
│           ├── warehouses.py
│           ├── inventory.py
│           ├── purchase_orders.py
│           ├── sales_orders.py
│           ├── alerts.py
│           └── reports.py
├── models/
├── schemas/
├── services/
├── repositories/
├── utils/
└── tests/
scripts/
Dockerfile
docker-compose.yml
README.md
```

## Functional Requirements

The system should support:

- Secure login and protected APIs
- CRUD operations for major entities
- Pagination, filtering, and sorting
- Data validation with meaningful error messages
- Soft delete where needed
- Status-based workflows for orders
- Atomic stock updates to avoid inconsistency
- Role-based permissions
- Report generation with filters and date ranges
- Consistent API response format

## Non-Functional Requirements

The project should also demonstrate strong engineering practices:

- Clean, readable, and maintainable code
- Reusable service and repository layers
- Scalable architecture
- Good naming conventions
- Proper comments and docstrings
- API documentation
- Test coverage for major modules
- Easy local setup
- Dockerized development environment

## Example API Scope

Example endpoints the team may implement:

```http
POST   /api/v1/auth/login
POST   /api/v1/users
GET    /api/v1/products
POST   /api/v1/products
PUT    /api/v1/products/{id}
POST   /api/v1/suppliers
POST   /api/v1/warehouses
POST   /api/v1/inventory/movement
POST   /api/v1/purchase-orders
POST   /api/v1/purchase-orders/{id}/approve
POST   /api/v1/purchase-orders/{id}/receive
POST   /api/v1/sales-orders
POST   /api/v1/sales-orders/{id}/dispatch
GET    /api/v1/reports/stock-summary
GET    /api/v1/reports/top-selling-products
```

This project is not just about CRUD APIs. The main goal is to build a backend system that reflects how real businesses handle inventory, procurement, sales, and operational tracking.

A successful implementation should show strong backend fundamentals, clear architecture, proper validation, secure access control, and reliable business workflows.
