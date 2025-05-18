import sqlite3
import json
import uuid
import os
from datetime import datetime
from pathlib import Path

# Create a 'data' directory if it doesn't exist
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Database file path
DB_PATH = 'data/app.db'

class SQLiteDB:
    """SQLite database implementation to replace in-memory database"""
    
    def __init__(self):
        """Initialize database connection and create tables if they don't exist"""
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Use Row factory for dictionaries
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
        
        # Initialize auth system
        self.auth = self.Auth(self)
        self.storage = self.Storage(self)
        
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            company_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create tenants table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            website_url TEXT,
            is_active INTEGER DEFAULT 1,
            owner_id TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            has_whatsapp_integration INTEGER DEFAULT 0,
            has_calendar_integration INTEGER DEFAULT 0,
            chat_widget_config TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
        ''')
        
        # Create documents table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            document_type TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            is_processed INTEGER DEFAULT 0,
            embedding_status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        )
        ''')
        
        # Create document chunks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents (id)
        )
        ''')

        # Create a directory for document storage
        os.makedirs('data/documents', exist_ok=True)
        
        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            customer_identifier TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            content TEXT NOT NULL,
            role TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        ''')
        
        self.conn.commit()
    
    def table(self, table_name):
        """Get a query builder for a specific table"""
        return TableQueryBuilder(self, table_name)
    
    # Auth functionality
    class Auth:
        def __init__(self, db):
            self.db = db
        
        def sign_up(self, email, password):
            """Create a new user in the auth system"""
            user_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            cursor = self.db.conn.cursor()
            cursor.execute(
                "INSERT INTO auth_users (id, email, password, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, password, now, now)
            )
            self.db.conn.commit()
            
            # Return auth response object
            user = {
                'id': user_id,
                'email': email,
                'password': password,
                'created_at': now,
                'updated_at': now
            }
            return AuthResponse(user)
        
        def sign_in(self, email, password):
            """Sign in existing user"""
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT * FROM auth_users WHERE email = ? AND password = ?",
                (email, password)
            )
            row = cursor.fetchone()
            
            if row:
                user = dict(row)
                return AuthResponse(user)
            return None
    
    # Storage functionality
    class Storage:
        def __init__(self, db):
            self.db = db
            self.storage_path = Path('data/documents')
            self.storage_path.mkdir(exist_ok=True)
        
        def from_(self, bucket):
            """Get storage bucket operations"""
            return StorageBucket(self, bucket)
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Helper Classes
class AuthResponse:
    """Auth response object to match Supabase interface"""
    def __init__(self, user):
        self.user = user
        self.id = user['id']
    
    def __str__(self):
        return f"AuthResponse(id={self.id})"
        
    def __repr__(self):
        return self.__str__()

class StorageBucket:
    """Storage bucket operations"""
    def __init__(self, storage, bucket_name):
        self.storage = storage
        self.bucket_name = bucket_name
        self.base_path = self.storage.storage_path / bucket_name
        self.base_path.mkdir(exist_ok=True)
    
    def upload(self, path, file, file_options=None):
        """Save a file to storage"""
        # Ensure directories exist
        full_path = self.base_path / path
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, 'wb') as f:
            # If it's a bytes object, write directly
            if isinstance(file, bytes):
                f.write(file)
            # If it has a read method (file-like object)
            elif hasattr(file, 'read'):
                # If 'read' is callable, use it
                if callable(file.read):
                    data = file.read()
                    if isinstance(data, bytes):
                        f.write(data)
                    else:
                        f.write(data.encode('utf-8'))
                else:
                    # If 'read' is not callable, convert to string and write
                    f.write(str(file).encode('utf-8'))
            else:
                # Fall back to string conversion
                f.write(str(file).encode('utf-8'))
        
        return {"path": path}
    
    def download(self, path):
        """Download file content"""
        full_path = self.base_path / path
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return b'File not found'
    
    def remove(self, paths):
        """Remove files"""
        for path in paths:
            full_path = self.base_path / path
            try:
                os.remove(full_path)
            except FileNotFoundError:
                pass

