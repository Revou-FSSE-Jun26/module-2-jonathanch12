# KINETIC — A Simple e-Commerce Backend [IN DEVELOPMENT]

KINETIC is a backend API for an online retail store, built with Flask and PostgreSQL. It provides RESTful endpoints for managing users, products, product images, categories, orders, and payments, with JWT-based authentication and role-based access control (admin/customer). Product images are stored on Cloudinary, and payments are processed through the Midtrans payment gateway.

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
| `orders` | Orders placed by users with soft deletion (total_amount, status, customer_name, customer_email, customer_phone, customer_address, is_deleted). The `customer_*` columns are a snapshot of the customer's details at checkout |
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
│   ├── auth.py                                 # Login/logout (JWT cookie issuing) and access-token refresh
│   ├── product.py                              # Product CRUD (admin-protected)
│   ├── image.py                                # Product image CRUD via Cloudinary (admin-protected writes, public reads)
│   ├── category.py                             # Category CRUD (admin-protected)
│   ├── order.py                                # Order creation and management
│   └── payment.py                              # Payment creation, Midtrans webhook, and payment reads
├── tests/
│   ├── __init__.py                             # Marks tests as a package
│   ├── conftest.py                             # Pytest fixtures (app, client, tokens)
│   ├── _helpers.py                             # auth() helper: sets the JWT cookie + CSRF header on the test client
│   ├── test_auth.py                            # Login, refresh, and logout route tests
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
JWT_COOKIE_SECURE="true"
```

`FRONTEND_ORIGINS` is a comma-separated list of origins allowed by CORS (the front-end app runs on a separate origin). Include every origin the front end is served from, for example `http://localhost:3000,https://your-frontend.vercel.app`. If unset, it defaults to `http://localhost:3000`.

`JWT_COOKIE_SECURE` controls whether the JWT cookies are marked `Secure` (HTTPS-only). It defaults to `true` and should stay `true` in any deployed (HTTPS) environment. Set it to `false` only for plain-HTTP local development — but because the cookies use `SameSite=None`, browsers still require `Secure`, so cross-origin browser testing should be done over HTTPS.

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

## Running over HTTPS (Local Development)

