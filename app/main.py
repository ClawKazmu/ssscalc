from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import os
import json
from dotenv import load_dotenv
import logging
from fastapi.responses import FileResponse

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ssscalc")

app = FastAPI(title="SSS Contribution Calculator", version="0.1.0")

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
def calculate(req: CalcRequest):
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
