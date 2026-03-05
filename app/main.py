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

# SSS Contribution Table configuration for 2024
# Minimum monthly salary credit
MIN_MSC = 3000.0
# Maximum monthly salary credit for 2024 (per official schedule)
MAX_MSC = 25000.0
STEP = 1000.0

# Base contribution amounts for MIN_MSC (3000)
BASE_EE = 135.0
BASE_ER = 195.0
BASE_EC = 30.0

# Incremental contributions per STEP (1000 increase in MSC)
INCR_EE = 22.5
INCR_ER = 37.5
INCR_EC = 7.5

# Generate the full SSS table covering all brackets from MIN_MSC to MAX_MSC inclusive.
# Each entry is (min_salary, max_salary, ee, er, ec) with half-open interval [min, max)
SSS_TABLE = []
num_steps = int((MAX_MSC - MIN_MSC) / STEP) + 1
for i in range(num_steps):
    msc = MIN_MSC + i * STEP
    ee = BASE_EE + i * INCR_EE
    er = BASE_ER + i * INCR_ER
    ec = BASE_EC + i * INCR_EC
    SSS_TABLE.append((msc, msc + STEP, ee, er, ec))

def get_rates(salary: float):
    # Clamp salary to the allowable range [MIN_MSC, MAX_MSC]
    salary = max(salary, MIN_MSC)
    salary = min(salary, MAX_MSC)
    # Find bracket where salary >= min and < max
    for min_s, max_s, ee, er, ec in SSS_TABLE:
        if min_s <= salary < max_s:
            return ee, er, ec
    # Fallback: should not happen if table covers up to MAX_MSC, but return last if needed
    return SSS_TABLE[-1][2], SSS_TABLE[-1][3], SSS_TABLE[-1][4]

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
