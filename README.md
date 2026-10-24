# RevoShop — A Simple e-Commerce Backend [IN DEVELOPMENT]

RevoShop is a backend API for an online retail store, built with Flask and PostgreSQL. It provides RESTful endpoints for managing users, products, product images, categories, orders, and payments, with JWT-based authentication and role-based access control (admin/customer). Product images are stored on Cloudinary, and payments are processed through the Midtrans payment gateway.

---

## Project Goals

- Build a Flask application using the application factory pattern, connected to PostgreSQL via SQLAlchemy.
- Define models that mirror the database schema (users, products, images, categories, orders, order_items, payments).
- Implement JWT authentication with role-based access control (admin, customer).
- Implement CRUD routes for users, products, product images, categories, and orders.
- Integrate Cloudinary for product image storage, so the database holds only the delivered image URL and its Cloudinary `public_id`.
- Integrate the Midtrans payment gateway, with a webhook that keeps payment status in sync.
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
- **Image Storage:** Cloudinary (via the `cloudinary` Python SDK)
- **Payment Gateway:** Midtrans (via the `midtransclient` Python SDK)
- **Testing:** pytest (unit tests), Locust (load/performance testing)

---

## Database

The application uses a PostgreSQL database with the following tables:

| Table | Description |
|-------|-------------|
| `users` | Registered users (name, email, phone, password, address, role) |
| `categories` | Product categories with soft deletion (name, description, is_deleted) |
| `products` | Products linked to a category with soft deletion (name, description, price, stock, is_deleted) |
| `images` | Product images linked to a product with soft deletion (product_id, url, public_id, is_deleted). `url` and `public_id` reference the asset stored on Cloudinary |
| `orders` | Orders placed by users with soft deletion (total_amount, status, is_deleted) |
| `order_items` | Association table linking orders to products (quantity, unit_price) |
| `payments` | Payment attempts for an order via Midtrans (order_id, amount, method, status, transaction_id, midtrans_order_id, signature_key) |

### ERD (Entity Relationship Diagram)

![ERD Diagram](database/Schema%20Diagram.png)

---

## Folder Structure

```
module-2-jonathanch12/
├── database/
│   ├── schema.sql                              # Table creation scripts
│   ├── seed.sql                                # Sample data (SQL)
│   ├── queries.sql                             # Example queries
│   └── Schema Diagram.png                      # Schema diagram (ERD)
├── helper/
│   └── seed.py                                 # Python database seeder for users, categories, and products
│   └── seed_order.py                           # Python database seeder for orders
│   └── cloudinary_service.py                   # Cloudinary upload/destroy wrapper used by the image routes
├── migrations/
│   ├── versions/                               # Migration history
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── routes/
│   ├── __init__.py                             # Blueprint exports
│   ├── main.py                                 # Home/health check route
│   ├── user.py                                 # User registration and retrieval
│   ├── auth.py                                 # Login (JWT token generation) and access-token refresh
│   ├── product.py                              # Product CRUD (admin-protected)
│   ├── image.py                                # Product image CRUD via Cloudinary (admin-protected writes, public reads)
│   ├── category.py                             # Category CRUD (admin-protected)
│   ├── order.py                                # Order creation and management
│   └── payment.py                              # Payment creation, Midtrans webhook, and payment reads
├── tests/
│   ├── conftest.py                             # Pytest fixtures (app, client, tokens)
│   ├── test_auth.py                            # Login route tests
│   ├── test_user.py                            # Registration route tests
│   ├── test_category.py                        # Category route tests
│   ├── test_product.py                         # Product route tests
│   ├── test_image.py                           # Product image route tests
│   ├── test_order.py                           # Order route tests
│   └── test_payment.py                         # Payment route tests
├── testing_screenshots/                        # Pytest and Locust testing screenshots
├── .env                                        # Environment variables (not committed)
├── .env.example                                # Environment variable template
├── .gitignore
├── app.py                                      # Flask app factory (create_app)
├── models/                                     # SQLAlchemy models (one file per model)
│   ├── __init__.py                             # Re-exports all models + order_items table
│   ├── category.py                             # Category model
│   ├── order.py                                # order_items association table + Order model
│   ├── product.py                              # Product model
│   ├── image.py                                # Product image model
│   ├── payment.py                              # Payment model
│   └── user.py                                 # User model
├── locustfile.py                               # Load testing configuration
├── openapi.yaml                                # API interaction documentation
├── requirements.txt                            # Python dependencies (For deployment)
├── requirements-localdev.txt                   # Python dependencies (For local development)
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3 installed
- PostgreSQL installed and running
- DBeaver (or any PostgreSQL client) for database management
- A [Cloudinary](https://cloudinary.com/) account (free tier is sufficient) for product image storage

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
pip install -r requirements-localdev.txt
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
MIDTRANS_SERVER_KEY="your-midtrans-server-key"
MIDTRANS_CLIENT_KEY="your-midtrans-client-key"
MIDTRANS_IS_PRODUCTION="false"
CLOUDINARY_CLOUD_NAME="your-cloudinary-cloud-name"
CLOUDINARY_API_KEY="your-cloudinary-api-key"
CLOUDINARY_API_SECRET="your-cloudinary-api-secret"
FRONTEND_ORIGINS="http://localhost:3000"
```

