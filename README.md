# SSS Contribution Calculator

Interactive web calculator for Social Security System (SSS) contributions in the Philippines.

## Features (MVP)
- Employee vs self‑employed selection
- Monthly income input
- Compute EE, ER, EC contributions
- Monthly remittance total
- Printable schedule

## Tech
- FastAPI backend + simple HTML/JS frontend (or Next.js)
- No database needed (static SSS tables encoded in JSON)

## Quickstart
```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://localhost:8000 for UI.

## API
- `GET /` – UI (or API info)
- `POST /api/calculate` – compute contributions

Input:
```json
{
  "employment_type": "employee" | "self-employed" | "ofw",
  "monthly_salary": 20000,
  "year": 2024
}
```

Output:
```json
{
  "employee_contribution": 800,
  "employer_contribution": 1200,
  "employee_ec": 100,
  "total_monthly": 2100,
  "total_annual": 25200
}
```

## Sources
- SSS Contribution Table 2024 (official)

## Project status
MVP in development. SSS table encoded in `sss_table.json`.
