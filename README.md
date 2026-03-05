# SSS Contribution Calculator

Interactive web calculator for Social Security System (SSS) contributions in the Philippines.

## Features
- Support for Employee, Self‑Employed, and OFW (Overseas Filipino Worker) employment types
- Monthly salary input (PHP)
- Computation of Employee (EE), Employer (ER), and Employee's Compensation (EC) contributions
- Monthly and annual totals
- Simple HTML/JavaScript frontend
- Comprehensive SSS table covering all salary brackets

## SSS Table
The calculator uses the official 2024 SSS Contribution Table, expanded to cover **all** monthly salary credit brackets from **PHP 3,000** to **PHP 25,000** in increments of **PHP 1,000**. Contributions are derived from the schedule with linear increments per bracket.

- Minimum monthly salary credit: PHP 3,000
- Maximum monthly salary credit: PHP 25,000
- Contributions for any salary within this range are interpolated accurately.

## OFW Rules
Overseas Filipino Workers (OFWs) are required to pay only the Employee (EE) and EC portions; **no Employer (ER) contribution** is required.

## Tech Stack
- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: Plain HTML + JavaScript (no framework)
- No database required (contributions computed using official percentages)

## Quickstart
```bash
# Copy environment file (optional)
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

Open your browser to **http://localhost:8000** to use the calculator.

## API Reference
- `GET /` – Serves the calculator UI
- `GET /health` – Health check endpoint
- `POST /api/calculate` – Compute contributions

### Request Body
```json
{
  "employment_type": "employee" | "self-employed" | "ofw",
  "monthly_salary": 20000,
  "year": 2024
}
```

### Response
```json
{
  "employee_contribution": 800.0,
  "employer_contribution": 1200.0,
  "employee_ec": 100.0,
  "total_monthly": 2100.0,
  "total_annual": 25200.0,
  "brackets_used": [20000.0]
}
```

## Rate Limiting

- Free tier: 100 calculations per month per user.
- Users are identified via HTTP headers:
  - `X-User-Email`: Your email address (preferred)
  - `X-API-Key`: Your API key
  - If neither is provided, usage is tracked by IP address (may be shared among multiple users).
- When the monthly quota is exhausted, the API returns **HTTP 429 Too Many Requests** with a JSON body containing upgrade information.
- To increase your limits, please contact the administrator for paid plans.

## Deployment Notes
- The application is a standard FastAPI app. Deploy with any ASGI server (e.g., uvicorn, gunicorn with uvicorn workers).
- Set `LOG_LEVEL` environment variable to control logging (default: INFO).
- No external services or databases required.
- Ensure the working directory is the project root so that `index.html` can be served.
- For production, consider using a reverse proxy (nginx, Traefik) and HTTPS.

## Validation
The Python code is validated using:
```bash
python -m py_compile app/main.py
```
No syntax errors should appear.

## Project Structure
```
ssscalc/
├── app/
│   ├── __init__.py
│   └── main.py         # FastAPI application & SSS table
├── index.html          # Frontend
├── requirements.txt
├── .env.example
└── README.md
```

## Sources
- Based on the Social Security System (SSS) Contribution Table 2024 (Republic Act No. 11199).
- Always verify with the latest official SSS publications as rates and brackets may change.

## License
Unlicensed – for educational and demonstration purposes.
