from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, func
from database import create_db_and_tables, get_session
from models import Cue, Show  # Import Show as well

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- LOBBY ROUTES (Show Management) ---

@app.get("/")
async def list_shows(
    request: Request, 
    session: Session = Depends(get_session)
):
    """The new Homepage: Lists all shows."""
    shows = session.exec(select(Show)).all()
    return templates.TemplateResponse("shows.html", {"request": request, "shows": shows})

@app.post("/shows")
async def create_show(
    name: str = Form(...), 
    description: str = Form(None), 
    session: Session = Depends(get_session)
):
    """Create a new show bucket."""
    new_show = Show(name=name, description=description)
    session.add(new_show)
    session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/shows/{show_id}/delete")
async def delete_show(
    show_id: int, 
    session: Session = Depends(get_session)
):
    """Delete a show and its cues."""
    show = session.get(Show, show_id)
    if show:
        # Note: In a real app, use cascade delete. Here we rely on SQLModel relationships or manual cleanup.
        # For simplicity, we just delete the show object.
        session.delete(show)
        session.commit()
    return RedirectResponse(url="/", status_code=303)


# --- SHOW CONTROL ROUTES (The Actual App) ---

@app.get("/shows/{show_id}")
async def enter_show(
    request: Request, 
    show_id: int, 
    session: Session = Depends(get_session)
):
    """
    This replaces the old root '/'. 
    It loads the specific show and its cues.
    """
    show = session.get(Show, show_id)
    if not show:
        return RedirectResponse(url="/")
        
    # Get cues ONLY for this show, sorted by sequence
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "cues": cues, 
        "show": show  # Pass the show object so we can use show.id in templates
    })

# --- CUE MANAGEMENT (Updated to use show_id) ---

@app.post("/shows/{show_id}/cues")
async def create_cue(
    show_id: int,
    number: str = Form(...),
    description: str = Form(...),
    department: str = Form(...),
    trigger: str = Form(None),
    page_num: str = Form(None),
    session: Session = Depends(get_session)
):
    # Calculate sequence relative to THIS show
    # SELECT MAX(sequence) FROM cue WHERE show_id = X
    max_seq = session.exec(
        select(func.max(Cue.sequence)).where(Cue.show_id == show_id)
    ).one()
    
    new_seq = (max_seq or 0) + 1
    
    new_cue = Cue(
        number=number, 
        description=description, 
        department=department,
        trigger=trigger,
        page_num=page_num,
        sequence=new_seq, 
        show_id=show_id
    )
    session.add(new_cue)
    session.commit()
    return RedirectResponse(url=f"/shows/{show_id}", status_code=303)

# ... (Previous Action Routes: Activate, Reset, Delete, Reorder) ...
# We need to update these to redirect correctly or filter correctly.

