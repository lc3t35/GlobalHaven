from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import hashlib
import httpx
from passlib.context import CryptContext
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'globalhaven-secret-key-2025')
ALGORITHM = "HS256"
MCP_API_KEY = os.environ.get('MCP_API_KEY', 'mcp-globalhaven-2025')

# Create the main app
app = FastAPI(title="GlobalHaven API", description="Community Resource Sharing Platform")
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    full_name: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # {"lat": 0.0, "lng": 0.0}
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str  # food, water, tools, skills, shelter, medical, other
    type: str  # available, needed
    user_id: str
    location: Dict[str, float]  # {"lat": 0.0, "lng": 0.0}
    address: Optional[str] = None
    quantity: Optional[str] = None
    contact_info: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceCreate(BaseModel):
    title: str
    description: str
    category: str
    type: str
    location: Dict[str, float]
    address: Optional[str] = None
    quantity: Optional[str] = None
    contact_info: Optional[str] = None
    expiry_date: Optional[datetime] = None

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    resource_id: Optional[str] = None
    content: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    receiver_id: str
    resource_id: Optional[str] = None
    content: str

class MCPRequest(BaseModel):
    action: str
    data: Optional[Dict[str, Any]] = None

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

def verify_mcp_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != MCP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MCP API key"
        )
    return True

# Geocoding function
async def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """Geocode address using Nominatim (OpenStreetMap)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1
                },
                headers={"User-Agent": "GlobalHaven/1.0"}
            )
            data = response.json()
            if data:
                return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"])}
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

# Authentication routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    user_dict = user_data.dict()
    del user_dict["password"]
    user_dict["password_hash"] = password_hash
    user = User(**user_dict)
    
    await db.users.insert_one(user.dict())
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Resource routes
@api_router.post("/resources", response_model=Resource)
async def create_resource(resource_data: ResourceCreate, current_user: User = Depends(get_current_user)):
    resource_dict = resource_data.dict()
    resource_dict["user_id"] = current_user.id
    resource = Resource(**resource_dict)
    
    await db.resources.insert_one(resource.dict())
    return resource

@api_router.get("/resources", response_model=List[Resource])
async def get_resources(
    category: Optional[str] = None,
    type: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[float] = 10.0,  # km
    current_user: User = Depends(get_current_user)
):
    filter_query = {"is_active": True}
    
    if category:
        filter_query["category"] = category
    if type:
        filter_query["type"] = type
    
    resources = await db.resources.find(filter_query).to_list(1000)
    
    # Filter by location if provided
    if lat is not None and lng is not None:
        filtered_resources = []
        for resource in resources:
            res_lat = resource["location"]["lat"]
            res_lng = resource["location"]["lng"]
            
            # Simple distance calculation (Haversine formula would be more accurate)
            distance = ((lat - res_lat) ** 2 + (lng - res_lng) ** 2) ** 0.5 * 111  # Approximate km
            if distance <= radius:
                filtered_resources.append(resource)
        resources = filtered_resources
    
    return [Resource(**resource) for resource in resources]

@api_router.get("/resources/{resource_id}", response_model=Resource)
async def get_resource(resource_id: str, current_user: User = Depends(get_current_user)):
    resource = await db.resources.find_one({"id": resource_id, "is_active": True})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return Resource(**resource)

@api_router.put("/resources/{resource_id}", response_model=Resource)
async def update_resource(resource_id: str, resource_data: ResourceCreate, current_user: User = Depends(get_current_user)):
    resource = await db.resources.find_one({"id": resource_id, "user_id": current_user.id})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found or not owned by user")
    
    update_data = resource_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.resources.update_one({"id": resource_id}, {"$set": update_data})
    updated_resource = await db.resources.find_one({"id": resource_id})
    return Resource(**updated_resource)

@api_router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, current_user: User = Depends(get_current_user)):
    resource = await db.resources.find_one({"id": resource_id, "user_id": current_user.id})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found or not owned by user")
    
    await db.resources.update_one({"id": resource_id}, {"$set": {"is_active": False}})
    return {"message": "Resource deleted successfully"}

# Messaging routes
@api_router.post("/messages", response_model=Message)
async def send_message(message_data: MessageCreate, current_user: User = Depends(get_current_user)):
    message_dict = message_data.dict()
    message_dict["sender_id"] = current_user.id
    message = Message(**message_dict)
    
    await db.messages.insert_one(message.dict())
    return message

@api_router.get("/messages", response_model=List[Message])
async def get_messages(current_user: User = Depends(get_current_user)):
    messages = await db.messages.find({"$or": [{"sender_id": current_user.id}, {"receiver_id": current_user.id}]}).to_list(1000)
    return [Message(**message) for message in messages]

@api_router.put("/messages/{message_id}/read")
async def mark_message_read(message_id: str, current_user: User = Depends(get_current_user)):
    await db.messages.update_one(
        {"id": message_id, "receiver_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    return {"message": "Message marked as read"}

# MCP Server endpoints
@api_router.post("/mcp/search_resources")
async def mcp_search_resources(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Search resources via MCP"""
    data = request.data or {}
    
    filter_query = {"is_active": True}
    if data.get("category"):
        filter_query["category"] = data["category"]
    if data.get("type"):
        filter_query["type"] = data["type"]
    
    resources = await db.resources.find(filter_query).to_list(100)
    
    # Location filtering if provided
    if data.get("lat") and data.get("lng"):
        lat, lng = data["lat"], data["lng"]
        radius = data.get("radius", 10.0)
        
        filtered_resources = []
        for resource in resources:
            res_lat = resource["location"]["lat"]
            res_lng = resource["location"]["lng"]
            distance = ((lat - res_lat) ** 2 + (lng - res_lng) ** 2) ** 0.5 * 111
            if distance <= radius:
                filtered_resources.append(resource)
        resources = filtered_resources
    
    return {"resources": [Resource(**resource).dict() for resource in resources]}

