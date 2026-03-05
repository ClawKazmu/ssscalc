from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Literal
import os
import json
from dotenv import load_dotenv
import logging
from fastapi.responses import FileResponse
from datetime import datetime, timezone

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ssscalc")

app = FastAPI(title="SSS Contribution Calculator", version="0.1.0")

# Rate Limiter Implementation
class RateLimiter:
    def __init__(self):
        self.usage = {}  # {user_key: {month_key: count}}
        self.last_reset = {}  # {user_key: month_key}
    
    def get_current_month_key(self) -> str:
        now = datetime.now(timezone.utc)
        return f"{now.year}-{now.month:02d}"
    
    def check_and_increment(self, user_key: str) -> bool:
        month_key = self.get_current_month_key()
        
        if user_key not in self.usage:
            self.usage[user_key] = {}
            self.last_reset[user_key] = month_key
        
        if self.last_reset[user_key] != month_key:
            # New month, reset counter
            self.usage[user_key] = {}
            self.last_reset[user_key] = month_key
        
        current = self.usage[user_key].get(month_key, 0)
        if current >= 100:
            return False
        
        self.usage[user_key][month_key] = current + 1
        return True
    
    def get_remaining(self, user_key: str) -> int:
        month_key = self.get_current_month_key()
        count = self.usage.get(user_key, {}).get(month_key, 0)
        return max(0, 100 - count)

rate_limiter = RateLimiter()

# Rate limiting middleware to add headers
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    if hasattr(request.state, "rate_limit_remaining"):
        remaining = request.state.rate_limit_remaining
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

# Rate limiting dependency
async def rate_limit_dependency(request: Request):
    user_email = request.headers.get("X-User-Email")
    api_key = request.headers.get("X-API-Key")
    
    if user_email:
        user_key = f"email:{user_email}"
    elif api_key:
        user_key = f"apikey:{api_key}"
    else:
        client = request.client
        host = client.host if client else "unknown"
        user_key = f"ip:{host}"
    
    if not rate_limiter.check_and_increment(user_key):
        remaining = rate_limiter.get_remaining(user_key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Free tier limit of 100 calculations per month exceeded. Please upgrade for higher limits.",
                "limit": 100,
                "remaining": remaining,
                "upgrade_info": "Contact administrator for paid plans."
            }
        )
    
    request.state.rate_limit_remaining = rate_limiter.get_remaining(user_key)
    return user_key

# SSS Contribution rates (2024)
# Minimum monthly salary credit
MIN_MSC = 3000.0
# Maximum monthly salary credit for 2024
MAX_MSC = 25000.0

# Contribution percentages (total 12%)
# Employee (EE): 4.5% of MSC
# Employer (ER): 6.5% of MSC
# Employee's Compensation (EC): 1% of MSC
# These percentages are applied to the monthly salary credit (MSC)
# No lookup table needed; compute directly.

def get_rates(salary: float):
    # Clamp salary to the allowable range [MIN_MSC, MAX_MSC]
    salary = max(salary, MIN_MSC)
    salary = min(salary, MAX_MSC)
    # Compute contributions as percentages of salary
    ee = salary * 0.045
    er = salary * 0.065
    ec = salary * 0.01
    return ee, er, ec

class CalcRequest(BaseModel):
    employment_type: Literal["employee", "self-employed", "ofw"]
    monthly_salary: float
    year: int = 2024

class CalcResponse(BaseModel):
    employee_contribution: float
    employer_contribution: float
    employee_ec: float
    total_monthly: float
    total_annual: float
    brackets_used: tuple

@app.post("/api/calculate", response_model=CalcResponse)
def calculate(req: CalcRequest, user_key: str = Depends(rate_limit_dependency)):
    ee, er, ec = get_rates(req.monthly_salary)
    if req.employment_type == "employee":
        total_monthly = ee + ec
        total_annual = total_monthly * 12
    elif req.employment_type == "self-employed":
        # self-employed pays both EE and ER plus EC
        total_monthly = ee + er + ec
        total_annual = total_monthly * 12
    else:  # ofw: pays only EE and EC? Actually OFW pays only EE? We'll simplify: OFW pays EE+EC (no ER)
        total_monthly = ee + ec
        total_annual = total_monthly * 12

    return CalcResponse(
        employee_contribution=ee,
        employer_contribution=er if req.employment_type != "ofw" else 0,
        employee_ec=ec,
        total_monthly=total_monthly,
        total_annual=total_annual,
        brackets_used=(req.monthly_salary,)
    )

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ssscalc"}
