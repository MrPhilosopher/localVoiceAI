import sqlite3
import os
from pathlib import Path

# Path to the SQLite database
DB_PATH = 'data/app.db'

def run_migration():
    """Add embedding column to document_chunks table"""
    # Get the absolute path to the database
    script_dir = Path(__file__).parent.parent  # Go up one level from migrations/
    db_path = script_dir / DB_PATH
    
    print(f"Running migration to add embedding column to document_chunks table")
    print(f"Database path: {db_path}")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(document_chunks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'embedding' in columns:
            print("Column 'embedding' already exists in document_chunks table")
            conn.close()
            return True
        
        # Add the embedding column to the document_chunks table
        cursor.execute("ALTER TABLE document_chunks ADD COLUMN embedding TEXT")
        conn.commit()
        
        print("Successfully added 'embedding' column to document_chunks table")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    run_migration()