class TableQueryBuilder:
    """SQL query builder class to match Supabase interface"""
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.select_fields = '*'
        self.where_clauses = []
        self.where_values = []
        self.insert_data = None
        self.update_data = None
        self.delete_flag = False
    
    def select(self, fields):
        """Select specific fields"""
        self.select_fields = fields
        return self
    
    def eq(self, field, value):
        """Add equality condition"""
        self.where_clauses.append(f"{field} = ?")
        self.where_values.append(value)
        return self
    
    def insert(self, data):
        """Set data to insert"""
        self.insert_data = data
        return self
    
    def update(self, data):
        """Set data to update"""
        self.update_data = data
        return self
    
    def delete(self):
        """Set delete flag"""
        self.delete_flag = True
        return self
    
    def execute(self):
        """Execute the query"""
        cursor = self.db.conn.cursor()
        
        try:
            # Insert operation
            if self.insert_data:
                # Add ID if not present
                if 'id' not in self.insert_data:
                    self.insert_data['id'] = str(uuid.uuid4())
                
                # Handle JSON fields
                for key, value in self.insert_data.items():
                    if isinstance(value, dict):
                        self.insert_data[key] = json.dumps(value)
                
                # Build query
                columns = ', '.join(self.insert_data.keys())
                placeholders = ', '.join(['?'] * len(self.insert_data))
                query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                
                cursor.execute(query, list(self.insert_data.values()))
                self.db.conn.commit()
                
                # Get the inserted data
                query = f"SELECT * FROM {self.table_name} WHERE id = ?"
                cursor.execute(query, (self.insert_data['id'],))
                
                # Format the result
                result = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for row in result:
                    for key, value in row.items():
                        if key == 'chat_widget_config' and isinstance(value, str):
                            try:
                                row[key] = json.loads(value)
                            except:
                                pass
                
                return QueryResponse(result)
            
            # Update operation
            elif self.update_data and self.where_clauses:
                # Handle JSON fields
                for key, value in self.update_data.items():
                    if isinstance(value, dict):
                        self.update_data[key] = json.dumps(value)
                
                # Build query
                set_clause = ', '.join([f"{key} = ?" for key in self.update_data.keys()])
                where_clause = ' AND '.join(self.where_clauses)
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE {where_clause}"
                
                # Execute
                values = list(self.update_data.values()) + self.where_values
                cursor.execute(query, values)
                self.db.conn.commit()
                
                # Get the updated data
                select_query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
                cursor.execute(select_query, self.where_values)
                
                # Format the result
                result = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for row in result:
                    for key, value in row.items():
                        if key == 'chat_widget_config' and isinstance(value, str):
                            try:
                                row[key] = json.loads(value)
                            except:
                                pass
                
                return QueryResponse(result)
            
            # Delete operation
            elif self.delete_flag and self.where_clauses:
                where_clause = ' AND '.join(self.where_clauses)
                query = f"DELETE FROM {self.table_name} WHERE {where_clause}"
                
                cursor.execute(query, self.where_values)
                self.db.conn.commit()
                
                return QueryResponse([])
            
            # Select operation
            else:
                where_clause = ''
                if self.where_clauses:
                    where_clause = 'WHERE ' + ' AND '.join(self.where_clauses)
                
                query = f"SELECT {self.select_fields} FROM {self.table_name} {where_clause}"
                
                cursor.execute(query, self.where_values)
                
                # Format the result
                result = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON fields
                for row in result:
                    for key, value in row.items():
                        if key == 'chat_widget_config' and isinstance(value, str):
                            try:
                                row[key] = json.loads(value)
                            except:
                                pass
                
                return QueryResponse(result)
                
        except Exception as e:
            print(f"SQL Error: {e}")
            self.db.conn.rollback()
            raise e

class QueryResponse:
    """Query response object to match Supabase interface"""
    def __init__(self, data):
        self.data = data
    
    def __str__(self):
        return f"QueryResponse(data={self.data})"
    
    def __repr__(self):
        return self.__str__()

# Create SQLite database instance
sqlite_db = SQLiteDB()

# Pre-populate with a test user for convenience
try:
    test_user_id = str(uuid.uuid4())
    test_email = 'test@example.com'
    test_password = 'testpassword'
    
    # Check if user already exists
    cursor = sqlite_db.conn.cursor()
    cursor.execute("SELECT * FROM auth_users WHERE email = ?", (test_email,))
    if not cursor.fetchone():
        # Create test user in auth
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO auth_users (id, email, password, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (test_user_id, test_email, test_password, now, now)
        )
        
        # Create test user in users table
        cursor.execute(
            "INSERT INTO users (id, email, full_name, company_name, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (test_user_id, test_email, 'Test User', 'Test Company', 1, now, now)
        )
        
        sqlite_db.conn.commit()
        print(f"Pre-populated SQLite DB with test user: {test_email}")
    else:
        print(f"Test user {test_email} already exists in SQLite DB")
except Exception as e:
    print(f"Error pre-populating test user: {e}")

def get_sqlite_client():
    """Get SQLite database client"""
    return sqlite_db