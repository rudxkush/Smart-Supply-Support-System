#!/usr/bin/env python3
"""
Reset the 4S database to its initial state.
This script will delete the existing database and recreate it with default data.
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

# Database setup
DATABASE_PATH = 'database/4s_database.db'

def reset_db():
    """Reset the database to its initial state"""
    # Remove existing database if it exists
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"Removed existing database: {DATABASE_PATH}")
    
    # Make sure the database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Create a new database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # Create Requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        auto_tag TEXT NOT NULL,
        status TEXT NOT NULL,
        submitted_time TIMESTAMP NOT NULL,
        fulfilled_time TIMESTAMP,
        vendor_name TEXT,
        solution TEXT,
        estimated_delivery TEXT,
        forwarded_to_production INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create Status_Logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS status_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        FOREIGN KEY (request_id) REFERENCES requests (id)
    )
    ''')
    
    # Create Inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT UNIQUE NOT NULL,
        quantity INTEGER NOT NULL,
        status TEXT NOT NULL
    )
    ''')
    
    # Insert sample inventory items
    sample_inventory = [
        ('Product A', 50, 'In Stock'),
        ('Product B', 25, 'In Stock'),
        ('Product C', 0, 'Out of Stock'),
        ('Product D', 10, 'Low Stock')
    ]
    
    for item in sample_inventory:
        cursor.execute('INSERT INTO inventory (item_name, quantity, status) VALUES (?, ?, ?)', item)
    
    # Insert default users with pbkdf2:sha256 method which is compatible with Python 3.13
    default_users = [
        ('sales', generate_password_hash('sales123', method='pbkdf2:sha256'), 'Sales Executive'),
        ('warehouse', generate_password_hash('warehouse123', method='pbkdf2:sha256'), 'Warehouse Officer'),
        ('production', generate_password_hash('production123', method='pbkdf2:sha256'), 'Production Planner'),
        ('support', generate_password_hash('support123', method='pbkdf2:sha256'), 'Support Agent')
    ]
    
    for user in default_users:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', user)
    
    conn.commit()
    conn.close()
    
    print(f"Database reset successfully: {DATABASE_PATH}")
    print("Default users created:")
    for username, _, role in default_users:
        print(f"  - {role}: username '{username}'")

if __name__ == '__main__':
    reset_db()