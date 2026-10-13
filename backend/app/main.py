import csv, io, json, os, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy import create_engine, String, Float, DateTime, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from .services.solar import calculate, ASSUMPTIONS

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./3s_calculator.db")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {"sslmode": "require"}
engine = create_engine(DB_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Record(Base):
    __tablename__ = "records"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
Base.metadata.create_all(engine)

app = FastAPI(title="3S Calculator API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH"], allow_headers=["*"])

def db():
    s = SessionLocal()
    try: yield s
    finally: s.close()
def now(): return datetime.now(timezone.utc).isoformat()

class CalcRequest(BaseModel):
    monthly_bill: float = Field(gt=0, le=100_000_000)
    roof_area: float | None = Field(default=None, ge=0)
    monthly_units: float | None = Field(default=None, gt=0)
    operating_hours: float = Field(default=10, ge=1, le=24)
    state: str = Field(default="Andhra Pradesh", max_length=80)
    city: str = Field(default="", max_length=100)
    property_type: str = Field(default="", max_length=80)
    language: str = Field(default="en", pattern="^(en|te)$")
    shade: str = Field(default="unknown", max_length=40)
    lead_id: str | None = None

class LeadRequest(BaseModel):
    report_id: str | None = None
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=r"^[+0-9 ()-]{8,20}$")
    email: str | None = Field(default=None, max_length=254)
    category: str
    language: str = Field(pattern="^(en|te)$")
    state: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=100)
    consent: bool
    marketing_consent: bool = False
    business_name: str | None = Field(default=None, max_length=160)
    source: str = Field(default="website", max_length=100)

def row_json(r): return {"id": r.id, "kind": r.kind, "created_at": r.created_at.isoformat(), **json.loads(r.data)}

@app.get("/api/v1/health")
def health(): return {"status": "ok", "service": "3s-calculator", "time": now()}

