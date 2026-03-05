from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import os
import json
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ssscalc")

app = FastAPI(title="SSS Contribution Calculator", version="0.1.0")

# Simplified SSS contribution table for 2024 (Employee/Employer/EC)
# Ranges are monthly salary credit. Values in PHP.
# Source: SSS Contribution Table (2024)
SSS_TABLE = [
    # (min, max, ee, er, ec)
    (0, 3000, 135, 195, 30),
    (3000, 5000, 180, 270, 45),
    (5000, 7000, 225, 337.5, 56.25),
    (7000, 9000, 270, 405, 67.5),
    (9000, 11000, 315, 472.5, 78.75),
    (11000, 13000, 360, 540, 90),
    (13000, 15000, 405, 607.5, 101.25),
    (15000, 17000, 450, 675, 112.5),
    (17000, 19000, 495, 742.5, 123.75),
    (19000, 21000, 540, 810, 135),
    (21000, 23000, 585, 877.5, 146.25),
    (23000, 25000, 630, 945, 157.5),
    (25000, 27000, 675, 1012.5, 168.75),
    (27000, 29000, 720, 1080, 180),
    (29000, 31000, 765, 1147.5, 191.25),
    (31000, 33000, 810, 1215, 202.5),
    (33000, 35000, 855, 1282.5, 213.75),
    (35000, 37000, 900, 1350, 225),
    (37000, 39000, 945, 1417.5, 236.25),
    (39000, 41000, 990, 1485, 247.5),
    (41000, 43000, 1035, 1552.5, 258.75),
    (43000, 45000, 1080, 1620, 270),
    (45000, 47000, 1125, 1687.5, 281.25),
    (47000, 49000, 1170, 1755, 292.5),
    (49000, 50000, 1215, 1822.5, 303.75),
]

def get_rates(salary: float):
    # find bracket where salary >= min and < max, or top bracket
    for min_s, max_s, ee, er, ec in SSS_TABLE:
        if min_s <= salary < max_s:
            return ee, er, ec
    # if above max, use last bracket
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
def health():
    return {"status": "ok", "service": "ssscalc"}
