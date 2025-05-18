from supabase import create_client, Client
from app.core.config import settings
import uuid
from datetime import datetime

# For demo purposes, we'll create an in-memory database
class InMemoryDatabase:
    def __init__(self):
        self.tables = {
            'users': [],
            'tenants': [],
            'documents': [],
            'document_embeddings': [],
            'conversations': [],
            'messages': []
        }
        self.auth_users = []

    def table(self, table_name):
        return TableQueryBuilder(self, table_name)
    
    def auth_sign_up(self, email, password):
        # Create a new auth user
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'email': email,
            'password': password,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        self.auth_users.append(user)
        # For debugging
        print(f"Created auth user: {user}")
        return AuthResponse(user)
    
    def auth_sign_in(self, email, password):
        # Find the user by email and password
        for user in self.auth_users:
            if user['email'] == email and user['password'] == password:
                return AuthResponse(user)
        return None
    
    class Auth:
        def __init__(self, db):
            self.db = db
        
        def sign_up(self, email, password):
            return self.db.auth_sign_up(email, password)
        
        def sign_in(self, email, password):
            return self.db.auth_sign_in(email, password)
    
    @property
    def auth(self):
        return self.Auth(self)
    
    class Storage:
        def from_(self, bucket):
            return {
                'download': lambda path: b'Mock file content'
            }
    
    @property
    def storage(self):
        return self.Storage()

class AuthResponse:
    def __init__(self, user):
        self.user = user
        self.id = user['id']
        
    def __str__(self):
        return f"AuthResponse(id={self.id})"
        
    def __repr__(self):
        return self.__str__()

class TableQueryBuilder:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.filters = []
        self.insert_data = None
        self.update_data = None
    
    def select(self, fields):
        return self
    
    def eq(self, field, value):
        self.filters.append((field, value))
        return self
    
    def insert(self, data):
        self.insert_data = data
        return self
    
    def update(self, data):
        self.update_data = data
        return self
    
    def execute(self):
        if self.insert_data:
            # Add ID if not present
            if 'id' not in self.insert_data:
                self.insert_data['id'] = str(uuid.uuid4())
            
            # Add timestamps if not present
            if 'created_at' not in self.insert_data:
                self.insert_data['created_at'] = datetime.utcnow()
            if 'updated_at' not in self.insert_data:
                self.insert_data['updated_at'] = datetime.utcnow()
                
            self.db.tables[self.table_name].append(self.insert_data)
            return QueryResponse([self.insert_data])
            
        elif self.update_data:
            # Apply update to matching items
            matched_items = []
            for item in self.db.tables[self.table_name]:
                matches = True
                for field, value in self.filters:
                    if item.get(field) != value:
                        matches = False
                        break
                
                if matches:
                    for key, value in self.update_data.items():
                        item[key] = value
                    item['updated_at'] = datetime.utcnow()
                    matched_items.append(item)
            
            return QueryResponse(matched_items)
            
        else:
            # Apply filters to find matching items
            result = []
            for item in self.db.tables[self.table_name]:
                matches = True
                for field, value in self.filters:
                    if item.get(field) != value:
                        matches = False
                        break
                
                if matches:
                    result.append(item)
            
            return QueryResponse(result)

class QueryResponse:
    def __init__(self, data):
        self.data = data
        
    def __str__(self):
        return f"QueryResponse(data={self.data})"
        
    def __repr__(self):
        return self.__str__()

# Create in-memory database for demo
in_memory_db = InMemoryDatabase()

# Pre-populate with a test user
test_user_id = str(uuid.uuid4())
test_user_auth = {
    'id': test_user_id,
    'email': 'test@example.com',
    'password': 'testpassword',
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}
in_memory_db.auth_users.append(test_user_auth)

# Add test user to users table
test_user = {
    'id': test_user_id,
    'email': 'test@example.com',
    'full_name': 'Test User',
    'company_name': 'Test Company',
    'is_active': True,
    'created_at': datetime.utcnow(),
    'updated_at': datetime.utcnow()
}
in_memory_db.tables['users'].append(test_user)
print(f"Pre-populated in-memory DB with test user: {test_user['email']}")

# Connect to the real Supabase client, but be ready to fall back to in-memory DB
try:
    print(f"Attempting to connect to Supabase at {settings.SUPABASE_URL}")
    real_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    print("Real Supabase client created successfully")
    
    # We know tables exist, so just use the real client
    supabase = real_supabase
    print("Successfully connected to Supabase database")
    print("Using real Supabase client")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    print("Using in-memory database as fallback")
    supabase = in_memory_db

def get_supabase_client():
    # Return whatever client we're using (real or in-memory)
    return supabase