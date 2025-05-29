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

# Water Access Module Models
class WaterSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # well, spring, tap, river, lake, rainwater, other
    location: Dict[str, float]  # {"lat": 0.0, "lng": 0.0}
    address: Optional[str] = None
    accessibility: str  # public, private, restricted, seasonal
    quality_status: str = "unknown"  # safe, unsafe, needs_testing, unknown
    flow_rate: Optional[str] = None  # liters per minute/hour
    depth: Optional[float] = None  # meters (for wells)
    treatment_required: bool = False
    last_tested: Optional[datetime] = None
    added_by: str  # user_id
    verified_by: Optional[str] = None  # user_id of verifier
    community_rating: float = 0.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WaterSourceCreate(BaseModel):
    name: str
    type: str
    location: Dict[str, float]
    address: Optional[str] = None
    accessibility: str = "public"
    quality_status: str = "unknown"
    flow_rate: Optional[str] = None
    depth: Optional[float] = None
    treatment_required: bool = False

class QualityReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    water_source_id: str
    reporter_id: str
    test_type: str  # visual, taste, laboratory, field_kit, community_feedback
    ph_level: Optional[float] = None
    turbidity: Optional[str] = None  # clear, slightly_cloudy, cloudy, very_cloudy
    color: Optional[str] = None
    odor: Optional[str] = None
    taste: Optional[str] = None
    bacteria_present: Optional[bool] = None
    chemical_contaminants: Optional[List[str]] = None
    overall_rating: str  # safe, caution, unsafe
    notes: Optional[str] = None
    test_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QualityReportCreate(BaseModel):
    water_source_id: str
    test_type: str
    ph_level: Optional[float] = None
    turbidity: Optional[str] = None
    color: Optional[str] = None
    odor: Optional[str] = None
    taste: Optional[str] = None
    bacteria_present: Optional[bool] = None
    chemical_contaminants: Optional[List[str]] = None
    overall_rating: str
    notes: Optional[str] = None

class InfrastructurePlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    plan_type: str  # well_drilling, rainwater_harvesting, pipeline, filtration_system, storage_tank
    location: Dict[str, float]
    estimated_cost: Optional[float] = None
    currency: str = "USD"
    materials_needed: List[str] = []
    tools_required: List[str] = []
    estimated_time: Optional[str] = None  # "2 weeks", "3 months"
    skill_level: str  # beginner, intermediate, advanced, professional
    water_yield: Optional[str] = None  # expected output
    serves_population: Optional[int] = None
    created_by: str
    community_approved: bool = False
    funding_status: str = "planning"  # planning, seeking_funds, funded, in_progress, completed
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InfrastructurePlanCreate(BaseModel):
    title: str
    description: str
    plan_type: str
    location: Dict[str, float]
    estimated_cost: Optional[float] = None
    currency: str = "USD"
    materials_needed: List[str] = []
    tools_required: List[str] = []
    estimated_time: Optional[str] = None
    skill_level: str = "beginner"
    water_yield: Optional[str] = None
    serves_population: Optional[int] = None

