# RevoShop — A Simple e-Commerce Backend [IN DEVELOPMENT]

RevoShop is a backend API for an online retail store, built with Flask and PostgreSQL. It provides RESTful endpoints for managing users, products, categories, and orders, including a many-to-many relationship between orders and products through an association table.

---

## Project Goals

- Build a Flask application connected to a PostgreSQL database via SQLAlchemy.
- Define models that mirror the database schema (users, products, categories, orders, order_items).
- Implement user registration and retrieval routes.
- Implement product listing and retrieval routes.
- Manage schema changes using Flask-Migrate (Alembic).
- Demonstrate a many-to-many relationship between orders and products.

---

## Tech Stack

- **Language:** Python 3
- **Framework:** Flask
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (via Flask-SQLAlchemy)
- **Migrations:** Flask-Migrate (Alembic)
- **Password Hashing:** bcrypt

---

## Database

The application uses a PostgreSQL database named `revoshop_db` with the following tables:

| Table | Description |
|-------|-------------|
| `users` | Stores registered users (name, email, password, address, role) |
| `categories` | Product categories (name, description) |
| `products` | Products linked to a category (name, description, price, stock) |
| `orders` | Orders placed by users (total_amount, status) |
| `order_items` | Association table linking orders to products (quantity, unit_price) |

### ERD (Entity Relationship Diagram)

![ERD Diagram](database/Schema%20Diagram%20(ERD_Screenshot_DBeaver).png)

---

## Folder Structure

```
module-2-jonathanch12/
├── database/
│   ├── schema.sql                              # Table creation scripts
│   ├── seed.sql                                # Sample data
│   ├── queries.sql                             # Example queries
│   └── Schema Diagram (ERD_Screenshot_DBeaver).png  # ERD screenshot
├── migrations/
│   ├── versions/                               # Migration history
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── postman_screenshots/                        # Screenshots documentation for Postman testing
├── .env                                        # Environment variables (not committed)
├── .gitignore
├── app.py                                      # Flask app setup and configuration
├── models.py                                   # SQLAlchemy models
├── routes.py                                   # API route definitions
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

Follow the steps below using DBeaver (or any PostgreSQL client):

1. Create a new database named `revoshop_db`.
2. Open `database/schema.sql` and execute it to create the tables.
3. Open `database/seed.sql` and execute it to insert sample data.
4. (Optional) Run `database/queries.sql` to verify the data.

### 5. Configure the `.env` File

Create a `.env` file in the project root with the following variable:

```
DATABASE_URL=postgresql://username:password@localhost/revoshop_db
```

Replace `username` and `password` with your PostgreSQL credentials.

> **Note:** The `.env` file is included in `.gitignore` and will not be committed to the repository. This keeps your database credentials secure.

### 6. Run Migrations

```bash
flask db upgrade
```

This applies all existing migrations (including the `role` column addition to `users`).

### 7. Run the Application

```bash
flask run --debug
```

The app will be available at `http://127.0.0.1:5000`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Database connection test |
| GET | `/products` | List all products |
| GET | `/products/<id>` | Get a product by ID |
| POST | `/users/register` | Register a new user |
| GET | `/users/<id>` | Get a user by ID |

### Postman Documentation

Full API documentation with request/response examples:

https://documenter.getpostman.com/view/57333016/2sBYApzDBC

---

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)
