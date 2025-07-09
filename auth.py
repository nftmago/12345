# app/auth.py
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import UserDB, UserCreate, UserLogin
from database import get_db, get_user_by_username, get_user_by_email, create_user

# ============ PASSWORD HASHING ============
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
)

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with improved error handling and safe fallback"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Only fallback if hash looks like bcrypt
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            try:
                import bcrypt
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            except Exception:
                return False
        return False

def get_password_hash(password: str) -> str:
    """Hash password with improved error handling"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Log the error but don't expose it to user
        logging.error(f"Password hashing error: {str(e)}")
        # Fallback to simpler bcrypt if needed
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# ============ JWT TOKEN FUNCTIONS ============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

# ============ USER AUTHENTICATION ============
async def authenticate_user(username: str, password: str, db: AsyncSession) -> Optional[UserDB]:
    """Authenticate a user"""
    user = await get_user_by_username(username, db)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def register_user(user_data: UserCreate, db: AsyncSession) -> UserDB:
    """Register a new user with enhanced validation"""
    # Validate username format
    if not user_data.username.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Check if username already exists
    existing_user = await get_user_by_username(user_data.username, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(user_data.email, db)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength (additional validation beyond Pydantic)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    return await create_user(user_dict, db)

async def login_user(user_credentials: UserLogin, db: AsyncSession) -> dict:
    """Login user and return token"""
    # Validate input
    if not user_credentials.username or not user_credentials.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required"
        )
    
    user = await authenticate_user(user_credentials.username, user_credentials.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ============ AUTHENTICATION DEPENDENCIES ============
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
) -> UserDB:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(username, db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def verify_user_access(user_id: str, current_user: UserDB = Depends(get_current_active_user)) -> str:
    """Verify that the current user can access the specified user_id"""
    if current_user.username != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user_id

# ============ OPTIONAL AUTHENTICATION ============
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[UserDB]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = await get_user_by_username(username, db)
        return user if user and user.is_active else None
    except JWTError:
        return None

# ============ PERMISSION HELPERS ============
def check_user_permission(current_user: UserDB, target_user_id: str) -> bool:
    """Check if current user has permission to access target user's data"""
    # A user can only access their own data. is_active is not an admin check.
    return current_user.username == target_user_id

def require_user_permission(current_user: UserDB, target_user_id: str):
    """Require user permission or raise HTTPException"""
    if not check_user_permission(current_user, target_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient permissions"
        )

# ============ PASSWORD UTILITIES ============
def validate_password_strength(password: str) -> bool:
    """Validate password meets strength requirements"""
    import re
    
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    
    return True

def get_password_strength_errors(password: str) -> List[str]:
    """Get list of password strength errors"""
    import re
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    
    return errors

# ============ TOKEN UTILITIES ============
def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token without validation"""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

def is_token_expired(token: str) -> bool:
    """Check if token is expired"""
    payload = decode_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow().timestamp() > exp

def get_token_expiry(token: str) -> Optional[datetime]:
    """Get token expiry datetime"""
    payload = decode_token(token)
    if not payload:
        return None
    
    exp = payload.get("exp")
    if not exp:
        return None
    
    return datetime.fromtimestamp(exp)

# ============ SECURITY UTILITIES ============
def generate_secure_random_string(length: int = 32) -> str:
    """Generate a secure random string for tokens"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(input_string: str) -> str:
    """Hash a string using SHA-256"""
    import hashlib
    return hashlib.sha256(input_string.encode()).hexdigest()

# ============ SESSION MANAGEMENT ============
class SessionManager:
    """Simple session management utilities"""
    
    @staticmethod
    def create_session_token(user_id: str, session_data: dict = None) -> str:
        """Create a session token with additional data"""
        data = {"sub": user_id}
        if session_data:
            data.update(session_data)
        
        return create_access_token(data)
    
    @staticmethod
    def validate_session(token: str) -> Optional[dict]:
        """Validate session token and return payload"""
        return decode_token(token)
    
    @staticmethod
    def refresh_session(token: str) -> Optional[str]:
        """Refresh session token if valid"""
        payload = decode_token(token)
        if not payload:
            return None
        
        # Remove exp from payload and create new token
        payload.pop("exp", None)
        return create_access_token(payload)