@api_router.post("/mcp/create_resource")
async def mcp_create_resource(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Create resource via MCP (requires user_id in data)"""
    data = request.data
    if not data or not data.get("user_id"):
        raise HTTPException(status_code=400, detail="user_id required in data")
    
    # Verify user exists
    user = await db.users.find_one({"id": data["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Geocode address if provided and no location
    if data.get("address") and not data.get("location"):
        location = await geocode_address(data["address"])
        if location:
            data["location"] = location
    
    resource_data = ResourceCreate(**data)
    resource_dict = resource_data.dict()
    resource_dict["user_id"] = data["user_id"]
    resource = Resource(**resource_dict)
    
    await db.resources.insert_one(resource.dict())
    return {"resource": resource.dict()}

@api_router.post("/mcp/get_user_stats")
async def mcp_get_user_stats(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Get community statistics via MCP"""
    total_users = await db.users.count_documents({"is_active": True})
    total_resources = await db.resources.count_documents({"is_active": True})
    active_resources = await db.resources.count_documents({"is_active": True, "type": "available"})
    needed_resources = await db.resources.count_documents({"is_active": True, "type": "needed"})
    
    # Resources by category
    categories = ["food", "water", "tools", "skills", "shelter", "medical", "other"]
    category_stats = {}
    for category in categories:
        count = await db.resources.count_documents({"is_active": True, "category": category})
        category_stats[category] = count
    
    return {
        "stats": {
            "total_users": total_users,
            "total_resources": total_resources,
            "available_resources": active_resources,
            "needed_resources": needed_resources,
            "categories": category_stats
        }
    }

@api_router.get("/geocode")
async def geocode_endpoint(address: str, current_user: User = Depends(get_current_user)):
    """Geocode an address"""
    location = await geocode_address(address)
    if not location:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"location": location}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
