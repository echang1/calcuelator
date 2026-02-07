from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Tell FastAPI where to find HTML templates
templates = Jinja2Templates(directory="templates")

# (Optional) Tell FastAPI where to find static files like CSS
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root(request: Request):
    """
    This function runs when you go to http://localhost:8000/
    It renders the index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request, "message": "Show Control System"})

if __name__ == "__main__":
    import uvicorn
    # Run the app on host 0.0.0.0 (accessible on network) and port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)