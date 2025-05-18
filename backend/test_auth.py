import os
from dotenv import load_dotenv
from supabase import create_client
import traceback
import json
import random
import string

# Load environment variables
load_dotenv()

def random_email():
    """Generate a random email for testing"""
    random_str = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    return f"test_{random_str}@example.com"

def test_auth():
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required.")
        return
    
    # Create Supabase client
    print(f"Connecting to Supabase at {supabase_url}...")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")
        
        # Test user registration
        email = random_email()
        password = "testpassword123"
        
        print(f"\nRegistering test user: {email}")
        try:
            # Try sign_up with different parameter formats to see what works
            print("Attempt 1: Using kwargs with email and password parameters")
            auth_response = supabase.auth.sign_up(
                email=email, 
                password=password
            )
            print(f"Response: {auth_response}")
            print("Registration successful!")
            
        except Exception as e:
            print(f"Registration error: {e}")
            print("Stack trace:")
            traceback.print_exc()
            
            # Try alternative format
            try:
                print("\nAttempt 2: Using dictionary format")
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                print(f"Response: {auth_response}")
                print("Registration successful!")
                
            except Exception as e:
                print(f"Registration error: {e}")
                print("Stack trace:")
                traceback.print_exc()
                
                # Check supabase version
                try:
                    import supabase
                    print(f"\nSupabase package version: {supabase.__version__}")
                except:
                    print("Could not determine Supabase version")
                
                # Try debugging API
                try:
                    print("\nAttempt 3: Using debug mode")
                    auth_response = supabase.auth._url 
                    print(f"Auth URL: {auth_response}")
                    
                    # List available methods
                    print("\nAvailable auth methods:")
                    for name in dir(supabase.auth):
                        if not name.startswith('_'):
                            print(f"- {name}")
                except Exception as e:
                    print(f"Debug error: {e}")
        
    except Exception as e:
        print(f"Supabase connection error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_auth()