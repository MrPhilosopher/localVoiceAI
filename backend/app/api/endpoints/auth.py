from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings
from app.db.sqlite_db import get_sqlite_client
from app.models.user import User, UserCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str

class TokenData(BaseModel):
    user_id: str = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Use SQLite database   
    db = get_sqlite_client()
    response = db.table('users').select('*').eq('id', token_data.user_id).execute()
    
    if not response.data:
        raise credentials_exception
        
    user = response.data[0]
    return user

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    # Use SQLite database
    db = get_sqlite_client()
    
    # For debugging
    print(f"Registering user: {user.email}")
    
    try:
        # Check if user already exists
        try:
            print("Checking if user already exists")
            response = db.table('users').select('*').eq('email', user.email).execute()
            
            if response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        except HTTPException as e:
            raise e
        except Exception as check_error:
            print(f"Error checking existing user: {check_error}")
            # Continue with registration
            pass
        
        # Create user in auth system
        try:
            auth_response = db.auth.sign_up(
                email=user.email,
                password=user.password
            )
            
            # For debugging, log the structure of auth_response
            print(f"Auth response: {auth_response}")
            
            if not auth_response:
                raise ValueError("Failed to create auth user - empty response")
                
            # Get user ID
            user_id = auth_response.id
            print(f"Created auth user with ID: {user_id}")
            
        except Exception as auth_error:
            print(f"Error creating auth user: {auth_error}")
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create user account: {str(auth_error)}"
            )
        
        # Create user in users table
        try:
            new_user = {
                "id": user_id,
                "email": user.email,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "is_active": 1 if user.is_active else 0,  # SQLite uses integers for booleans
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            print(f"Inserting user into SQLite table: {new_user}")
            response = db.table('users').insert(new_user).execute()
            print(f"Insert response: {response.data}")
            
            if not response.data:
                raise ValueError("User record creation failed - empty response")
            
            return response.data[0]
            
        except Exception as db_error:
            print(f"Error creating user record: {db_error}")
            raise ValueError(f"User record creation failed: {db_error}")
            
    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Use SQLite database
    db = get_sqlite_client()
    
    # For debugging
    print(f"Attempting login for user: {form_data.username}")
    
    try:
        # Sign in with SQLite auth system
        auth_response = db.auth.sign_in(
            email=form_data.username,
            password=form_data.password
        )
        
        # For debugging
        print(f"Login response: {auth_response}")
        
        # Check the structure of the response
        if not auth_response:
            raise ValueError("Authentication failed")
            
        # Get user ID
        user_id = auth_response.id
        print(f"Authenticated user ID: {user_id}")
            
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id
        }
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return current_user