class PurificationGuide(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    method_type: str  # boiling, solar_disinfection, sand_filtration, chlorination, ceramic_filter, uv_treatment
    local_materials: List[str] = []
    steps: List[str] = []
    time_required: Optional[str] = None
    effectiveness: str  # high, medium, low
    suitable_for: List[str] = []  # bacteria, viruses, chemicals, sediment
    region_specific: Optional[str] = None
    cost_estimate: Optional[str] = None
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    created_by: str
    community_rating: float = 0.0
    usage_count: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PurificationGuideCreate(BaseModel):
    title: str
    description: str
    method_type: str
    local_materials: List[str] = []
    steps: List[str] = []
    time_required: Optional[str] = None
    effectiveness: str = "medium"
    suitable_for: List[str] = []
    region_specific: Optional[str] = None
    cost_estimate: Optional[str] = None
    difficulty_level: str = "beginner"

class WaterAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    alert_type: str  # contamination, supply_disruption, infrastructure_failure, quality_concern
    severity: str  # low, medium, high, critical
    location: Dict[str, float]
    radius_km: float = 5.0  # affected area radius
    water_source_ids: List[str] = []  # affected water sources
    issued_by: str  # user_id
    verified: bool = False
    verified_by: Optional[str] = None
    active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WaterAlertCreate(BaseModel):
    title: str
    description: str
    alert_type: str
    severity: str
    location: Dict[str, float]
    radius_km: float = 5.0
    water_source_ids: List[str] = []
    expires_at: Optional[datetime] = None

class WaterUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: datetime = Field(default_factory=datetime.utcnow)
    drinking_liters: float = 0.0
    cooking_liters: float = 0.0
    cleaning_liters: float = 0.0
    agriculture_liters: float = 0.0
    other_liters: float = 0.0
    total_liters: float = 0.0
    source_ids: List[str] = []  # water sources used
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WaterUsageCreate(BaseModel):
    date: Optional[datetime] = None
    drinking_liters: float = 0.0
    cooking_liters: float = 0.0
    cleaning_liters: float = 0.0
    agriculture_liters: float = 0.0
    other_liters: float = 0.0
    source_ids: List[str] = []
    notes: Optional[str] = None

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

@api_router.post("/mcp/search_water_sources")
async def mcp_search_water_sources(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Search water sources via MCP"""
    data = request.data or {}
    
    filter_query = {"is_active": True}
    if data.get("type"):
        filter_query["type"] = data["type"]
    if data.get("accessibility"):
        filter_query["accessibility"] = data["accessibility"]
    if data.get("quality_status"):
        filter_query["quality_status"] = data["quality_status"]
    
    sources = await db.water_sources.find(filter_query).to_list(100)
    
    # Location filtering if provided
    if data.get("lat") and data.get("lng"):
        lat, lng = data["lat"], data["lng"]
        radius = data.get("radius", 10.0)
        
        filtered_sources = []
        for source in sources:
            source_lat = source["location"]["lat"]
            source_lng = source["location"]["lng"]
            distance = ((lat - source_lat) ** 2 + (lng - source_lng) ** 2) ** 0.5 * 111
            if distance <= radius:
                filtered_sources.append(source)
        sources = filtered_sources
    
    return {"water_sources": [WaterSource(**source).dict() for source in sources]}

@api_router.post("/mcp/get_water_alerts")
async def mcp_get_water_alerts(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Get water alerts via MCP"""
    data = request.data or {}
    
    filter_query = {"active": True}
    if data.get("alert_type"):
        filter_query["alert_type"] = data["alert_type"]
    if data.get("severity"):
        filter_query["severity"] = data["severity"]
    
    # Filter out expired alerts
    filter_query["$or"] = [
        {"expires_at": {"$gte": datetime.utcnow()}},
        {"expires_at": None}
    ]
    
    alerts = await db.water_alerts.find(filter_query).sort("created_at", -1).to_list(50)
    
    # Location filtering if provided
    if data.get("lat") and data.get("lng"):
        lat, lng = data["lat"], data["lng"]
        
        filtered_alerts = []
        for alert in alerts:
            alert_lat = alert["location"]["lat"]
            alert_lng = alert["location"]["lng"]
            distance = ((lat - alert_lat) ** 2 + (lng - alert_lng) ** 2) ** 0.5 * 111
            if distance <= alert["radius_km"]:
                filtered_alerts.append(alert)
        alerts = filtered_alerts
    
    return {"water_alerts": [WaterAlert(**alert).dict() for alert in alerts]}

@api_router.post("/mcp/get_purification_guides")
async def mcp_get_purification_guides(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Get purification guides via MCP"""
    data = request.data or {}
    
    filter_query = {"is_active": True}
    if data.get("method_type"):
        filter_query["method_type"] = data["method_type"]
    if data.get("effectiveness"):
        filter_query["effectiveness"] = data["effectiveness"]
    if data.get("difficulty_level"):
        filter_query["difficulty_level"] = data["difficulty_level"]
    
    guides = await db.purification_guides.find(filter_query).sort("community_rating", -1).to_list(50)
    
    return {"purification_guides": [PurificationGuide(**guide).dict() for guide in guides]}

@api_router.post("/mcp/create_water_source")
async def mcp_create_water_source(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Create water source via MCP"""
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
    
    source_data = WaterSourceCreate(**data)
    source_dict = source_data.dict()
    source_dict["added_by"] = data["user_id"]
    source = WaterSource(**source_dict)
    
    await db.water_sources.insert_one(source.dict())
    return {"water_source": source.dict()}

@api_router.post("/mcp/create_water_alert")
async def mcp_create_water_alert(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Create water alert via MCP"""
    data = request.data
    if not data or not data.get("user_id"):
        raise HTTPException(status_code=400, detail="user_id required in data")
    
    # Verify user exists
    user = await db.users.find_one({"id": data["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alert_data = WaterAlertCreate(**data)
    alert_dict = alert_data.dict()
    alert_dict["issued_by"] = data["user_id"]
    alert = WaterAlert(**alert_dict)
    
    await db.water_alerts.insert_one(alert.dict())
    return {"water_alert": alert.dict()}

@api_router.post("/mcp/log_water_usage")
async def mcp_log_water_usage(
    request: MCPRequest,
    api_key_valid: bool = Depends(verify_mcp_api_key)
):
    """Log water usage via MCP"""
    data = request.data
    if not data or not data.get("user_id"):
        raise HTTPException(status_code=400, detail="user_id required in data")
    
    # Verify user exists
    user = await db.users.find_one({"id": data["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usage_data = WaterUsageCreate(**{k: v for k, v in data.items() if k != "user_id"})
    usage_dict = usage_data.dict()
    usage_dict["user_id"] = data["user_id"]
    
    if not usage_dict["date"]:
        usage_dict["date"] = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate total
    total = (usage_dict["drinking_liters"] + usage_dict["cooking_liters"] + 
             usage_dict["cleaning_liters"] + usage_dict["agriculture_liters"] + 
             usage_dict["other_liters"])
    usage_dict["total_liters"] = total
    
    usage = WaterUsage(**usage_dict)
    
    # Check if usage already exists for this date, update if so
    existing = await db.water_usage.find_one({
        "user_id": data["user_id"],
        "date": usage_dict["date"]
    })
    
    if existing:
        await db.water_usage.update_one(
            {"id": existing["id"]},
            {"$set": usage_dict}
        )
        result_usage = WaterUsage(**{**existing, **usage_dict})
    else:
        await db.water_usage.insert_one(usage.dict())
        result_usage = usage
    
    return {"water_usage": result_usage.dict()}

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
    
    # Water-specific stats
    total_water_sources = await db.water_sources.count_documents({"is_active": True})
    safe_water_sources = await db.water_sources.count_documents({"is_active": True, "quality_status": "safe"})
    active_alerts = await db.water_alerts.count_documents({"active": True})
    total_purification_guides = await db.purification_guides.count_documents({"is_active": True})
    users_tracking_water = await db.water_usage.distinct("user_id")
    
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
            "categories": category_stats,
            "water_module": {
                "total_water_sources": total_water_sources,
                "safe_water_sources": safe_water_sources,
                "active_water_alerts": active_alerts,
                "purification_guides": total_purification_guides,
                "users_tracking_usage": len(users_tracking_water)
            }
        }
    }

@api_router.get("/geocode")
async def geocode_endpoint(address: str, current_user: User = Depends(get_current_user)):
    """Geocode an address"""
    location = await geocode_address(address)
    if not location:
        raise HTTPException(status_code=404, detail="Address not found")
    return {"location": location}

# Water Access Module Routes

# Water Sources
@api_router.post("/water/sources", response_model=WaterSource)
async def create_water_source(source_data: WaterSourceCreate, current_user: User = Depends(get_current_user)):
    source_dict = source_data.dict()
    source_dict["added_by"] = current_user.id
    source = WaterSource(**source_dict)
    
    await db.water_sources.insert_one(source.dict())
    return source

@api_router.get("/water/sources", response_model=List[WaterSource])
async def get_water_sources(
    type: Optional[str] = None,
    accessibility: Optional[str] = None,
    quality_status: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[float] = 10.0,
    current_user: User = Depends(get_current_user)
):
    filter_query = {"is_active": True}
    
    if type:
        filter_query["type"] = type
    if accessibility:
        filter_query["accessibility"] = accessibility
    if quality_status:
        filter_query["quality_status"] = quality_status
    
    sources = await db.water_sources.find(filter_query).to_list(1000)
    
    # Filter by location if provided
    if lat is not None and lng is not None:
        filtered_sources = []
        for source in sources:
            source_lat = source["location"]["lat"]
            source_lng = source["location"]["lng"]
            distance = ((lat - source_lat) ** 2 + (lng - source_lng) ** 2) ** 0.5 * 111
            if distance <= radius:
                filtered_sources.append(source)
        sources = filtered_sources
    
    return [WaterSource(**source) for source in sources]

@api_router.get("/water/sources/{source_id}", response_model=WaterSource)
async def get_water_source(source_id: str, current_user: User = Depends(get_current_user)):
    source = await db.water_sources.find_one({"id": source_id, "is_active": True})
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found")
    return WaterSource(**source)

@api_router.put("/water/sources/{source_id}", response_model=WaterSource)
async def update_water_source(source_id: str, source_data: WaterSourceCreate, current_user: User = Depends(get_current_user)):
    source = await db.water_sources.find_one({"id": source_id, "added_by": current_user.id})
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found or not owned by user")
    
    update_data = source_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.water_sources.update_one({"id": source_id}, {"$set": update_data})
    updated_source = await db.water_sources.find_one({"id": source_id})
    return WaterSource(**updated_source)

# Quality Reports
@api_router.post("/water/quality-reports", response_model=QualityReport)
async def create_quality_report(report_data: QualityReportCreate, current_user: User = Depends(get_current_user)):
    # Verify water source exists
    source = await db.water_sources.find_one({"id": report_data.water_source_id, "is_active": True})
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found")
    
    report_dict = report_data.dict()
    report_dict["reporter_id"] = current_user.id
    report = QualityReport(**report_dict)
    
    await db.quality_reports.insert_one(report.dict())
    
    # Update water source quality status based on latest report
    await db.water_sources.update_one(
        {"id": report_data.water_source_id},
        {"$set": {"quality_status": report_data.overall_rating, "last_tested": datetime.utcnow()}}
    )
    
    return report

@api_router.get("/water/quality-reports", response_model=List[QualityReport])
async def get_quality_reports(
    water_source_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    filter_query = {}
    if water_source_id:
        filter_query["water_source_id"] = water_source_id
    
    reports = await db.quality_reports.find(filter_query).sort("test_date", -1).to_list(1000)
    return [QualityReport(**report) for report in reports]

# Infrastructure Plans
@api_router.post("/water/infrastructure-plans", response_model=InfrastructurePlan)
async def create_infrastructure_plan(plan_data: InfrastructurePlanCreate, current_user: User = Depends(get_current_user)):
    plan_dict = plan_data.dict()
    plan_dict["created_by"] = current_user.id
    plan = InfrastructurePlan(**plan_dict)
    
    await db.infrastructure_plans.insert_one(plan.dict())
    return plan

@api_router.get("/water/infrastructure-plans", response_model=List[InfrastructurePlan])
async def get_infrastructure_plans(
    plan_type: Optional[str] = None,
    funding_status: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[float] = 50.0,
    current_user: User = Depends(get_current_user)
):
    filter_query = {"is_active": True}
    
    if plan_type:
        filter_query["plan_type"] = plan_type
    if funding_status:
        filter_query["funding_status"] = funding_status
    
    plans = await db.infrastructure_plans.find(filter_query).to_list(1000)
    
    # Filter by location if provided
    if lat is not None and lng is not None:
        filtered_plans = []
        for plan in plans:
            plan_lat = plan["location"]["lat"]
            plan_lng = plan["location"]["lng"]
            distance = ((lat - plan_lat) ** 2 + (lng - plan_lng) ** 2) ** 0.5 * 111
            if distance <= radius:
                filtered_plans.append(plan)
        plans = filtered_plans
    
    return [InfrastructurePlan(**plan) for plan in plans]

# Purification Guides
@api_router.post("/water/purification-guides", response_model=PurificationGuide)
async def create_purification_guide(guide_data: PurificationGuideCreate, current_user: User = Depends(get_current_user)):
    guide_dict = guide_data.dict()
    guide_dict["created_by"] = current_user.id
    guide = PurificationGuide(**guide_dict)
    
    await db.purification_guides.insert_one(guide.dict())
    return guide

@api_router.get("/water/purification-guides", response_model=List[PurificationGuide])
async def get_purification_guides(
    method_type: Optional[str] = None,
    effectiveness: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    filter_query = {"is_active": True}
    
    if method_type:
        filter_query["method_type"] = method_type
    if effectiveness:
        filter_query["effectiveness"] = effectiveness
    if difficulty_level:
        filter_query["difficulty_level"] = difficulty_level
    
    guides = await db.purification_guides.find(filter_query).sort("community_rating", -1).to_list(1000)
    return [PurificationGuide(**guide) for guide in guides]

@api_router.get("/water/purification-guides/{guide_id}", response_model=PurificationGuide)
async def get_purification_guide(guide_id: str, current_user: User = Depends(get_current_user)):
    guide = await db.purification_guides.find_one({"id": guide_id, "is_active": True})
    if not guide:
        raise HTTPException(status_code=404, detail="Purification guide not found")
    
    # Increment usage count
    await db.purification_guides.update_one({"id": guide_id}, {"$inc": {"usage_count": 1}})
    
    return PurificationGuide(**guide)

# Water Alerts
@api_router.post("/water/alerts", response_model=WaterAlert)
async def create_water_alert(alert_data: WaterAlertCreate, current_user: User = Depends(get_current_user)):
    alert_dict = alert_data.dict()
    alert_dict["issued_by"] = current_user.id
    alert = WaterAlert(**alert_dict)
    
    await db.water_alerts.insert_one(alert.dict())
    return alert

@api_router.get("/water/alerts", response_model=List[WaterAlert])
async def get_water_alerts(
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    filter_query = {}
    
    if active_only:
        filter_query["active"] = True
        # Also filter out expired alerts
        filter_query["$or"] = [
            {"expires_at": {"$gte": datetime.utcnow()}},
            {"expires_at": None}
        ]
    
    if alert_type:
        filter_query["alert_type"] = alert_type
    if severity:
        filter_query["severity"] = severity
    
    alerts = await db.water_alerts.find(filter_query).sort("created_at", -1).to_list(1000)
    
    # Filter by user location if provided
    if lat is not None and lng is not None:
        filtered_alerts = []
        for alert in alerts:
            alert_lat = alert["location"]["lat"]
            alert_lng = alert["location"]["lng"]
            distance = ((lat - alert_lat) ** 2 + (lng - alert_lng) ** 2) ** 0.5 * 111
            if distance <= alert["radius_km"]:
                filtered_alerts.append(alert)
        alerts = filtered_alerts
    
    return [WaterAlert(**alert) for alert in alerts]

@api_router.put("/water/alerts/{alert_id}/verify")
async def verify_water_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    alert = await db.water_alerts.find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.water_alerts.update_one(
        {"id": alert_id},
        {"$set": {"verified": True, "verified_by": current_user.id, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Alert verified successfully"}

# Water Usage Tracking
@api_router.post("/water/usage", response_model=WaterUsage)
async def log_water_usage(usage_data: WaterUsageCreate, current_user: User = Depends(get_current_user)):
    usage_dict = usage_data.dict()
    usage_dict["user_id"] = current_user.id
    
    if not usage_dict["date"]:
        usage_dict["date"] = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate total
    total = (usage_dict["drinking_liters"] + usage_dict["cooking_liters"] + 
             usage_dict["cleaning_liters"] + usage_dict["agriculture_liters"] + 
             usage_dict["other_liters"])
    usage_dict["total_liters"] = total
    
    usage = WaterUsage(**usage_dict)
    
    # Check if usage already exists for this date, update if so
    existing = await db.water_usage.find_one({
        "user_id": current_user.id,
        "date": usage_dict["date"]
    })
    
    if existing:
        await db.water_usage.update_one(
            {"id": existing["id"]},
            {"$set": usage_dict}
        )
        return WaterUsage(**{**existing, **usage_dict})
    else:
        await db.water_usage.insert_one(usage.dict())
        return usage

@api_router.get("/water/usage", response_model=List[WaterUsage])
async def get_water_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    filter_query = {"user_id": current_user.id}
    
    if start_date:
        filter_query["date"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        if "date" in filter_query:
            filter_query["date"]["$lte"] = datetime.fromisoformat(end_date)
        else:
            filter_query["date"] = {"$lte": datetime.fromisoformat(end_date)}
    
    usage_records = await db.water_usage.find(filter_query).sort("date", -1).to_list(1000)
    return [WaterUsage(**usage) for usage in usage_records]

@api_router.get("/water/usage/stats")
async def get_water_usage_stats(current_user: User = Depends(get_current_user)):
    # Personal stats
    personal_usage = await db.water_usage.find({"user_id": current_user.id}).to_list(1000)
    
    if not personal_usage:
        return {"personal": {}, "community": {}}
    
    # Calculate personal averages
    total_days = len(personal_usage)
    total_consumption = sum(usage["total_liters"] for usage in personal_usage)
    avg_daily = total_consumption / total_days if total_days > 0 else 0
    
    # Category breakdown
    categories = {
        "drinking": sum(usage["drinking_liters"] for usage in personal_usage) / total_days,
        "cooking": sum(usage["cooking_liters"] for usage in personal_usage) / total_days,
        "cleaning": sum(usage["cleaning_liters"] for usage in personal_usage) / total_days,
        "agriculture": sum(usage["agriculture_liters"] for usage in personal_usage) / total_days,
        "other": sum(usage["other_liters"] for usage in personal_usage) / total_days
    }
    
    # Community stats (anonymized)
    all_usage = await db.water_usage.find({}).to_list(10000)
    community_total = sum(usage["total_liters"] for usage in all_usage)
    community_users = len(set(usage["user_id"] for usage in all_usage))
    community_avg = community_total / len(all_usage) if all_usage else 0
    
    return {
        "personal": {
            "daily_average": round(avg_daily, 2),
            "total_days_logged": total_days,
            "total_consumption": round(total_consumption, 2),
            "category_averages": {k: round(v, 2) for k, v in categories.items()}
        },
        "community": {
            "average_daily_per_person": round(community_avg, 2),
            "total_users_tracking": community_users,
            "total_community_consumption": round(community_total, 2)
        }
    }

# Include the router in the main app
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "GlobalHaven API is running"}

@api_router.get("/")
async def api_root():
    return {"message": "GlobalHaven API v1.0", "status": "active"}

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
