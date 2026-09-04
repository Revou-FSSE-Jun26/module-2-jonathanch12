# RevoShop — A Simple e-Commerce Backend [IN DEVELOPMENT]

RevoShop is a backend API for an online retail store, built with Flask and PostgreSQL. It provides RESTful endpoints for managing users, products, categories, and orders, with JWT-based authentication and role-based access control (admin/customer).

---

## Project Goals

- Build a Flask application using the application factory pattern, connected to PostgreSQL via SQLAlchemy.
- Define models that mirror the database schema (users, products, categories, orders, order_items).
- Implement JWT authentication with role-based access control (admin, customer).
- Implement CRUD routes for users, products, categories, and orders.
- Support soft deletion for products, categories, and orders.
- Manage schema changes using Flask-Migrate (Alembic).
- Demonstrate a many-to-many relationship between orders and products through an association table.
- Include unit tests using pytest and load testing using Locust.

---

## Tech Stack

- **Language:** Python 3
- **Framework:** Flask
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (via Flask-SQLAlchemy)
- **Migrations:** Flask-Migrate (Alembic)
- **Authentication:** Flask-JWT-Extended (JWT access and refresh tokens)
- **Password Hashing:** bcrypt
- **Testing:** pytest (unit tests), Locust (load/performance testing)

---

## Database

The application uses a PostgreSQL database with the following tables:

| Table | Description |
|-------|-------------|
| `users` | Registered users (name, email, password, address, role) |
| `categories` | Product categories with soft deletion (name, description, is_deleted) |
| `products` | Products linked to a category with soft deletion (name, description, price, stock, is_deleted) |
| `orders` | Orders placed by users with soft deletion (total_amount, status, is_deleted) |
| `order_items` | Association table linking orders to products (quantity, unit_price) |

### ERD (Entity Relationship Diagram)

![ERD Diagram](database/Schema%20Diagram%20(ERD_Screenshot_DBeaver).png)

---

## Folder Structure

```
module-2-jonathanch12/
├── database/
│   ├── schema.sql                              # Table creation scripts
│   ├── seed.sql                                # Sample data (SQL)
│   ├── queries.sql                             # Example queries
│   └── Schema Diagram (ERD_Screenshot_DBeaver).png
├── helper/
│   └── seed.py                                 # Python database seeder for users, categories, and products
│   └── seed_order.py                           # Python database seeder for orders
├── migrations/
│   ├── versions/                               # Migration history
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── routes/
│   ├── __init__.py                             # Blueprint exports
│   ├── main.py                                 # Home/health check route
│   ├── user.py                                 # User registration and retrieval
│   ├── auth.py                                 # Login (JWT token generation)
│   ├── product.py                              # Product CRUD (admin-protected)
│   ├── category.py                             # Category CRUD (admin-protected)
│   └── order.py                                # Order creation and management
├── tests/
│   ├── conftest.py                             # Pytest fixtures (app, client, tokens)
│   ├── test_auth.py                            # Login route tests
│   ├── test_user.py                            # Registration route tests
│   ├── test_category.py                        # Category route tests
│   ├── test_product.py                         # Product route tests
│   └── test_order.py                           # Order route tests
├── testing_screenshots/                        # Pytest and Locust testing screenshots
├── .env                                        # Environment variables (not committed)
├── .env.example                                # Environment variable template
├── .gitignore
├── app.py                                      # Flask app factory (create_app)
├── models.py                                   # SQLAlchemy models
├── locustfile.py                               # Load testing configuration
├── requirements.txt                            # Python dependencies
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3 installed
- PostgreSQL installed and running
- DBeaver (or any PostgreSQL client) for database management

### 1. Clone the Repository

```bash
git clone <repository-url>
cd module-2-jonathanch12
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
```

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

1. Create a new PostgreSQL database.
2. Execute `database/schema.sql` to create the tables.
3. Run migrations as applied:
   ```bash
   flask db upgrade
   ```
4. Run `seed.py` from `helper` folder to populate the database with users, categories, and products data.
5. Run `seed_order.py` from `helper` folder to populate the database with orders data.

### 5. Configure the `.env` File

Create a `.env` file in the project root (see `.env.example` for reference):

```
DATABASE_URL="postgresql://username:password@localhost/your_db_name"
JWT_SECRET_KEY="your-generated-secret-key"
```

Generate the JWT secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Seed the Database

```bash
python helper/seed.py
```

This inserts sample users (with bcrypt-hashed passwords), categories, and products.

### 7. Run the Application

```bash
flask run --debug
```

The app will be available at `http://127.0.0.1:5000`.

