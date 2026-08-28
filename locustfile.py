from locust import HttpUser, task, between
import random


class BrowsingUser(HttpUser):
    """
    Scenario 1: Users browse products without logging in.
    They view all products and view details of a random product.
    """
    wait_time = between(1, 3)

    @task(3)
    def get_all_products(self):
        self.client.get("/products/", name="/products")

    @task(2)
    def get_product_by_id(self):
        product_id = random.randint(1, 10)
        self.client.get(f"/products/{product_id}", name="/products/[id]")


class ShoppingUser(HttpUser):
    """
    Scenario 2: Users login, browse products, view product details,
    and create an order.
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Login to get JWT access token."""
        response = self.client.post("/auth/login", json={
            "email": "sarah@email.com",
            "password": "Sarah1234"
        })
        data = response.json()
        self.token = data.get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def browse_products(self):
        self.client.get("/products/", name="/products")

    @task(2)
    def view_product_details(self):
        product_id = random.randint(1, 10)
        self.client.get(f"/products/{product_id}", name="/products/[id]")

    @task(1)
    def create_order(self):
        product_id = random.randint(1, 10)
        quantity = random.randint(1, 3)
        self.client.post("/orders/", json={
            "order_items": [
                {"product_id": product_id, "quantity": quantity}
            ]
        }, headers=self.headers, name="/orders")
