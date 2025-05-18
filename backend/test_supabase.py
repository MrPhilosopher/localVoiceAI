from app.db.supabase import get_supabase_client
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    # Get Supabase client
    print("Getting Supabase client...")
    supabase = get_supabase_client()
    print(f"Supabase client type: {type(supabase)}")
    
    # Try direct connection for testing
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    print(f"URL: {supabase_url}")
    print(f"Key (first 10 chars): {supabase_key[:10]}...")
    
    try:
        direct_client = create_client(supabase_url, supabase_key)
        print("Direct client created successfully")
        
        # Try different query formats
        try:
            print("\nTrying table() query...")
            response = direct_client.table('users').select('*').limit(1).execute()
            print(f"Response: {response}")
            print(f"Data: {response.data}")
        except Exception as e:
            print(f"table() query error: {e}")
        
        try:
            print("\nTrying from_() query...")
            response = direct_client.from_('users').select('*').limit(1).execute()
            print(f"Response: {response}")
            print(f"Data: {response.data}")
        except Exception as e:
            print(f"from_() query error: {e}")
            
        # If both failed, check if tables exist
        print("\nChecking which tables exist...")
        try:
            # This is a special query that lists tables
            response = direct_client.rpc('pg_table_list', {}).execute()
            print(f"Available tables: {response.data}")
        except Exception as e:
            print(f"Table list error: {e}")
        
    except Exception as e:
        print(f"Error creating direct client: {e}")

if __name__ == "__main__":
    test_supabase_connection()