#!/usr/bin/env python3
"""
WMS v4.4 Quick Start
Run this to initialize the database with seed data and start the app.
"""
import os, sys

def main():
    print("🏭 WMS v4.4 — Quantum Warehouse")
    print("=" * 40)

    # Step 1: Check dependencies
    print("\n📦 Checking dependencies...")
    try:
        import streamlit, pandas, numpy, yaml
        print("   ✓ All core dependencies found")
    except ImportError as e:
        print(f"   ✗ Missing dependency: {e}")
        print("   Run: pip install -r requirements_v44.txt")
        return

    # Step 2: Initialize database
    print("\n🗄️  Initializing database...")
    from db import Database
    from seed_data import SeedData

    db = Database()
    seed = SeedData()
    stats = seed.seed_database(db)
    print(f"   ✓ Seeded {stats['users']} users, {stats['inventory']} inventory items, {stats['orders']} orders")

    # Step 3: Start app
    print("\n🚀 Starting Streamlit app...")
    print("   URL: http://localhost:8501")
    print("   Login: admin / admin")
    print("=" * 40)
    os.system("streamlit run app_v44.py")

if __name__ == "__main__":
    main()