@app.get("/api/v1/config/public")
def public_config():
    return {"brand": "3S Solutions", "currency": "INR", "languages": ["en", "te"], "assumption_version": ASSUMPTIONS["version"], "integrations": {"google_sheets": "unconfigured" if not os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID") else "configured", "whatsapp": "unconfigured" if not os.getenv("WHATSAPP_ACCESS_TOKEN") else "configured"}}

@app.post("/api/v1/calculations/{category}")
def create_calculation(category: str, payload: CalcRequest, session: Session = Depends(db)):
    if category not in ("residential", "commercial", "industrial"): raise HTTPException(404, "Unknown customer category")
    try: result = calculate(category, payload.monthly_bill, payload.roof_area, payload.monthly_units, payload.operating_hours, payload.language)
    except ValueError as e: raise HTTPException(422, str(e))
    calc_id = str(uuid.uuid4())
    result.update({"id": calc_id, "inputs": payload.model_dump(), "created_at": now()})
    session.add(Record(id=calc_id, kind="calculation", data=json.dumps(result)))
    if payload.lead_id:
        lead = session.get(Record, payload.lead_id)
        if not lead or lead.kind != "lead": raise HTTPException(404, "Lead not found")
        lead_data = json.loads(lead.data)
        if lead_data.get("category") != category or lead_data.get("language") != payload.language:
            raise HTTPException(422, "Calculation category and language must match the saved lead")
        lead_data.update({"report_id": calc_id, "state": payload.state, "city": payload.city, "annual_savings_inr": result["annual_savings_inr"], "capacity_kw": result["capacity_kw"], "gross_cost_inr": result["gross_cost_inr"]})
        lead.data = json.dumps(lead_data)
    session.commit()
    return result

@app.get("/api/v1/reports/{report_id}")
def get_report(report_id: str, session: Session = Depends(db)):
    r = session.get(Record, report_id)
    if not r or r.kind != "calculation": raise HTTPException(404, "Report not found")
    return row_json(r)

@app.get("/api/v1/reports/{report_id}/pdf")
def report_pdf(report_id: str, session: Session = Depends(db)):
    r = session.get(Record, report_id)
    if not r or r.kind != "calculation": raise HTTPException(404, "Report not found")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError: raise HTTPException(503, "PDF dependency is not installed")
    d = json.loads(r.data); buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("3S Calculator estimate")
    c.setFillColorRGB(0, .5, .58); c.setFont("Helvetica-Bold", 21)
    logo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "assets", "3s-solutions-logo.png"))
    if os.path.exists(logo): c.drawImage(logo, 48, 744, width=145, height=39, preserveAspectRatio=True, mask="auto")
    c.drawString(205, 754, "Solar estimate")
    c.setFillColorRGB(.15, .2, .22); c.setFont("Helvetica", 10)
    y = 710
    lines = [f"Report: {report_id}", f"Category: {d['category'].title()}", f"Monthly bill: INR {d['inputs']['monthly_bill']:,.0f}", f"Suggested capacity range: {d['capacity_kw']['low']} - {d['capacity_kw']['high']} kW", f"Annual generation: {d['annual_generation_kwh']:,} kWh", f"Estimated annual bill savings: INR {d['annual_savings_inr']:,}", f"Indicative project cost: INR {d['gross_cost_inr']:,}", f"Subsidy: not assessed; none deducted", f"Simple payback: {d['payback_years'] if d['payback_years'] else 'Not recoverable'} years", f"Carbon reduction: {d['carbon_reduction_tonnes_year']} tCO2e/year", "", "Planning estimate only. Verify site conditions, utility tariffs, export rules, project pricing and eligibility.", "No subsidy has been included. Generation depends on site irradiation, orientation, shading and system design.", f"Assumption set: {d['assumptions']['version']} | Created: {d['created_at']}"]
    for line in lines:
        if y < 75: c.showPage(); y = 744; c.setFont("Helvetica", 10)
        c.drawString(48, y, line[:120]); y -= 23
    c.save(); buf.seek(0)
    return Response(buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=3s-estimate-{report_id[:8]}.pdf"})

@app.post("/api/v1/leads")
def create_lead(payload: LeadRequest, session: Session = Depends(db)):
    if not payload.consent: raise HTTPException(422, "Contact consent is required to request a consultation")
    calc_data = None
    if payload.report_id:
        calc = session.get(Record, payload.report_id)
        if not calc or calc.kind != "calculation": raise HTTPException(404, "Calculation not found")
        calc_data = json.loads(calc.data)
        if payload.category != calc_data.get("category") or payload.language != calc_data.get("inputs", {}).get("language"):
            raise HTTPException(422, "Lead category and language must match the saved calculation")
    lead_id = str(uuid.uuid4())
    record = payload.model_dump(exclude={"consent", "marketing_consent"})
    record.update({"report_id": payload.report_id, "annual_savings_inr": calc_data["annual_savings_inr"] if calc_data else None, "capacity_kw": calc_data["capacity_kw"] if calc_data else None, "gross_cost_inr": calc_data["gross_cost_inr"] if calc_data else None, "consent_at": now(), "marketing_consent": payload.marketing_consent, "status": "New", "deliveries": {"google_sheets": "unconfigured", "whatsapp": "unconfigured"}})
    session.add(Record(id=lead_id, kind="lead", data=json.dumps(record))); session.commit()
    return {"id": lead_id, "status": "saved", "integrations": record["deliveries"]}

def require_admin(x_admin_key: str | None = Header(default=None)):
    key = os.getenv("ADMIN_API_KEY")
    if not key or not x_admin_key or x_admin_key != key: raise HTTPException(401, "Admin authentication is not configured or credentials are invalid")

@app.get("/api/v1/admin/leads", dependencies=[Depends(require_admin)])
def leads(session: Session = Depends(db), q: str = ""):
    items = session.scalars(select(Record).where(Record.kind == "lead").order_by(Record.created_at.desc())).all()
    result = [row_json(r) for r in items]
    return [x for x in result if not q or q.lower() in json.dumps(x, ensure_ascii=False).lower()]

@app.patch("/api/v1/admin/leads/{lead_id}", dependencies=[Depends(require_admin)])
def update_lead(lead_id: str, body: dict, session: Session = Depends(db)):
    r = session.get(Record, lead_id)
    if not r or r.kind != "lead": raise HTTPException(404, "Lead not found")
    d = json.loads(r.data)
    if "status" in body:
        allowed = {"New", "Contacted", "Qualified", "Consultation Scheduled", "Site Survey Completed", "Proposal Sent", "Won", "Lost", "Unqualified"}
        if body["status"] not in allowed: raise HTTPException(422, "Invalid status")
        d["status"] = body["status"]
    r.data = json.dumps(d); session.commit(); return row_json(r)

@app.get("/api/v1/admin/export.csv", dependencies=[Depends(require_admin)])
def export_csv(session: Session = Depends(db)):
    items = session.scalars(select(Record).where(Record.kind == "lead").order_by(Record.created_at.desc())).all()
    rows = [row_json(r) for r in items]
    fields = ["id", "created_at", "name", "phone", "email", "category", "language", "state", "city", "annual_savings_inr", "capacity_kw", "gross_cost_inr", "status", "marketing_consent"]
    out = io.StringIO(); w = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore"); w.writeheader()
    for row in rows:
        safe = {k: ("'" + str(v) if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v) for k, v in row.items()}
        w.writerow(safe)
    return Response("\ufeff" + out.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=3s-leads.csv"})

@app.get("/api/v1/admin/integrations/status", dependencies=[Depends(require_admin)])
def integration_status():
    return {"google_sheets": "unconfigured" if not os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID") else "credentials_present_adapter_pending", "whatsapp": "unconfigured" if not os.getenv("WHATSAPP_ACCESS_TOKEN") else "credentials_present_adapter_pending", "pabbly": "unconfigured" if not os.getenv("PABBLY_WEBHOOK_URL") else "credentials_present_adapter_pending"}

