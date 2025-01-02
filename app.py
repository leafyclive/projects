from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import models
from sqlalchemy.exc import SQLAlchemyError

from starlette.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Todo
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

models.Base.metadata.create_all(bind=engine)

directory = Jinja2Templates(directory="templates")

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.add_middleware(SessionMiddleware, secret_key="!secret")


# ----------------- Dependency -----------------


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None  # User not found or password doesn't match
    return user


# --------------------------------------------

# ----------------- Home -----------------


@app.get("/")
async def home(req: Request, db: Session = Depends(get_db)):
    logged_in = False
    user = None

    # Check if user is logged in
    if hasattr(req, "session") and "user" in req.session:
        logged_in = True
        user = req.session["user"]

    todos = db.query(models.Todo).all()

    # Categorize tasks by their status
    pending_tasks = [
        task for task in todos if not task.status and task.dueDate >= datetime.now()
    ]
    completed_tasks = [task for task in todos if task.status]
    overdue_tasks = [
        task for task in todos if not task.status and task.dueDate < datetime.now()
    ]

    return directory.TemplateResponse(
        "index.html",
        {
            "request": req,
            "logged_in": logged_in,
            "user": user,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
        },
    )


# -----------------------------------------

# ----------------- Profile -----------------


@app.get("/profile")
async def profile(req: Request):
    return directory.TemplateResponse("profile.html", {"request": req})


# -----------------------------------------

# ----------------- Login -----------------


@app.get("/login")
async def login(req: Request):
    return directory.TemplateResponse("login.html", {"request": req})


@app.post("/token")
async def login_for_access_token(
    req: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Authenticate the user using the User table
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})

    # Set the session to indicate the user is logged in
    if hasattr(req, "session"):
        req.session["user"] = user.username

    # Redirect to the home page after successful login
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
async def logout(req: Request):
    req.session.clear()
    return RedirectResponse(url="/", status_code=303)


# -----------------------------------------

# ----------------- Sign Up -----------------


@app.get("/sign_up")
async def signup(req: Request):
    return directory.TemplateResponse("sign_up.html", {"request": req})


@app.post("/sign_up")
async def signup_post(req: Request, db: Session = Depends(get_db)):
    form = await req.form()
    username = form.get("username")
    email = form.get("email")
    password = form.get("password")

    print(f"username: {username}, email: {email}, password: {password}")

    if not username or not password or not email:
        return {"error": "Username, Password, and Email are required."}

    # Hash the password
    hashed_password = pwd_context.hash(password)

    # Create a new User instance with the captured data
    new_user = models.User(
        username=username,
        hashed_password=hashed_password,
        email=email,
    )

    try:
        # Add the new user to the database session and commit
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Redirect to the login page after successful signup
        return RedirectResponse(url="/login", status_code=303)
    except SQLAlchemyError as e:
        db.rollback()  # Rollback in case of an error
        return {"error": f"Error occurred while saving the user: {str(e)}"}


# -----------------------------------------

# ----------------- New Task -----------------


@app.get("/new_task", response_class=HTMLResponse)
async def get_new_task_page(req: Request):
    # Render the new task creation page
    return directory.TemplateResponse("new_task.html", {"request": req})


@app.post("/new_task")
async def newTask(req: Request, db: Session = Depends(get_db)):
    form = await req.form()
    title = form.get("taskTitle")
    description = form.get("taskDescription")
    due_date = form.get("taskDueDate")

    if not title or not due_date:
        return {"error": "Title and Due Date are required."}

    # Create a new Todo instance
    new_task = Todo(
        title=title,
        description=description,
        status=False,
        dueDate=datetime.strptime(due_date, "%Y-%m-%d"),
    )

    # Add the new task to the database session and commit
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Redirect to the index page after task creation
    return RedirectResponse(url="/", status_code=303)


# --------------------------------------------


@app.get("/analytics")
async def analytics(req: Request, db: Session = Depends(get_db)):
    return directory.TemplateResponse("analytics.html", {"request": req})


# ---------------complete task-----------------


@app.post("/complete_task/{task_id}")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Todo).filter(models.Todo.id == task_id).first()
    if task:
        task.status = True
        db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------
