## Step 1: Create the Database

Before running the SQL scripts, you'll need to create an empty database named `revoshop_db`.

### Using DBeaver

1. Open **DBeaver** and connect to your PostgreSQL server.
2. In the **Database Navigator** (left sidebar), expand your PostgreSQL connection.
3. Right-click **Databases** and select **Create New Database**.
4. Enter the following database name:

```text
revoshop_db
```

5. Click **OK** to create the database.

You should now see `revoshop_db` listed under the **Databases** section.

> **Note:** If a database with the same name already exists, you can either delete it or choose a different name.

---

## Step 2: Open an SQL Editor

1. In the **Database Navigator**, select the `revoshop_db` database.
2. Right-click the database and choose **SQL Editor → New SQL Script**.
3. A new SQL editor tab will open.

This is where you'll run the SQL scripts included in this repository.

---

## Step 3: Create the Tables

1. Open the `schema.sql` file from this repository.
2. Copy all of its contents and paste them into the SQL editor.
3. Click the **Execute SQL Script** button or press **Ctrl + Enter** (Windows/Linux) or **⌘ + Enter** (macOS).

If the script runs successfully, DBeaver will display a success message, and the tables will be created in the `revoshop_db` database.

---

## Step 4: Insert Sample Data

1. Open the `seed.sql` file.
2. Copy its contents into a new SQL editor tab (or clear the current one).
3. Execute the script using the **Execute** button or **Ctrl + Enter**.

This will populate the database with sample users, categories, products, orders, and order items.

---

## Step 5: Run the Example Queries

Finally, open `queries.sql`, execute the statements, and review the results displayed in DBeaver's **Results** panel.

If you can see rows returned by the queries, your database has been set up successfully! 

---

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)