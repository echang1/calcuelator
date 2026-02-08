from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, func
from database import create_db_and_tables, get_session
from models import Cue, Show, StageElement, ElementTransition

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- LOBBY ROUTES ---

@app.get("/")
async def list_shows(request: Request, session: Session = Depends(get_session)):
    shows = session.exec(select(Show)).all()
    return templates.TemplateResponse("shows.html", {"request": request, "shows": shows})

@app.post("/shows")
async def create_show(name: str = Form(...), description: str = Form(None), session: Session = Depends(get_session)):
    new_show = Show(name=name, description=description)
    session.add(new_show)
    session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/shows/{show_id}/delete")
async def delete_show(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    if show:
        session.delete(show)
        session.commit()
    return RedirectResponse(url="/", status_code=303)

# --- SHOW CONTROL ROUTES ---

@app.get("/shows/{show_id}")
async def enter_show(request: Request, show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    if not show: return RedirectResponse(url="/")
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("index.html", {"request": request, "cues": cues, "show": show})

# --- INVENTORY ROUTES ---

@app.post("/shows/{show_id}/elements")
async def create_element(show_id: int, name: str = Form(...), category: str = Form(...), default_state: str = Form(...), session: Session = Depends(get_session)):
    element = StageElement(name=name, category=category, default_state=default_state, show_id=show_id)
    session.add(element)
    session.commit()
    session.refresh(element)
    return templates.TemplateResponse("partials/element_row.html", {"request": {}, "element": element})

@app.delete("/elements/{element_id}")
async def delete_element(element_id: int, session: Session = Depends(get_session)):
    element = session.get(StageElement, element_id)
    if element:
        session.delete(element)
        session.commit()
    return Response(status_code=200)

# --- TRANSITION ROUTES ---

@app.get("/shows/{show_id}/cues/{cue_id}")
async def get_single_cue_row(show_id: int, cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_rows.html", {"request": {}, "cues": [cue]})

@app.get("/cues/{cue_id}/transitions")
async def get_transitions(cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    elements = session.exec(select(StageElement).where(StageElement.show_id == cue.show_id)).all()
    return templates.TemplateResponse("partials/cue_transitions.html", {"request": {}, "cue": cue, "elements": elements})

@app.post("/cues/{cue_id}/transitions")
async def create_transition(cue_id: int, element_id: int = Form(...), target_state: str = Form(...), session: Session = Depends(get_session)):
    transition = ElementTransition(cue_id=cue_id, element_id=element_id, target_state=target_state)
    session.add(transition)
    session.commit()
    cue = session.get(Cue, cue_id)
    elements = session.exec(select(StageElement).where(StageElement.show_id == cue.show_id)).all()
    return templates.TemplateResponse("partials/cue_transitions.html", {"request": {}, "cue": cue, "elements": elements})

@app.delete("/transitions/{trans_id}")
async def delete_transition(trans_id: int, session: Session = Depends(get_session)):
    trans = session.get(ElementTransition, trans_id)
    cue_id = trans.cue_id
    if trans:
        session.delete(trans)
        session.commit()
    cue = session.get(Cue, cue_id)
    elements = session.exec(select(StageElement).where(StageElement.show_id == cue.show_id)).all()
    return templates.TemplateResponse("partials/cue_transitions.html", {"request": {}, "cue": cue, "elements": elements})

# --- CUE MANAGEMENT ---

@app.post("/shows/{show_id}/cues")
async def create_cue(show_id: int, number: str = Form(...), description: str = Form(...), department: str = Form(...), trigger: str = Form(None), page_num: str = Form(None), session: Session = Depends(get_session)):
    max_seq = session.exec(select(func.max(Cue.sequence)).where(Cue.show_id == show_id)).one()
    new_seq = (max_seq or 0) + 1
    new_cue = Cue(number=number, description=description, department=department, trigger=trigger, page_num=page_num, sequence=new_seq, show_id=show_id)
    session.add(new_cue)
    session.commit()
    return RedirectResponse(url=f"/shows/{show_id}", status_code=303)

@app.get("/cues/{cue_id}/activate")
async def activate_cue(request: Request, cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    if not cue: return Response(status_code=404)
    show_id = cue.show_id
    show = session.get(Show, show_id)

    # Deactivate ALL
    active_cues = session.exec(select(Cue).where(Cue.show_id == show_id).where(Cue.is_active == True)).all()
    for c in active_cues:
        c.is_active = False
        session.add(c)
    
    # Activate Target
    cue.is_active = True
    show.status = "running"
    session.add(cue)
    session.add(show)
    session.commit()
    
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

@app.post("/shows/{show_id}/reset")
async def reset_show(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id)).all()
    
    # NUCLEAR RESET: Turn EVERYTHING off
    for cue in cues:
        cue.is_active = False
        session.add(cue)
    
    show.status = "pre"
    session.add(show)
    session.commit()
    return Response(status_code=204)

@app.delete("/cues/{cue_id}")
async def delete_cue(cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    if cue:
        session.delete(cue)
        session.commit()
    return Response(status_code=200)

@app.get("/cues/{cue_id}/edit")
async def get_edit_form(request: Request, cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row_edit.html", {"request": request, "cue": cue})

@app.get("/cues/{cue_id}")
async def get_single_cue(request: Request, cue_id: int, session: Session = Depends(get_session)):
    cue = session.get(Cue, cue_id)
    return templates.TemplateResponse("partials/cue_row.html", {"request": request, "cue": cue})

@app.put("/cues/{cue_id}")
async def update_cue(request: Request, cue_id: int, number: str = Form(...), department: str = Form(...), description: str = Form(...), trigger: str = Form(None), page_num: str = Form(None), session: Session = Depends(get_session)):
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

@app.post("/reorder")
async def reorder_cues(request: Request, ids: List[int] = Form(...), session: Session = Depends(get_session)):
    show_id = None
    for index, cue_id in enumerate(ids):
        cue = session.get(Cue, cue_id)
        if cue:
            cue.sequence = index + 1
            if show_id is None: show_id = cue.show_id
            session.add(cue)
    session.commit()
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

@app.get("/shows/{show_id}/table_body")
async def get_table_body(request: Request, show_id: int, session: Session = Depends(get_session)):
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    return templates.TemplateResponse("partials/cue_rows.html", {"request": request, "cues": cues})

# --- ENGINE ROUTES (API Control) ---

@app.post("/shows/{show_id}/go")
async def go_cue_server(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    active_cue = next((c for c in cues if c.is_active), None)
    
    if active_cue:
        idx = cues.index(active_cue)
        active_cue.is_active = False 
        
        if idx < len(cues) - 1:
            cues[idx + 1].is_active = True 
            show.status = "running"
        else:
            show.status = "post" # End of show
            
    elif show.status == "pre" and cues:
        cues[0].is_active = True 
        show.status = "running"

    elif show.status == "post":
        show.status = "pre"
        
    session.add(show)
    session.commit()
    return Response(status_code=204)

@app.post("/shows/{show_id}/back")
async def back_cue_server(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    active_cue = next((c for c in cues if c.is_active), None)
    
    if active_cue:
        idx = cues.index(active_cue)
        active_cue.is_active = False # Turn off current
        
        if idx > 0:
            cues[idx - 1].is_active = True # Turn on prev
            show.status = "running"
        else:
            show.status = "pre" # Back to start
            
    elif show.status == "post" and cues:
        cues[-1].is_active = True # Back from end
        show.status = "running"

    session.add(show)
    session.commit()
    return Response(status_code=204)


# --- HUD ROUTES ---

@app.get("/shows/{show_id}/hud_content")
async def get_hud_content(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    # 1. Determine Context
    active_cue = next((c for c in cues if c.is_active), None)
    prev_cue, next_cue = None, None
    curr_global, prev_global, next_global = "-", None, None

    if active_cue:
        idx = cues.index(active_cue)
        curr_global = idx + 1
        
        if idx > 0:
            prev_cue = cues[idx - 1]
            prev_global = idx
        if idx < len(cues) - 1:
            next_cue = cues[idx + 1]
            next_global = idx + 2
            
    elif show.status == 'post' and cues:
        prev_cue = cues[-1]
        prev_global = len(cues)
        curr_global = "END"
        
    elif show.status == 'pre' and cues:
        next_cue = cues[0]
        next_global = 1
        curr_global = "PRE"

    current_time = datetime.now().strftime("%H:%M:%S")

    return templates.TemplateResponse("partials/hud_content.html", {
        "request": {},
        "show_name": show.name,
        "status": show.status,
        "current_cue": active_cue, # Note: Template expects current_cue
        "prev_cue": prev_cue,
        "next_cue": next_cue,
        "curr_global": curr_global,
        "prev_global": prev_global,
        "next_global": next_global,
        "current_time": current_time
    })

@app.get("/shows/{show_id}/hud/spatial")
async def get_spatial_content(show_id: int, session: Session = Depends(get_session)):
    show = session.get(Show, show_id)
    cues = session.exec(select(Cue).where(Cue.show_id == show_id).order_by(Cue.sequence)).all()
    
    # 1. Determine Context (Identical Logic)
    active_cue = next((c for c in cues if c.is_active), None)
    prev_cue, next_cue = None, None
    curr_global, prev_global, next_global = None, None, None # Spatial handles "PRE/END" differently in template usually, but let's pass consistent data
    
    # Note: Spatial template uses 'active_cue' variable, LVL 0 uses 'current_cue'. 
    # Logic below matches spatial expectations.
    
    if active_cue:
        idx = cues.index(active_cue)
        curr_global = idx + 1
        
        if idx > 0:
            prev_cue = cues[idx - 1]
            prev_global = idx
        if idx < len(cues) - 1:
            next_cue = cues[idx + 1]
            next_global = idx + 2

    elif show.status == 'post' and cues:
        prev_cue = cues[-1]
        prev_global = len(cues)
    
    elif show.status == 'pre' and cues:
        next_cue = cues[0]
        next_global = 1

    # 2. Element States
    active_seq = active_cue.sequence if active_cue else (999999 if show.status == 'post' else 0)
    elements = session.exec(select(StageElement).where(StageElement.show_id == show_id)).all()
    
    element_states = []
    for el in elements:
        last_move = session.exec(
            select(ElementTransition)
            .join(Cue)
            .where(ElementTransition.element_id == el.id)
            .where(Cue.sequence <= active_seq)
            .order_by(Cue.sequence.desc())
        ).first()
        current_state = last_move.target_state if last_move else el.default_state
        element_states.append({"name": el.name, "category": el.category, "state": current_state})

    fly_items = [e for e in element_states if e['category'] == 'Fly']
    deck_items = [e for e in element_states if e['category'] != 'Fly'] 
    current_time = datetime.now().strftime("%H:%M:%S")

    return templates.TemplateResponse("partials/hud_spatial.html", {
        "request": {},
        "show": show,
        "status": show.status,
        "active_cue": active_cue,
        "prev_cue": prev_cue,
        "next_cue": next_cue,
        "curr_global": curr_global,
        "prev_global": prev_global,
        "next_global": next_global,
        "deck_items": deck_items,
        "fly_items": fly_items,
        "current_time": current_time
    })