`FRONTEND_ORIGINS` is a comma-separated list of origins allowed by CORS (the front-end app runs on a separate origin). Include every origin the front end is served from, for example `http://localhost:3000,https://your-frontend.vercel.app`. If unset, it defaults to `http://localhost:3000`.

Generate the JWT secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The Midtrans server and client keys are available from the [Midtrans Dashboard](https://dashboard.midtrans.com/) (Settings → Access Keys). Leave `MIDTRANS_IS_PRODUCTION` as `false` to use the sandbox environment.

The Cloudinary cloud name, API key, and API secret are available from the [Cloudinary Console](https://console.cloudinary.com/) (Dashboard → Product Environment Credentials). These are required for adding, replacing, and deleting product images.

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
| GET | `/products/<product_id>/images/` | List all images for a product |
| GET | `/categories/` | List all categories |
| GET | `/categories/<id>` | Get category by ID (includes products) |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login (returns JWT access and refresh tokens) |
| POST | `/auth/refresh` | Exchange a refresh token for a new access token |
| POST | `/users/` | Register a new user |
| GET | `/users/<id>` | Get user by ID |

### Admin-Protected Routes (requires admin JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/products/` | Create a product |
| PUT | `/products/<id>` | Update a product |
| DELETE | `/products/<id>` | Soft-delete a product |
| POST | `/products/<product_id>/images/` | Upload one or more images to Cloudinary and attach them to a product (accepts file uploads and/or remote URLs) |
| PUT | `/products/<product_id>/images/<image_id>` | Replace a product image on Cloudinary (overwrites the old asset in place) |
| DELETE | `/products/<product_id>/images/<image_id>` | Delete a product image from Cloudinary and soft-delete the record |
| POST | `/categories/` | Create a category |
| PUT | `/categories/<id>` | Update a category |
| DELETE | `/categories/<id>` | Soft-delete a category |
| GET | `/orders/<id>` | View a specific order |
| DELETE | `/orders/<id>` | Soft-delete an order (blocked if processing/delivering) |

### Customer-Protected Routes (requires customer JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/orders/` | Place a new order |
| POST | `/payments` | Create a Midtrans payment for one of your own pending orders |

### Shared Order Routes (Customer and Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | List orders (customer: own orders only, admin: all orders) |
| PUT | `/orders/<id>` | Update order status (admin: advance the flow; customer: cancel own pending order) |

### Shared Payment Routes (Customer and Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payments/<id>` | View a payment (customer: own payments only, admin: any payment) |
| GET | `/orders/<order_id>/payments` | List all payment attempts for an order (customer: own order only, admin: any order) |

### Webhook (Public — called by Midtrans)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments/notification` | Midtrans HTTP notification. Verified server-side; updates payment status and advances the order when paid. Not for manual use. |

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

When an order is cancelled (by either role), the reserved product stock is automatically restored.

---

## Image Storage (Cloudinary)

Product images are stored on [Cloudinary](https://cloudinary.com/) rather than in the database or on the application server. The database keeps only the delivered `url` (Cloudinary `secure_url`) and the `public_id` needed to manage the asset later. The SDK is configured once in the app factory (`create_app`) from the `CLOUDINARY_*` environment variables, and the routes talk to it through a thin wrapper in `helper/cloudinary_service.py`.

### How it works

1. **Upload (`POST /products/<product_id>/images/`).** An admin can send either a file upload (`multipart/form-data`, field `file`, one or many) or a JSON body with a remote image URL — a single `{"url": "..."}` object or a list of them. Each source is uploaded to Cloudinary under a per-product folder (`products/<product_id>`), and only the returned `secure_url` and `public_id` are saved to the database.
2. **Replace (`PUT /products/<product_id>/images/<image_id>`).** Accepts exactly one new file or URL. The existing Cloudinary asset is overwritten in place (the same `public_id` is reused, so the old file is replaced and the CDN cache invalidated), and the stored `url` is refreshed.
3. **Delete (`DELETE /products/<product_id>/images/<image_id>`).** The asset is removed from Cloudinary first. Only after Cloudinary confirms the deletion is the database record soft-deleted — if the Cloudinary call fails, the whole request fails and the record is left untouched, so the database never claims an image is gone while it still lives on Cloudinary.

### Request examples

Upload files:

```bash
curl -X POST http://127.0.0.1:5000/products/1/images/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -F "file=@./mouse-front.jpg" \
  -F "file=@./mouse-side.jpg"
```

Upload by remote URL(s):

```bash
curl -X POST http://127.0.0.1:5000/products/1/images/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '[{"url": "https://example.com/mouse-front.jpg"}, {"url": "https://example.com/mouse-side.jpg"}]'
```

> [!IMPORTANT]
> Cloudinary credentials are loaded from the environment and never exposed to clients. On failure, upload/replace return `502` and roll back the database (removing any assets uploaded earlier in the same batch), and delete returns `502` without soft-deleting, so Cloudinary and the database stay consistent.

---

## Payment Flow (Midtrans)

Payments are handled through the [Midtrans](https://midtrans.com/) payment gateway using the Snap API. Each order can have multiple payment attempts (a history), which supports retries after a failed, denied, or expired payment.

### How it works

1. **Create a payment.** A customer calls `POST /payments` with the `order_id` of one of their own `pending` orders. The payment amount is always taken from the order's `total_amount` (never from the client, to prevent tampering).
2. **A payment row is stored** with status `pending` and a globally unique `midtrans_order_id` in the form `order-<order_id>-<payment_id>`. This per-attempt id is required because Midtrans rejects reused order ids, so it is what makes retries possible.
3. **The response returns a Snap `token` and `redirect_url`** that the frontend uses to open the Midtrans payment page.
4. **Midtrans calls the webhook** (`POST /payments/notification`) whenever the transaction status changes. The notification is verified server-side via the Midtrans SDK (which re-fetches the authoritative status) rather than trusting the request body. The matching payment row is then updated with the latest `status`, `method`, `transaction_id`, and `signature_key`.
5. **The order advances automatically.** When a payment reaches a paid state (`settlement`, or `capture` with `fraud_status = accept`), a still-`pending` order is moved to `processing`. Other statuses leave the order untouched so the customer can retry.

### Payment status values

The `status` column stores the raw Midtrans `transaction_status` for accurate reconciliation: `pending`, `settlement`, `capture`, `deny`, `cancel`, `expire`, `refund`, `partial_refund`, `authorize`.

> [!IMPORTANT]
> Payment status is only ever updated from the Midtrans HTTP notification (or a server-side status check), never from frontend callbacks. The Midtrans server key is loaded from the environment and never exposed to clients.

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Tokens carry a `role` claim (`admin` or `customer`) that drives role-based access control.

### Login

`POST /auth/login` with an email and password returns two tokens:

- **Access token** — short-lived (1 hour), sent with every protected request.
- **Refresh token** — long-lived (7 days), used only to obtain a new access token.

```json
{
  "message": "Login successful",
  "name": "Sarah Tan",
  "access_token": "<jwt_access_token>",
  "refresh_token": "<jwt_refresh_token>",
  "status": "ok"
}
```

Include the access token in the `Authorization` header on protected requests:

```
Authorization: Bearer <access_token>
```

### Refreshing the access token

When the access token expires, call `POST /auth/refresh` with the **refresh token** (not the access token) in the `Authorization` header to get a new access token — no need to re-send credentials. The new access token preserves the user's `role` claim.

```bash
curl -X POST http://127.0.0.1:5000/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

```json
{
  "access_token": "<new_jwt_access_token>",
  "status": "ok"
}
```

Sending an access token to this endpoint (instead of a refresh token) is rejected with `422`; a missing, expired, or invalid token returns `401`.

### Logout

There is no logout endpoint. JWTs are stateless and are not tracked server-side, so the server cannot invalidate a token on demand. Logout is handled on the client by discarding the stored access and refresh tokens. Any token that was already issued remains valid until it expires (access token up to 1 hour, refresh token up to 7 days). True server-side revocation would require a token blocklist, which is not currently implemented.

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
| `test_image.py` | Product image CRUD via Cloudinary (file and URL uploads, in-place replace, delete), validation, admin role checks, soft deletion, and Cloudinary failure handling (mocked SDK) |
| `test_order.py` | Order creation, listing (customer/admin), status workflow, cancellation with restock, and soft deletion |
| `test_payment.py` | Payment creation (own-order enforcement), access control (public/admin/customer), reads, and the Midtrans webhook |

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

### Postman Documentation

Full API documentation with request/response examples:

https://documenter.getpostman.com/view/57333016/2sBYHSzgiz

---

### Deployment

The deployed project is live and can be accesed at:

https://revoshop-flask.vercel.app/

> [!NOTE]  
> **Live Demo Status:** The production deployment on [Vercel](https://revoshop-flask.vercel.app/) reflects the stable release at commit [`05dc237`](https://github.com/Revou-FSSE-Jun26/module-2-jonathanch12/commit/05dc2379b12fad4fcdd35ef460c33d0bf8ecab12) (v1.0.0).  
> Recent commits on the `main` branch contain unreleased updates and work-in-progress features that are not yet deployed.

---

Disclaimer: RevoShop is a portfolio project created for educational and demonstration purposes only. It is not an actual commercial store, and no items are available for real purchase. All trademarks, logos, and product imagery belong to their respective owners.