The API issues its JWT cookies with `SameSite=None` and `Secure`. Browsers reject a `SameSite=None` cookie that is not also `Secure`, so cross-origin browser testing against the API needs HTTPS even locally. [mkcert](https://github.com/FiloSottile/mkcert) issues a locally-trusted certificate, so the browser accepts `https://127.0.0.1:5000` with no warnings.

> This is a **local development** concern only. In production (e.g. Vercel) HTTPS is terminated by the platform — you do not use mkcert, certificate files, or `flask run` there.

### 1. Install mkcert (one-time, machine level)

mkcert is a standalone tool, **not** a Python package — it does not go in the virtual environment or `requirements-localdev.txt`.

```powershell
winget install FiloSottile.mkcert
```

(When winget asks you to accept the source agreements, answer **Yes**.) Alternatively, download the Windows binary from the [mkcert releases page](https://github.com/FiloSottile/mkcert/releases), rename it to `mkcert.exe`, and place it on your `PATH`.

### 2. Trust the local CA (one-time, machine level)

```powershell
mkcert -install
```

### 3. Generate the certificate for the project

Run this from the project's `certs/` folder so the files land there (they are git-ignored and never committed):

```powershell
cd certs
mkcert localhost 127.0.0.1
cd ..
```

This produces `localhost+1.pem` (certificate) and `localhost+1-key.pem` (key) inside `certs/`.

### 4. Run the app over HTTPS

```powershell
python run_local.py
```

`run_local.py` auto-detects the mkcert files in `certs/` and starts the dev server with TLS. The app is then available at **`https://127.0.0.1:5000/`**. If the certificate is missing, the script prints the setup steps and exits.

With HTTPS working locally you can keep `JWT_COOKIE_SECURE="true"` in `.env` so local behaviour matches production. Plain HTTP via `flask run --debug` still works if you prefer it (set `JWT_COOKIE_SECURE="false"` in that case).

### Uninstalling mkcert (restore the machine to its original state)

> [!IMPORTANT]
> Do the steps **in order**. `mkcert -install` added a local Certificate Authority to your system (and browser) trust stores. Deleting the `mkcert` binary alone does **not** remove that CA — you must run `mkcert -uninstall` *before* removing the binary, otherwise the trusted CA is left behind and has to be deleted manually.

#### 1. Untrust the local CA

Run this **while mkcert is still installed**. It undoes `mkcert -install`, removing the mkcert root CA from the Windows (and Firefox/NSS, if present) trust stores. A Windows security dialog may appear — confirm it.

```powershell
mkcert -uninstall
```

On success it prints:

```
The local CA is now uninstalled from the system trust store(s)! 👋
```

> [!NOTE]
> `mkcert -uninstall` only **untrusts** the CA — it does *not* delete anything. The mkcert binary, the root CA files in `%LOCALAPPDATA%\mkcert`, and your project's `certs/*.pem` all stay on disk; they are simply no longer trusted. After this step, loading `https://127.0.0.1:5000` will show the "not private" warning again. The remaining steps below are what actually remove the files. (If you only wanted to stop trusting mkcert and plan to keep using it later, you can stop here and re-run `mkcert -install` to re-trust it — no need to regenerate the certificate.)

#### 2. Uninstall the mkcert binary

If you installed it with winget:

```powershell
winget uninstall FiloSottile.mkcert
```

If you installed it by downloading the binary manually, just delete the `mkcert.exe` file (and remove its folder from your `PATH` if you added one).

#### 3. Delete the generated CA files

`mkcert -uninstall` removes the CA from the trust stores but leaves the generated root CA files on disk. Delete the CA root folder to fully clean up:

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\mkcert"
```

#### 4. Delete the project certificate files (optional)

These are already git-ignored, so they only live on your machine. Remove them if you no longer want local HTTPS:

```powershell
Remove-Item ".\certs\localhost+1.pem", ".\certs\localhost+1-key.pem"
```

After these steps, the machine is back to its original state: no mkcert binary, no trusted local CA, and no leftover certificate files. (The `certs/.gitkeep` placeholder stays so the folder remains in the repo.)

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
| POST | `/auth/login` | Login (sets JWT access and refresh tokens as HttpOnly cookies) |
| POST | `/auth/refresh` | Exchange the refresh cookie for a new access-token cookie |
| POST | `/auth/logout` | Clear the JWT and CSRF cookies |
| POST | `/users/` | Register a new user |
| GET | `/users` | View user's personal data |
| PUT | `/users` | Update user's personal data (name, password, phone, address) |

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
| POST | `/orders/` | Place a new order (customer details are copied from your profile) |
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

### Customer Details on Orders

When a customer places an order (`POST /orders/`), the API copies their `name`, `email`, `phone`, and `address` from the `users` table into the order's `customer_name`, `customer_email`, `customer_phone`, and `customer_address` columns. The client does not send these fields; they always come from the authenticated user's profile.

These values are a snapshot taken at checkout. If the customer later updates their profile via `PUT /users`, existing orders keep the details they were placed with, so order history stays accurate. The four fields are returned in every order response:

```json
{
  "id": 1,
  "user_id": 2,
  "total_amount": 398000.0,
  "status": "pending",
  "order_items": [{ "product_id": 1, "quantity": 2, "unit_price": 199000.0 }],
  "customer_name": "Sarah Tan",
  "customer_email": "sarah@example.com",
  "customer_phone": "081234567890",
  "customer_address": "Jl. Sudirman No. 1, Jakarta",
  "created_at": "2026-10-30T10:00:00"
}
```

If the user behind the token no longer exists, `POST /orders/` returns `404` with `"User not found"` and no order is created.

---

## Image Storage (Cloudinary)

Product images are stored on [Cloudinary](https://cloudinary.com/) rather than in the database or on the application server. The database keeps only the delivered `url` (Cloudinary `secure_url`) and the `public_id` needed to manage the asset later. The SDK is configured once in the app factory (`create_app`) from the `CLOUDINARY_*` environment variables, and the routes talk to it through a thin wrapper in `helper/cloudinary_service.py`.

### How it works

1. **Upload (`POST /products/<product_id>/images/`).** An admin can send either a file upload (`multipart/form-data`, field `file`, one or many) or a JSON body with a remote image URL — a single `{"url": "..."}` object or a list of them. Each source is uploaded to Cloudinary under a per-product folder (`products/<product_id>`), and only the returned `secure_url` and `public_id` are saved to the database.
2. **Replace (`PUT /products/<product_id>/images/<image_id>`).** Accepts exactly one new file or URL. The existing Cloudinary asset is overwritten in place (the same `public_id` is reused, so the old file is replaced and the CDN cache invalidated), and the stored `url` is refreshed.
3. **Delete (`DELETE /products/<product_id>/images/<image_id>`).** The asset is removed from Cloudinary first. Only after Cloudinary confirms the deletion is the database record soft-deleted — if the Cloudinary call fails, the whole request fails and the record is left untouched, so the database never claims an image is gone while it still lives on Cloudinary.

### Request examples

These are admin-only, state-changing requests, so they send the JWT cookies (set at login) and the CSRF token in the `X-CSRF-TOKEN` header.

Upload files:

```bash
curl -X POST https://api.example.com/products/1/images/ \
  --cookie "access_token_cookie=<admin_access_jwt>; csrf_access_token=<csrf>" \
  -H "X-CSRF-TOKEN: <csrf>" \
  -F "file=@./mouse-front.jpg" \
  -F "file=@./mouse-side.jpg"
```

Upload by remote URL(s):

```bash
curl -X POST https://api.example.com/products/1/images/ \
  --cookie "access_token_cookie=<admin_access_jwt>; csrf_access_token=<csrf>" \
  -H "X-CSRF-TOKEN: <csrf>" \
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
2. **A payment row is stored** with status `pending` and a globally unique `midtrans_order_id` in the form `order-<order_id>-<payment_id>-ktic` (for example, `order-12-34-ktic`). This per-attempt id is required because Midtrans rejects reused order ids, so it is what makes retries possible. The `-ktic` suffix marks the transaction as coming from this API version, so payments can be told apart on the Midtrans dashboard.
3. **The response returns a Snap `token` and `redirect_url`** that the frontend uses to open the Midtrans payment page.
4. **Midtrans calls the webhook** (`POST /payments/notification`) whenever the transaction status changes. The notification is verified server-side via the Midtrans SDK (which re-fetches the authoritative status) rather than trusting the request body. The matching payment row is then updated with the latest `status`, `method`, `transaction_id`, and `signature_key`.
5. **The order advances automatically.** When a payment reaches a paid state (`settlement`, or `capture` with `fraud_status = accept`), a still-`pending` order is moved to `processing`. Other statuses leave the order untouched so the customer can retry.

### Payment status values

The `status` column stores the raw Midtrans `transaction_status` for accurate reconciliation: `pending`, `settlement`, `capture`, `deny`, `cancel`, `expire`, `refund`, `partial_refund`, `authorize`.

> [!IMPORTANT]
> Payment status is only ever updated from the Midtrans HTTP notification (or a server-side status check), never from frontend callbacks. The Midtrans server key is loaded from the environment and never exposed to clients.

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication, delivered as **HttpOnly cookies** rather than in the response body. Tokens carry a `role` claim (`admin` or `customer`) that drives role-based access control.

### Why HttpOnly cookies

Because the cookies are `HttpOnly`, JavaScript cannot read them (`document.cookie` won't expose them), which protects the token against theft via XSS. The frontend never handles the token directly — the browser stores it and attaches it automatically. The tradeoff is CSRF exposure (the browser sends the cookie on any request to the API), which is why CSRF protection is enabled (see below).

Since the frontend and backend run on separate origins, the cookies are issued with `SameSite=None` and `Secure`, so **HTTPS is required** in any deployed environment. For plain-HTTP local development you can set `JWT_COOKIE_SECURE=false` in `.env`, but note that browsers reject a `SameSite=None` cookie without `Secure`, so cross-origin browser testing is best done over HTTPS.

### Sending requests from the frontend

The frontend must opt into sending cookies on every request — it does **not** set an `Authorization` header:

```js
// fetch
fetch("https://api.example.com/orders/", { credentials: "include" });

// axios
axios.get("/orders/", { withCredentials: true });
```

### CSRF protection

Cookie auth is paired with double-submit CSRF protection. On login (and refresh), the server also sets **readable** `csrf_access_token` and `csrf_refresh_token` cookies. On every state-changing request (`POST`/`PUT`/`DELETE`) to a protected endpoint, the frontend must read the relevant CSRF cookie and send its value back in the `X-CSRF-TOKEN` header:

```js
function getCookie(name) {
  return document.cookie.split("; ").find(c => c.startsWith(name + "="))?.split("=")[1];
}

fetch("https://api.example.com/orders/", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-TOKEN": getCookie("csrf_access_token"),
  },
  body: JSON.stringify({ order_items: [{ product_id: 1, quantity: 2 }] }),
});
```

`GET` requests are not CSRF-checked. A protected state-changing request without the matching CSRF header is rejected with `401`.

### Login

`POST /auth/login` with an email and password sets the JWT cookies and returns only non-sensitive data in the body:

```json
{
  "message": "Login successful",
  "name": "Sarah Tan",
  "expires_in": 3600,
  "status": "ok"
}
```

On success the server sends four cookies via `Set-Cookie`:

- **`access_token_cookie`** (HttpOnly) — short-lived access token (1 hour).
- **`refresh_token_cookie`** (HttpOnly) — long-lived refresh token (7 days), scoped to `/auth/refresh`.
- **`csrf_access_token`** / **`csrf_refresh_token`** (readable) — CSRF tokens the frontend echoes back in `X-CSRF-TOKEN`.

### Refreshing the access token

When the access token expires, call `POST /auth/refresh`. The refresh cookie is sent automatically by the browser (no `Authorization` header), and the request must include the refresh CSRF token in the `X-CSRF-TOKEN` header. The response sets a new `access_token_cookie` that preserves the user's `role` claim.

```bash
curl -X POST https://api.example.com/auth/refresh \
  --cookie "refresh_token_cookie=<refresh_jwt>; csrf_refresh_token=<csrf>" \
  -H "X-CSRF-TOKEN: <csrf>"
```

```json
{
  "expires_in": 3600,
  "status": "ok"
}
```

A missing/invalid/expired refresh cookie or a missing/invalid CSRF header returns `401`; sending an access token instead of a refresh token returns `422`.

### Logout

`POST /auth/logout` clears the JWT and CSRF cookies by unsetting them (re-sending them empty with an immediate expiry). Because the token lives in an HttpOnly cookie the frontend cannot delete itself, the server must do it. The endpoint requires no token, so a client can always end its session.

```json
{
  "message": "Logout successful",
  "status": "ok"
}
```

JWTs are otherwise stateless and are not tracked server-side, so an already-issued token stays technically valid until it expires — logout clears the browser's cookies rather than revoking the token. True server-side revocation would require a token blocklist, which is not currently implemented.

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

Protected-route tests authenticate via the `auth()` helper in `tests/_helpers.py`, which sets the JWT access cookie on the test client and supplies the `X-CSRF-TOKEN` header (mirroring how a browser behaves) instead of an `Authorization` header.

| Test file | Covers |
|-----------|--------|
| `test_auth.py` | Login (sets JWT + CSRF cookies), token refresh (cookie + CSRF header), logout (clears cookies) |
| `test_user.py` | User registration and validation |
| `test_category.py` | Category CRUD with admin role checks |
| `test_product.py` | Product CRUD, validation, and soft deletion |
| `test_image.py` | Product image CRUD via Cloudinary (file and URL uploads, in-place replace, delete), validation, admin role checks, soft deletion, and Cloudinary failure handling (mocked SDK) |
| `test_order.py` | Order creation (including customer details copied from the user's profile, the snapshot staying unchanged after a profile update, and `404` for a missing user), listing (customer/admin), status workflow, cancellation with restock, and soft deletion |
| `test_payment.py` | Payment creation (own-order enforcement, `-ktic` suffixed `midtrans_order_id` stored and sent to Snap), access control (public/admin/customer), reads, and the Midtrans webhook (mocked SDK) |

Orders created directly in tests (outside `POST /orders/`) go through small helpers (`_new_order()` in `test_order.py`, `_make_order()` in `test_payment.py`). They fill in the required `customer_*` columns from the owning user, the same way the route does.

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

### Frontend Repository

The KINETIC Next.js frontend side that runs on this Flask REST API lives in a separate repository: 

https://github.com/jonathanch12/kinetic-fe

---

### Deployment

The deployed project is live and can be accesed at:

https://kinetic-be.vercel.app/

> [!NOTE]  
> **Live Demo Status:** The production deployment on [Vercel](https://kinetic-be.vercel.app/) reflects the stable release at commit [`8f54207`](https://github.com/jonathanch12/kinetic-be/commit/8f542074dfb07630f4c946ac1106c017e55e6e9d). 
> Recent commits on the `main` branch contain unreleased updates and work-in-progress features that are not yet deployed.

---

Origin: This project was initially named as `RevoShop`, but a renaming was held to keep it aligned with the dummy products catalogue. The current name of the project is `KINETIC`.

---

Disclaimer: KINETIC is a portfolio project created for educational and demonstration purposes only. It is not an actual commercial store, and no items are available for real purchase. All trademarks, logos, and product imagery belong to their respective owners.
