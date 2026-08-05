"""
Seed Data v4.4 — Rich seed data for demo and testing
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict

class SeedData:
    def __init__(self):
        self.sku_prefixes = ["ELEC", "MECH", "TEXT", "FOOD", "CHEM", "AUTO", "HOME", "SPORT"]
        self.categories = ["Electronics", "Mechanical", "Textiles", "Food", "Chemicals", "Automotive", "Home", "Sports"]
        self.zones = ["A", "B", "C", "D"]
        self.customer_names = ["Acme Corp", "Globex", "Soylent", "Initech", "Umbrella", "Stark Ind", "Wayne Ent", "Cyberdyne"]
        self.carriers = ["DHL", "FedEx", "UPS", "USPS", "Amazon"]

    def generate_inventory(self, count: int = 100) -> List[Dict]:
        items = []
        for i in range(count):
            prefix = random.choice(self.sku_prefixes)
            sku = f"{prefix}-{1000 + i}"
            zone = random.choice(self.zones)
            qty = random.randint(0, 500)
            items.append({
                "sku": sku,
                "name": f"Product {sku}",
                "location": f"{zone}-{random.randint(1, 50):02d}",
                "quantity": qty,
                "reserved": random.randint(0, qty),
                "reorder_point": random.randint(5, 20),
                "max_stock": random.randint(500, 2000),
                "unit_cost": round(random.uniform(1.0, 500.0), 2),
                "category": random.choice(self.categories),
                "zone": zone,
                "aisle": f"{zone}{random.randint(1, 10)}",
                "bin": f"{random.randint(1, 20):02d}"
            })
        return items

    def generate_orders(self, count: int = 50) -> List[Dict]:
        orders = []
        statuses = ["PENDING", "PICKING", "PACKED", "SHIPPED", "DELIVERED"]
        priorities = ["LOW", "NORMAL", "HIGH", "URGENT"]

        for i in range(count):
            created = datetime.now() - timedelta(hours=random.randint(1, 168))
            status = random.choice(statuses)
            orders.append({
                "order_id": f"ORD-{10000 + i}",
                "customer_id": f"CUST-{random.randint(100, 999)}",
                "customer_name": random.choice(self.customer_names),
                "status": status,
                "priority": random.choice(priorities),
                "total_items": random.randint(1, 20),
                "total_value": round(random.uniform(10.0, 5000.0), 2),
                "shipping_address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St, {random.choice(['NY', 'CA', 'TX', 'FL'])}",
                "created_at": created.isoformat(),
                "promised_date": (created + timedelta(days=random.randint(1, 5))).isoformat(),
                "carrier": random.choice(self.carriers) if status in ["SHIPPED", "DELIVERED"] else "",
                "tracking_number": f"TRK{random.randint(1000000000, 9999999999)}" if status in ["SHIPPED", "DELIVERED"] else ""
            })
        return orders

    def generate_order_items(self, order_id: str, count: int = None) -> List[Dict]:
        count = count or random.randint(1, 10)
        items = []
        for i in range(count):
            prefix = random.choice(self.sku_prefixes)
            items.append({
                "order_id": order_id,
                "sku": f"{prefix}-{random.randint(1000, 1100)}",
                "quantity": random.randint(1, 10),
                "picked_qty": 0,
                "packed_qty": 0,
                "unit_price": round(random.uniform(5.0, 200.0), 2)
            })
        return items

    def generate_users(self) -> List[Dict]:
        return [
            {"username": "admin", "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", "role": "admin", "email": "admin@warehouse.com"},
            {"username": "manager", "password_hash": "c7ad44cbad762a5da0a452f9e854fdc1e0e7a52a38015f23f3eab1d80b931dd472634dfac71cd34ebc35d16ab7fb8a90c81f975113d6c7538dc69dd8de9077ec", "role": "manager", "email": "manager@warehouse.com"},
            {"username": "operator", "password_hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae", "role": "operator", "email": "operator@warehouse.com"},
            {"username": "viewer", "password_hash": "04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb", "role": "viewer", "email": "viewer@warehouse.com"}
        ]

    def generate_pick_history(self, days: int = 30) -> List[Dict]:
        history = []
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            for _ in range(random.randint(50, 200)):
                prefix = random.choice(self.sku_prefixes)
                history.append({
                    "date": date.isoformat(),
                    "sku": f"{prefix}-{random.randint(1000, 1100)}",
                    "quantity": random.randint(1, 10),
                    "operator": random.choice(["Mike", "Sarah", "John", "Lisa", "Tom"]),
                    "zone": random.choice(self.zones),
                    "duration_seconds": random.randint(30, 300),
                    "accuracy": random.random() > 0.02
                })
        return history

    def seed_database(self, db):
        """Seed a Database instance with demo data."""
        for user in self.generate_users():
            db.create_user(user["username"], user["password_hash"], user["role"], user["email"])

        for item in self.generate_inventory(100):
            db.execute(
                "INSERT OR IGNORE INTO inventory (sku, name, location, quantity, reserved, reorder_point, max_stock, unit_cost, category, zone, aisle, bin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item["sku"], item["name"], item["location"], item["quantity"], item["reserved"],
                 item["reorder_point"], item["max_stock"], item["unit_cost"], item["category"],
                 item["zone"], item["aisle"], item["bin"])
            )

        for order in self.generate_orders(50):
            db.execute(
                "INSERT OR IGNORE INTO orders (order_id, customer_id, status, priority, total_items, total_value, shipping_address, created_at, promised_date, carrier, tracking_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (order["order_id"], order["customer_id"], order["status"], order["priority"],
                 order["total_items"], order["total_value"], order["shipping_address"],
                 order["created_at"], order["promised_date"], order["carrier"], order["tracking_number"])
            )
            for item in self.generate_order_items(order["order_id"]):
                db.execute(
                    "INSERT INTO order_items (order_id, sku, quantity, picked_qty, packed_qty, unit_price) VALUES (?, ?, ?, ?, ?, ?)",
                    (item["order_id"], item["sku"], item["quantity"], item["picked_qty"],
                     item["packed_qty"], item["unit_price"])
                )

        return {"users": 4, "inventory": 100, "orders": 50}
