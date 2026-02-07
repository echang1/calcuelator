from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import Cue

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# 1. Run this when the app starts
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 2. View Cues (Read)
@app.get("/")
async def read_root(request: Request, session: Session = Depends(get_session)):
    # Fetch all cues from the database
    cues = session.exec(select(Cue)).all()
    return templates.TemplateResponse("index.html", {"request": request, "cues": cues})

# 3. Add a Cue (Create) - A temporary way to add data
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)