---

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/products/` | List all products |
| GET | `/products/<id>` | Get product by ID |
| GET | `/categories/` | List all categories |
| GET | `/categories/<id>` | Get category by ID (includes products) |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login (returns JWT access and refresh tokens) |
| POST | `/users/` | Register a new user |
| GET | `/users/<id>` | Get user by ID |

### Admin-Protected Routes (requires admin JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/products/` | Create a product |
| PUT | `/products/<id>` | Update a product |
| DELETE | `/products/<id>` | Soft-delete a product |
| POST | `/categories/` | Create a category |
| PUT | `/categories/<id>` | Update a category |
| DELETE | `/categories/<id>` | Soft-delete a category |
| GET | `/orders/<id>` | View a specific order |
| DELETE | `/orders/<id>` | Soft-delete an order (blocked if processing/delivering) |

### Customer-Protected Routes (requires customer JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/orders/` | Place a new order |

### Shared Order Routes (Customer and Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | List orders (customer: own orders only, admin: all orders) |
| PUT | `/orders/<id>` | Update order status (admin: advance the flow; customer: cancel own pending order) |

---

## Order Status Workflow

Orders follow a forward-only status lifecycle. The `PUT /orders/<id>` route enforces the rules below.

```
pending --> processing --> delivering --> completed
   |            |              |
   +------------+--------------+--------> cancelled
```

**Admin** can advance an order one step at a time and cannot revert or skip statuses:

| Current status | Allowed next statuses |
|----------------|-----------------------|
| `pending` | `processing`, `cancelled` |
| `processing` | `delivering`, `cancelled` |
| `delivering` | `completed`, `cancelled` |
| `completed` | none (terminal) |
| `cancelled` | none (terminal) |

**Customer** can only cancel their own order, and only while it is still `pending`.

When an order is cancelled (by either role), the reserved product stock is automatically restored. Since the project has no payment integration, cancellation acts as the logical equivalent of a refund.

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After logging in, include the access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

- **Access token** expires in 1 hour.
- **Refresh token** expires in 7 days.
- User roles: `admin`, `customer`.

---

## Testing

### Unit Tests (pytest)

Tests run against an in-memory SQLite database — your PostgreSQL database is not affected.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run a specific test class
pytest tests/test_order.py::TestUpdateOrder -v

# Run with coverage report
pytest tests/ --cov=routes --cov-report=term-missing
```

Test coverage per route file:

| Test file | Covers |
|-----------|--------|
| `test_auth.py` | Login and JWT token generation |
| `test_user.py` | User registration and validation |
| `test_category.py` | Category CRUD with admin role checks |
| `test_product.py` | Product CRUD, validation, and soft deletion |
| `test_order.py` | Order creation, listing (customer/admin), status workflow, cancellation with restock, and soft deletion |

### Load Testing (Locust)

Load testing simulates concurrent users accessing the application.

```bash
# Start the Flask app first
flask run

# In another terminal, start Locust
locust -f locustfile.py --users 200 --spawn-rate 10
```

Open `http://localhost:8089` in the browser. Set the host to `http://localhost:5000` and start the test.

Two user scenarios are tested:
- **BrowsingUser** — Public users browsing and viewing products.
- **ShoppingUser** — Authenticated customers who login, browse, and place orders.

---

## Seeded Test Accounts

| Name | Email | Password | Role |
|------|-------|----------|------|
| John Alexander | john@email.com | John1234 | admin |
| Sarah Tan | sarah@email.com | Sarah1234 | customer |
| Michael Max | michael@email.com | Michael1234 | customer |
| Alonso Wirtz | alonso@email.com | Alonso1234 | customer |
| David Alten | david@email.com | David1234 | customer |

---

### Postman Documentation

Full API documentation with request/response examples:

https://documenter.getpostman.com/view/57333016/2sBYApzDBC

---

### Deployment

The deployed project is live and can be accesed at:

https://revoshop-flask.vercel.app/

> [!NOTE]  
> **Live Demo Status:** The production deployment on [Vercel](https://revoshop-flask.vercel.app/) reflects the stable release at commit [`05dc237`](https://github.com/Revou-FSSE-Jun26/module-2-jonathanch12/commit/05dc2379b12fad4fcdd35ef460c33d0bf8ecab12) (v1.0.0).  
> Recent commits on the `main` branch contain unreleased updates and work-in-progress features that are not yet deployed.

---

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)
