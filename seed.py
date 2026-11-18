"""Fill the database with made-up sample data (no real customers or prices).

    docker compose exec api python seed.py
"""
from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Customer, Product

PRODUCTS = [
    ("TOM-RED-KG", "Tomatoes, red", "kg", "2.40", "180", "40"),
    ("CUC-KG", "Cucumbers", "kg", "1.90", "120", "30"),
    ("POT-BAG-25", "Potatoes, bag 25 kg", "box", "14.00", "35", "10"),
    ("LEM-BOX", "Lemons, box 10 kg", "box", "18.50", "4", "5"),
    ("BAN-KG", "Bananas", "kg", "2.10", "90", "25"),
    ("PAR-BUNCH", "Parsley, bunch", "piece", "0.60", "60", "20"),
]
CUSTOMERS = [("Green Corner Ltd", "BG100000001"), ("Bistro Example", "BG100000002"), ("Market Stall 7", "BG100000003")]


def main() -> None:
    with SessionLocal() as db:
        if db.scalars(select(Product).limit(1)).first():
            print("already seeded")
            return
        db.add_all(Product(sku=s, name=n, unit=u, price=Decimal(p), stock=Decimal(st), min_stock=Decimal(m)) for s, n, u, p, st, m in PRODUCTS)
        db.add_all(Customer(name=n, vat_number=v) for n, v in CUSTOMERS)
        db.commit()
        print(f"seeded {len(PRODUCTS)} products and {len(CUSTOMERS)} customers")


if __name__ == "__main__":
    main()
