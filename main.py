from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import Cue

# --- NEW: Lifespan Context Manager ---
# This replaces @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create the database tables
    create_db_and_tables()
    yield
    # Shutdown: (We don't need to do anything here yet)

# Initialize the app with the lifespan
app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

# --- ROUTE 1: View Cues (Read) ---
@app.get("/")
async def read_root(request: Request, session: Session = Depends(get_session)):
    # Get all cues, sorted by their ID so they stay in order
    cues = session.exec(select(Cue)).all()
    return templates.TemplateResponse("index.html", {"request": request, "cues": cues})

# --- ROUTE 2: Add a Cue (Create) ---
@app.post("/cues")
async def create_cue(
    number: str = Form(...),
    description: str = Form(...),
    department: str = Form(...),
    session: Session = Depends(get_session)
):
    new_cue = Cue(number=number, description=description, department=department)
    session.add(new_cue)
    session.commit()
    return RedirectResponse(url="/", status_code=303)

# --- ROUTE 3: Activate a Cue (Update) ---
# This was likely the issue. It must be at the same indentation level as the others.
@app.get("/cues/{cue_id}/activate")
async def activate_cue(
    request: Request,  # We need 'request' for the template
    cue_id: int, 
    session: Session = Depends(get_session)
):
    # 1. Logic (Same as before)
    active_cues = session.exec(select(Cue).where(Cue.is_active == True)).all()
    for active_cue in active_cues:
        active_cue.is_active = False
        session.add(active_cue)
    
    cue_to_activate = session.get(Cue, cue_id)
    if cue_to_activate:
        cue_to_activate.is_active = True
        session.add(cue_to_activate)
    
    session.commit()
    
    # 2. Re-fetch the updated list
    cues = session.exec(select(Cue)).all()
    
    # 3. Return ONLY the table rows (we will create this template in a second)
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# --- ROUTE 4: Reset Show (Clear all active cues) ---
@app.post("/reset")
async def reset_show(
    request: Request,
    session: Session = Depends(get_session)
):
    # 1. Find all active cues and turn them off
    active_cues = session.exec(select(Cue).where(Cue.is_active == True)).all()
    for cue in active_cues:
        cue.is_active = False
        session.add(cue)
    
    session.commit()
    
    # 2. Re-fetch the clean list
    cues = session.exec(select(Cue)).all()
    
    # 3. Return the updated (empty) table rows
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})