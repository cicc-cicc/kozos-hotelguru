#!/usr/bin/env python3
"""Direct script to add missing columns to bookings table"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from WebApp import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if columns already exist
    with db.engine.connect() as conn:
        # Get the current columns in bookings table
        result = conn.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'bookings' 
            AND TABLE_SCHEMA = DATABASE()
        """))
        existing_columns = {row[0] for row in result}
        print(f"Existing columns in bookings table: {existing_columns}")
        
        # Add check_in_time if it doesn't exist
        if 'check_in_time' not in existing_columns:
            print("Adding check_in_time column...")
            conn.execute(text("""
                ALTER TABLE bookings 
                ADD COLUMN check_in_time DATETIME NULL
            """))
            conn.commit()
            print("✓ check_in_time column added")
        else:
            print("✓ check_in_time column already exists")
        
        # Add check_out_time if it doesn't exist
        if 'check_out_time' not in existing_columns:
            print("Adding check_out_time column...")
            conn.execute(text("""
                ALTER TABLE bookings 
                ADD COLUMN check_out_time DATETIME NULL
            """))
            conn.commit()
            print("✓ check_out_time column added")
        else:
            print("✓ check_out_time column already exists")

        # Add guests_count if it doesn't exist
        if 'guests_count' not in existing_columns:
            print("Adding guests_count column...")
            conn.execute(text("""
                ALTER TABLE bookings 
                ADD COLUMN guests_count INT NOT NULL DEFAULT 1
            """))
            conn.commit()
            print("✓ guests_count column added")
        else:
            print("✓ guests_count column already exists")
        
        # Verify the columns were added
        result = conn.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'bookings' 
            AND TABLE_SCHEMA = DATABASE()
        """))
        final_columns = {row[0] for row in result}
        print(f"\nFinal columns in bookings table: {final_columns}")
        
        if {'check_in_time', 'check_out_time', 'guests_count'}.issubset(final_columns):
            print("\n✓ All required columns are present!")
        else:
            print("\n✗ Some columns are still missing")
            sys.exit(1)
