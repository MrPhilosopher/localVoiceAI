import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_postgres_url(supabase_url, supabase_key):
    """
    Builds a PostgreSQL connection string from Supabase credentials.
    For Supabase, we need to use the connection string format for direct database access.
    
    """
    # Extract the project ID from the URL
    project_id = supabase_url.split('//')[1].split('.')[0]
    
    # The connection details for Supabase PostgreSQL
    host = f"db.{project_id}.supabase.co"
    port = 5432
    database = "postgres"
    user = "postgres"
    password = supabase_key.split('.')[1]  # The middle part of the JWT is often used as the password
    
    return f"postgres://{user}:{password}@{host}:{port}/{database}"

def run_migrations(conn_string):
    """Run the migrations from the SQL file."""
    try:
        # Connect to the database
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read the migration file
        with open('migrations/create_tables.sql', 'r') as f:
            sql = f.read()
        
        # Execute the migrations
        cursor.execute(sql)
        
        # Close the connection
        cursor.close()
        conn.close()
        
        print("Migrations completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    # Get database credentials from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required.")
        sys.exit(1)
    
    # Parse PostgreSQL connection string
    conn_string = parse_postgres_url(supabase_url, supabase_key)
    
    # Run migrations
    success = run_migrations(conn_string)
    
    if success:
        print("Database tables created successfully.")
    else:
        print("Failed to create database tables.")
        sys.exit(1)