# 1. Activate (Logic doesn't change much, but we need to ensure we return the right list)
@app.get("/cues/{cue_id}/activate")
async def activate_cue(
    request: Request, 
    cue_id: int, 
    session: Session = Depends(get_session)
):
    # Get the cue to find out which show it belongs to
    cue = session.get(Cue, cue_id)
    if not cue: return Response(status_code=404)
    show_id = cue.show_id

    # Deactivate all cues IN THIS SHOW
    active_cues = session.exec(select(Cue).where(Cue.show_id == show_id).where(Cue.is_active == True)).all()
    for c in active_cues:
        c.is_active = False
        session.add(c)
    
    # Activate target
    cue.is_active = True
    session.add(cue)
    session.commit()
    
    # Return updated list for THIS show
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# 2. Reset (Needs show_id)
@app.post("/shows/{show_id}/reset")
async def reset_show(
    request: Request, 
    show_id: int, 
    session: Session = Depends(get_session)
):
    active_cues = session.exec(select(Cue).where(Cue.show_id == show_id).where(Cue.is_active == True)).all()
    for c in active_cues:
        c.is_active = False
        session.add(c)
    session.commit()
    
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# 3. Delete (Same as before, logic is ID based so it's safe)
@app.delete("/cues/{cue_id}")
async def delete_cue(
    cue_id: int, 
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    if cue:
        session.delete(cue)
        session.commit()
    return Response(status_code=200)

# 4. Edit Routes (Same as before)
@app.get("/cues/{cue_id}/edit")
async def get_edit_form(
    request: Request, 
    cue_id: int, 
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row_edit.html", {"request": request, "cue": cue})

@app.get("/cues/{cue_id}")
async def get_single_cue(
    request: Request, 
    cue_id: int, 
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row.html", {"request": request, "cue": cue})

@app.put("/cues/{cue_id}")
async def update_cue(
    request: Request, 
    cue_id: int, 
    number: str = Form(...), 
    department: str = Form(...), 
    description: str = Form(...),
    trigger: str = Form(None),
    page_num: str = Form(None),
    session: Session = Depends(get_session)
):
    cue = session.get(Cue, cue_id)
    if cue:
        cue.number = number
        cue.department = department
        cue.description = description
        cue.trigger = trigger
        cue.page_num = page_num
        session.add(cue)
        session.commit()
        session.refresh(cue)
    return templates.TemplateResponse("partials/cue_row.html", {"request": request, "cue": cue})

# 5. Reorder (Needs to return correct list)
@app.post("/reorder")
async def reorder_cues(
    request: Request, 
    ids: List[int] = Form(...), 
    session: Session = Depends(get_session)
):
    show_id = None
    for index, cue_id in enumerate(ids):
        cue = session.get(Cue, cue_id)
        if cue:
            cue.sequence = index + 1
            if show_id is None: show_id = cue.show_id # Capture show ID from first cue
            session.add(cue)
    session.commit()
    
    # Return list for the captured show_id
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# --- HUD ROUTES ---

@app.get("/shows/{show_id}/hud_content")
async def get_hud_content(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    if not cues:
        return "No cues found"

    # Default variables
    current_cue = None
    prev_cue = None
    next_cue = None
    curr_global = "-"
    prev_global = None
    next_global = None
    
    # LOGIC BRANCHING
    if show.status == "pre":
        # PRE-SHOW: Center=PRE, Next=Cue 1
        curr_global = "PRE"
        next_global = 1
        next_cue = cues[0]

    elif show.status == "post":
        # POST-SHOW: Center=END, Prev=Last Cue, Next=PRE
        curr_global = "END"
        prev_global = len(cues)
        prev_cue = cues[-1]
        next_global = "PRE" 

    elif show.status == "running":
        # NORMAL RUNNING
        active_index = next((i for i, c in enumerate(cues) if c.is_active), 0)
        current_cue = cues[active_index]
        curr_global = active_index + 1
        
        if active_index > 0:
            prev_cue = cues[active_index - 1]
            prev_global = active_index
            
        if active_index < len(cues) - 1:
            next_cue = cues[active_index + 1]
            next_global = active_index + 2
        else:
            # Active is Last Cue -> Next is END
            next_global = "END"

    return templates.TemplateResponse("partials/hud_content.html", {
        "request": {},
        "current_cue": current_cue,
        "prev_cue": prev_cue,
        "next_cue": next_cue,
        "curr_global": curr_global,
        "prev_global": prev_global,
        "next_global": next_global,
        "show_name": show.name,
        "status": show.status # Pass status to template
    })
    
@app.post("/shows/{show_id}/next_cue")
async def advance_cue(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    if not show or not cues:
        return Response(status_code=200)

    # 1. Handle PRE -> START
    if show.status == "pre":
        show.status = "running"
        cues[0].is_active = True
        session.add(show)
        session.add(cues[0])
        session.commit()
        return Response(status_code=200)

    # 2. Handle POST -> PRE (Loop)
    if show.status == "post":
        show.status = "pre"
        session.add(show)
        session.commit()
        return Response(status_code=200)

    # 3. Handle RUNNING Logic
    if show.status == "running":
        active_index = next((i for i, c in enumerate(cues) if c.is_active), -1)
        
        # If we are somehow running but nothing is active, reset to pre
        if active_index == -1:
            show.status = "pre"
            session.add(show)
            session.commit()
            return Response(status_code=200)

        # Deactivate current
        cues[active_index].is_active = False
        session.add(cues[active_index])

        # Check if Last Cue
        if active_index == len(cues) - 1:
            # Go to POST
            show.status = "post"
            session.add(show)
        else:
            # Go to Next
            cues[active_index + 1].is_active = True
            session.add(cues[active_index + 1])
        
        session.commit()
        return Response(status_code=200)


@app.post("/shows/{show_id}/prev_cue")
async def regress_cue(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    if not show or not cues:
        return Response(status_code=200)

    # 1. Handle PRE -> POST (Loop Back)
    if show.status == "pre":
        show.status = "post"
        session.add(show)
        session.commit()
        return Response(status_code=200)

    # 2. Handle POST -> LAST CUE
    if show.status == "post":
        show.status = "running"
        cues[-1].is_active = True # Activate last cue
        session.add(show)
        session.add(cues[-1])
        session.commit()
        return Response(status_code=200)

    # 3. Handle RUNNING Logic
    if show.status == "running":
        active_index = next((i for i, c in enumerate(cues) if c.is_active), -1)
        
        if active_index > 0:
            # Normal Step Back
            cues[active_index].is_active = False
            cues[active_index - 1].is_active = True
            session.add(cues[active_index])
            session.add(cues[active_index - 1])
        elif active_index == 0:
            # First Cue -> PRE
            cues[0].is_active = False
            show.status = "pre"
            session.add(cues[0])
            session.add(show)
            
        session.commit()
        return Response(status_code=200)