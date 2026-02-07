from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, func
from database import create_db_and_tables, get_session
from models import Cue
from typing import List

# --- ROUTE 0: Lifespan Context Manager ---
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
    # ORDER BY sequence
    cues = session.exec(select(Cue).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("index.html", {"request": request, "cues": cues})

# --- ROUTE 2: Add a Cue (Create) ---
@app.post("/cues")
async def create_cue(
    number: str = Form(...),
    description: str = Form(...),
    department: str = Form(...),
    session: Session = Depends(get_session)
):
    # 1. Find the highest current sequence number
    # "SELECT MAX(sequence) FROM cue"
    max_seq = session.exec(select(func.max(Cue.sequence))).one()
    
    # If the table is empty, start at 1. Otherwise, add 1 to the max.
    new_seq = (max_seq or 0) + 1
    
    # 2. Create the cue with this sequence number
    new_cue = Cue(
        number=number, 
        description=description, 
        department=department,
        sequence=new_seq  # <--- HERE
    )
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
    active_cues = session.exec(select(Cue).order_by(Cue.sequence).where(Cue.is_active == True)).all()
    for active_cue in active_cues:
        active_cue.is_active = False
        session.add(active_cue)
    
    cue_to_activate = session.get(Cue, cue_id)
    if cue_to_activate:
        cue_to_activate.is_active = True
        session.add(cue_to_activate)
    
    session.commit()
    
    # 2. Re-fetch the updated list
    cues = session.exec(select(Cue).order_by(Cue.sequence)).all()
    
    # 3. Return ONLY the table rows (we will create this template in a second)
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# --- ROUTE 4: Reset Show (Clear all active cues) ---
@app.post("/reset")
async def reset_show(
    request: Request,
    session: Session = Depends(get_session)
):
    # 1. Find all active cues and turn them off
    active_cues = session.exec(select(Cue).order_by(Cue.sequence).where(Cue.is_active == True)).all()
    for cue in active_cues:
        cue.is_active = False
        session.add(cue)
    
    session.commit()
    
    # 2. Re-fetch the clean list
    cues = session.exec(select(Cue).order_by(Cue.sequence)).all()
    
    # 3. Return the updated (empty) table rows
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# --- ROUTE 5: Delete a Cue ---
@app.delete("/cues/{cue_id}")
async def delete_cue(
    cue_id: int,
    session: Session = Depends(get_session)
):
    # 1. Find the cue
    cue = session.get(Cue, cue_id)
    
    # 2. Delete it if it exists
    if cue:
        session.delete(cue)
        session.commit()
    
    # 3. Return an empty response. 
    # HTMX will swap the target with "nothing", effectively removing it.
    return Response(status_code=200)

# --- ROUTES 6-8: Inline Editing ---

# 1. Get the Edit Form
@app.get("/cues/{cue_id}/edit")
async def get_edit_form(
    request: Request,
    cue_id: int,
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row_edit.html", {"request": request, "cue": cue})

# 2. Cancel Edit (Get Single Read-Only Row)
@app.get("/cues/{cue_id}")
async def get_single_cue(
    request: Request,
    cue_id: int,
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row.html", {"request": request, "cue": cue})

# 3. Save Changes (Update)
@app.put("/cues/{cue_id}")
async def update_cue(
    request: Request,
    cue_id: int,
    number: str = Form(...),
    department: str = Form(...),
    description: str = Form(...),
    session: Session = Depends(get_session)
):
    # Find the cue
    cue = session.get(Cue, cue_id)
    if cue:
        # Update fields
        cue.number = number
        cue.department = department
        cue.description = description
        session.add(cue)
        session.commit()
        session.refresh(cue) # Refresh to get the latest data
    
    # Return the normal row (Read Mode) with the new data
    return templates.TemplateResponse("partials/cue_row.html", {"request": request, "cue": cue})

# --- ROUTE 9: Reorder Cues ---
@app.post("/reorder")
async def reorder_cues(
    request: Request,
    ids: List[int] = Form(...),  # FastAPI automatically parses the list of IDs
    session: Session = Depends(get_session)
):
    # 1. Loop through the IDs in the order they were sent
    for index, cue_id in enumerate(ids):
        cue = session.get(Cue, cue_id)
        if cue:
            cue.sequence = index + 1  # Update sequence (1, 2, 3...)
            session.add(cue)
    
    session.commit()
    
    # 2. Return the sorted list
    cues = session.exec(select(Cue).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})