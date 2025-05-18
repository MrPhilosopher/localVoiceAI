import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def run_migrations():
    """Create tables in Supabase using the REST API"""
    
    # Get Supabase credentials from env
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required.")
        return False
    
    try:
        # Create Supabase client
        print(f"Connecting to Supabase at {supabase_url}...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Define table schemas
        # Note: This is a simplified version that creates only the users table
        # for demonstration purposes. The full migration would need SQL execution
        # access which requires a direct database connection.
        
        print("Creating users table...")
        
        # Here we're using a simplified RPC call for table creation
        # In a real scenario, the Supabase dashboard for SQL execution would be better
        try:
            # This is a very simplified approach - in reality you would use the SQL editor
            # in the Supabase dashboard to run the full migration script
            response = supabase.rpc(
                'create_users_table', 
                {}
            ).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"Error creating users table: {response.error}")
                print("Please use the Supabase dashboard SQL editor to run the migration script")
                return False
                
            print("Users table created successfully!")
            return True
            
        except Exception as e:
            print(f"Error creating table: {e}")
            print("Please use the Supabase dashboard SQL editor to run the migration script")
            print("Migration SQL is in backend/migrations/create_tables.sql")
            return False
            
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    print("Supabase Migration Script")
    print("-------------------------")
    print("This script attempts to create tables in Supabase.")
    print("For full migrations, use the SQL editor in the Supabase dashboard.")
    print("Copy the contents of backend/migrations/create_tables.sql and execute it there.")
    print("-------------------------")
    
    success = run_migrations()
    
    if success:
        print("Database setup completed!")
    else:
        print("\nTo manually create the tables:")
        print("1. Log in to your Supabase dashboard")
        print("2. Go to the SQL Editor")
        print("3. Copy the contents of backend/migrations/create_tables.sql")
        print("4. Execute the SQL script")