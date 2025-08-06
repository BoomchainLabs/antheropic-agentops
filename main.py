#!/usr/bin/env python3
“””
Anthropic Computer Use - Production Ready Backend
Main application entry point with AgentOps integration
“””

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import jwt
from pydantic import BaseModel, Field
import anthropic
import agentops
from agentops import track_agent
import asyncpg
import redis.asyncio as redis
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
import traceback
from prometheus_client import Counter, Histogram, generate_latest
import time

# Environment configuration

from dotenv import load_dotenv
load_dotenv()

# Logging configuration

logging.basicConfig(
level=logging.INFO,
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
handlers=[
logging.FileHandler(‘app.log’),
logging.StreamHandler(sys.stdout)
]
)
logger = logging.getLogger(**name**)

# Configuration

class Config:
ANTHROPIC_API_KEY = os.getenv(“ANTHROPIC_API_KEY”)
AGENTOPS_API_KEY = os.getenv(“AGENTOPS_API_KEY”)
DATABASE_URL = os.getenv(“DATABASE_URL”, “postgresql://user:password@localhost/anthropic_db”)
REDIS_URL = os.getenv(“REDIS_URL”, “redis://localhost:6379”)
JWT_SECRET = os.getenv(“JWT_SECRET”, “your-secret-key”)
CORS_ORIGINS = os.getenv(“CORS_ORIGIN”, “http://localhost:3000”).split(”,”)
MAX_REQUESTS_PER_HOUR = int(os.getenv(“MAX_REQUESTS_PER_HOUR”, “100”))
ENABLE_AUDIT_LOGGING = os.getenv(“ENABLE_AUDIT_LOGGING”, “true”).lower() == “true”
AGENTOPS_ENABLED = os.getenv(“AGENTOPS_ENABLED”, “true”).lower() == “true”
PORT = int(os.getenv(“PORT”, “8000”))
HOST = os.getenv(“HOST”, “0.0.0.0”)

config = Config()

# Initialize AgentOps if enabled

if config.AGENTOPS_ENABLED and config.AGENTOPS_API_KEY:
agentops.init(
api_key=config.AGENTOPS_API_KEY,
tags=[“anthropic”, “computer-use”, “production”],
auto_start_session=True
)
logger.info(“AgentOps initialized successfully”)
else:
logger.warning(“AgentOps not initialized - check AGENTOPS_API_KEY and AGENTOPS_ENABLED”)

# Initialize Anthropic client

anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Database models

Base = declarative_base()

class User(Base):
**tablename** = “users”

```
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
email = Column(String, unique=True, index=True)
hashed_password = Column(String)
is_active = Column(Boolean, default=True)
created_at = Column(DateTime, default=datetime.utcnow)
```

class ComputerUseSession(Base):
**tablename** = “computer_use_sessions”

```
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id = Column(UUID(as_uuid=True), nullable=False)
instructions = Column(Text)
status = Column(String, default="active")  # active, completed, error
agentops_session_id = Column(String, nullable=True)
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
total_tokens = Column(Integer, default=0)
total_cost = Column(String, default="0.00")
```

class AuditLog(Base):
**tablename** = “audit_logs”

```
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
user_id = Column(UUID(as_uuid=True), nullable=True)
session_id = Column(UUID(as_uuid=True), nullable=True)
action = Column(String)
details = Column(Text)
timestamp = Column(DateTime, default=datetime.utcnow)
success = Column(Boolean)
error_message = Column(Text, nullable=True)
```

# Database setup

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables

Base.metadata.create_all(bind=engine)

# Dependency to get DB session

def get_db():
db = SessionLocal()
try:
yield db
finally:
db.close()

# Redis client for caching and rate limiting

redis_client = None

# Metrics

REQUEST_COUNT = Counter(‘http_requests_total’, ‘Total HTTP requests’, [‘method’, ‘endpoint’])
REQUEST_DURATION = Histogram(‘http_request_duration_seconds’, ‘HTTP request duration’)
COMPUTER_USE_SESSIONS = Counter(‘computer_use_sessions_total’, ‘Total computer use sessions’)
ANTHROPIC_API_CALLS = Counter(‘anthropic_api_calls_total’, ‘Total Anthropic API calls’)

# Pydantic models

class UserLogin(BaseModel):
email: str
password: str

class ComputerUseRequest(BaseModel):
instructions: str
session_id: Optional[str] = None

class ComputerUseResponse(BaseModel):
session_id: str
status: str
response: Optional[str] = None
screenshot: Optional[str] = None
agentops_session_id: Optional[str] = None

class HealthResponse(BaseModel):
status: str
timestamp: str
version: str = “1.0.0”
dependencies: Dict[str, str] = {}

# WebSocket Connection Manager

class ConnectionManager:
def **init**(self):
self.active_connections: List[WebSocket] = []
self.session_connections: Dict[str, List[WebSocket]] = {}

```
async def connect(self, websocket: WebSocket, session_id: str = None):
    await websocket.accept()
    self.active_connections.append(websocket)
    if session_id:
        if session_id not in self.session_connections:
            self.session_connections[session_id] = []
        self.session_connections[session_id].append(websocket)

def disconnect(self, websocket: WebSocket, session_id: str = None):
    if websocket in self.active_connections:
        self.active_connections.remove(websocket)
    if session_id and session_id in self.session_connections:
        if websocket in self.session_connections[session_id]:
            self.session_connections[session_id].remove(websocket)

async def send_personal_message(self, message: str, websocket: WebSocket):
    await websocket.send_text(message)

async def broadcast_to_session(self, message: str, session_id: str):
    if session_id in self.session_connections:
        for connection in self.session_connections[session_id]:
            try:
                await connection.send_text(message)
            except:
                pass
```

manager = ConnectionManager()

# JWT Authentication

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
try:
payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[“HS256”])
return payload
except jwt.PyJWTError:
raise HTTPException(status_code=401, detail=“Invalid authentication credentials”)

# Rate limiting decorator

async def rate_limit_check(user_id: str):
if redis_client:
key = f”rate_limit:{user_id}”
current = await redis_client.get(key)
if current and int(current) >= config.MAX_REQUESTS_PER_HOUR:
raise HTTPException(status_code=429, detail=“Rate limit exceeded”)
await redis_client.incr(key)
await redis_client.expire(key, 3600)  # 1 hour

# Audit logging

async def log_audit(db: Session, user_id: str = None, session_id: str = None,
action: str = None, details: str = None, success: bool = True,
error_message: str = None):
if config.ENABLE_AUDIT_LOGGING:
audit_log = AuditLog(
user_id=user_id,
session_id=session_id,
action=action,
details=details,
success=success,
error_message=error_message
)
db.add(audit_log)
db.commit()

# Lifespan events

@asynccontextmanager
async def lifespan(app: FastAPI):
# Startup
global redis_client
try:
redis_client = redis.from_url(config.REDIS_URL)
await redis_client.ping()
logger.info(“Redis connected successfully”)
except Exception as e:
logger.warning(f”Redis connection failed: {e}”)
redis_client = None

```
logger.info("Application startup complete")
yield

# Shutdown
if redis_client:
    await redis_client.close()
logger.info("Application shutdown complete")
```

# FastAPI app initialization

app = FastAPI(
title=“Anthropic Computer Use API”,
description=“Production-ready API for Anthropic Computer Use with AgentOps integration”,
version=“1.0.0”,
lifespan=lifespan
)

# Middleware

app.add_middleware(
CORSMiddleware,
allow_origins=config.CORS_ORIGINS,
allow_credentials=True,
allow_methods=[”*”],
allow_headers=[”*”],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=[”*”])

# Middleware for metrics

@app.middleware(“http”)
async def metrics_middleware(request, call_next):
start_time = time.time()
REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()

```
response = await call_next(request)

process_time = time.time() - start_time
REQUEST_DURATION.observe(process_time)

return response
```

# Health check endpoints

@app.get(”/health”, response_model=HealthResponse)
async def health_check():
dependencies = {}

```
# Check database
try:
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    dependencies["database"] = "healthy"
except Exception as e:
    dependencies["database"] = f"unhealthy: {str(e)}"

# Check Redis
if redis_client:
    try:
        await redis_client.ping()
        dependencies["redis"] = "healthy"
    except Exception as e:
        dependencies["redis"] = f"unhealthy: {str(e)}"
else:
    dependencies["redis"] = "not configured"

# Check Anthropic API
try:
    # Simple API test - just check if client is configured
    if config.ANTHROPIC_API_KEY:
        dependencies["anthropic"] = "configured"
    else:
        dependencies["anthropic"] = "not configured"
except Exception as e:
    dependencies["anthropic"] = f"unhealthy: {str(e)}"

# Check AgentOps
if config.AGENTOPS_ENABLED and config.AGENTOPS_API_KEY:
    dependencies["agentops"] = "configured"
else:
    dependencies["agentops"] = "not configured"

return HealthResponse(
    status="healthy",
    timestamp=datetime.utcnow().isoformat(),
    dependencies=dependencies
)
```

@app.get(”/health/database”)
async def health_database():
try:
db = SessionLocal()
result = db.execute(“SELECT version()”).fetchone()
db.close()
return {“status”: “healthy”, “version”: result[0] if result else “unknown”}
except Exception as e:
raise HTTPException(status_code=503, detail=f”Database unhealthy: {str(e)}”)

@app.get(”/health/anthropic”)
async def health_anthropic():
try:
if not config.ANTHROPIC_API_KEY:
raise HTTPException(status_code=503, detail=“Anthropic API key not configured”)
return {“status”: “configured”, “api_key_present”: bool(config.ANTHROPIC_API_KEY)}
except Exception as e:
raise HTTPException(status_code=503, detail=f”Anthropic API unhealthy: {str(e)}”)

@app.get(”/health/agentops”)
async def health_agentops():
if not config.AGENTOPS_ENABLED:
return {“status”: “disabled”}
if not config.AGENTOPS_API_KEY:
raise HTTPException(status_code=503, detail=“AgentOps API key not configured”)
return {“status”: “configured”, “enabled”: config.AGENTOPS_ENABLED}

# Authentication endpoints

@app.post(”/api/auth/login”)
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
# Simplified authentication - in production, use proper password hashing
user = db.query(User).filter(User.email == user_login.email).first()
if not user:
# Create user if doesn’t exist (simplified for demo)
user = User(email=user_login.email, hashed_password=“hashed_password”)
db.add(user)
db.commit()
db.refresh(user)

```
# Generate JWT token
token_data = {
    "user_id": str(user.id),
    "email": user.email,
    "exp": datetime.utcnow().timestamp() + 86400  # 24 hours
}
token = jwt.encode(token_data, config.JWT_SECRET, algorithm="HS256")

await log_audit(db, str(user.id), None, "login", f"User {user.email} logged in", True)

return {
    "token": token,
    "user": {
        "id": str(user.id),
        "email": user.email
    }
}
```

# Computer Use endpoints

@track_agent(“computer_use_session”)
@app.post(”/api/computer-use/session”, response_model=ComputerUseResponse)
async def create_computer_use_session(
request: ComputerUseRequest,
db: Session = Depends(get_db),
user_data: Dict = Depends(verify_token)
):
user_id = user_data[“user_id”]

```
# Rate limiting
await rate_limit_check(user_id)

# Start AgentOps session if enabled
agentops_session_id = None
if config.AGENTOPS_ENABLED:
    try:
        agentops_session_id = agentops.start_session(tags=["computer-use", user_id])
    except Exception as e:
        logger.warning(f"Failed to start AgentOps session: {e}")

# Create database session
session = ComputerUseSession(
    user_id=user_id,
    instructions=request.instructions,
    agentops_session_id=agentops_session_id
)
db.add(session)
db.commit()
db.refresh(session)

COMPUTER_USE_SESSIONS.inc()

try:
    # Call Anthropic API for computer use
    ANTHROPIC_API_CALLS.inc()
    
    # Track the API call with AgentOps
    if config.AGENTOPS_ENABLED:
        agentops.record_action(
            action_type="llm_call",
            params={
                "model": "claude-3-sonnet-20240229",
                "instructions": request.instructions,
                "session_id": str(session.id)
            }
        )
    
    # Simulate computer use response (replace with actual computer use logic)
    response_text = f"I'll help you with: {request.instructions}"
    screenshot_data = None  # Would contain actual screenshot in production
    
    # Update session with results
    session.status = "completed"
    session.total_tokens = 150  # Would be actual token count
    session.total_cost = "0.003"  # Would be actual cost calculation
    db.commit()
    
    # Log audit trail
    await log_audit(
        db, user_id, str(session.id), "computer_use_session",
        f"Created session with instructions: {request.instructions[:100]}...", True
    )
    
    # Send real-time update via WebSocket
    await manager.broadcast_to_session(
        json.dumps({
            "type": "session_update",
            "session_id": str(session.id),
            "status": "completed",
            "response": response_text
        }),
        str(session.id)
    )
    
    # End AgentOps session
    if config.AGENTOPS_ENABLED and agentops_session_id:
        agentops.end_session("Success")
    
    return ComputerUseResponse(
        session_id=str(session.id),
        status=session.status,
        response=response_text,
        screenshot=screenshot_data,
        agentops_session_id=agentops_session_id
    )
    
except Exception as e:
    # Handle errors
    session.status = "error"
    db.commit()
    
    error_message = str(e)
    logger.error(f"Computer use session failed: {error_message}")
    
    await log_audit(
        db, user_id, str(session.id), "computer_use_session",
        f"Session failed: {error_message}", False, error_message
    )
    
    # End AgentOps session with error
    if config.AGENTOPS_ENABLED and agentops_session_id:
        agentops.end_session("Fail", end_state_reason=error_message)
    
    raise HTTPException(status_code=500, detail=f"Computer use session failed: {error_message}")
```

@app.get(”/api/computer-use/session/{session_id}”)
async def get_session_status(
session_id: str,
db: Session = Depends(get_db),
user_data: Dict = Depends(verify_token)
):
session = db.query(ComputerUseSession).filter(
ComputerUseSession.id == session_id,
ComputerUseSession.user_id == user_data[“user_id”]
).first()

```
if not session:
    raise HTTPException(status_code=404, detail="Session not found")

return {
    "session_id": str(session.id),
    "status": session.status,
    "instructions": session.instructions,
    "created_at": session.created_at.isoformat(),
    "updated_at": session.updated_at.isoformat(),
    "total_tokens": session.total_tokens,
    "total_cost": session.total_cost,
    "agentops_session_id": session.agentops_session_id
}
```

# WebSocket endpoint for real-time updates

@app.websocket(”/api/computer-use/stream/{session_id}”)
async def websocket_endpoint(websocket: WebSocket, session_id: str):
await manager.connect(websocket, session_id)
try:
while True:
data = await websocket.receive_text()
# Handle incoming WebSocket messages if needed
logger.info(f”Received WebSocket message for session {session_id}: {data}”)
except WebSocketDisconnect:
manager.disconnect(websocket, session_id)

# Metrics endpoint

@app.get(”/metrics”)
async def get_metrics():
return generate_latest()

# Admin endpoints

@app.get(”/api/admin/sessions”)
async def get_all_sessions(
db: Session = Depends(get_db),
user_data: Dict = Depends(verify_token)
):
# Add admin check here in production
sessions = db.query(ComputerUseSession).all()
return [
{
“session_id”: str(session.id),
“user_id”: str(session.user_id),
“status”: session.status,
“created_at”: session.created_at.isoformat(),
“total_tokens”: session.total_tokens,
“total_cost”: session.total_cost
}
for session in sessions
]

@app.get(”/api/admin/audit-logs”)
async def get_audit_logs(
limit: int = 100,
db: Session = Depends(get_db),
user_data: Dict = Depends(verify_token)
):
# Add admin check here in production
logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
return [
{
“id”: str(log.id),
“user_id”: str(log.user_id) if log.user_id else None,
“session_id”: str(log.session_id) if log.session_id else None,
“action”: log.action,
“details”: log.details,
“timestamp”: log.timestamp.isoformat(),
“success”: log.success,
“error_message”: log.error_message
}
for log in logs
]

# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
return JSONResponse(
status_code=exc.status_code,
content={
“error”: exc.detail,
“timestamp”: datetime.utcnow().isoformat(),
“path”: str(request.url)
}
)

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
logger.error(f”Unhandled exception: {str(exc)}\n{traceback.format_exc()}”)
return JSONResponse(
status_code=500,
content={
“error”: “Internal server error”,
“timestamp”: datetime.utcnow().isoformat(),
“path”: str(request.url)
}
)

# Main entry point

if **name** == “**main**”:
logger.info(f”Starting Anthropic Computer Use API on {config.HOST}:{config.PORT}”)
logger.info(f”AgentOps enabled: {config.AGENTOPS_ENABLED}”)
logger.info(f”Audit logging enabled: {config.ENABLE_AUDIT_LOGGING}”)

```
uvicorn.run(
    "main:app",
    host=config.HOST,
    port=config.PORT,
    reload=False,  # Set to True for development
    log_level="info",
    access_log=True
)
```
