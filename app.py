from fastapi import FastAPI, Depends, Request, Form, status

from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)

directory = Jinja2Templates(directory="templates")

app = FastAPI()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(req: Request, db: Session = Depends(get_db)):
    todos = db.query(models.Todo).all()
    return directory.TemplateResponse("index.html", {"request": req, "todo_list": todos})

@app.get("/profile")
async def profile(req: Request, db: Session = Depends(get_db)):
    return directory.TemplateResponse("profile.html",{"request": req})

@app.get("/login")
async def profile(req: Request, db: Session = Depends(get_db)):
    return directory.TemplateResponse("login.html",{"request": req})

@app.get("/sign_up")
async def profile(req: Request, db: Session = Depends(get_db)):
    return directory.TemplateResponse("sign_up.html",{"request":req})

@app.get("/new_task")
async def profile(req: Request, db: Session = Depends(get_db)):
    return directory.TemplateResponse("new_task.html",{"request":req})

@app.get("/analytics")
async def profile(req: Request, db:Session = Depends(get_db)):
    return directory.TemplateResponse("analytics.html",{"request":req})





