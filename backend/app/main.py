from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import date

from app import models, schemas
from app.security import create_access_token, hash_password, verify_password
from app.streaks import calculate_stats
from app.database import engine, get_db
from app.dependencies import get_current_user


# Create any tables that don't exist yet
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Log Dog API")

######################################################
#                      GET                           #
######################################################

@app.get("/")
def read_root():
    return {"message": "Log Dog API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", response_model=list[schemas.TaskRead])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Task).filter(models.Task.user_id == current_user.id).all()

@app.get("/auth/me", response_model=schemas.UserRead)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/tasks/{task_id}/stats", response_model=schemas.TaskStats)
def get_task_stats(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = get_owned_task(task_id, current_user, db)

    rows = db.query(models.Completion.completed_date).filter(
        models.Completion.task_id == task.id
    ).all()
    dates = [row.completed_date for row in rows]

    streak, period_count = calculate_stats(dates, task.interval, date.today())
    return {"task_id": task.id, "streak": streak, "period_count": period_count}

def get_owned_task(task_id: int, user: models.User, db: Session) -> models.Task:
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user.id,
    ).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

######################################################
#                      POST                          #
######################################################

@app.post("/tasks", response_model=schemas.TaskRead, status_code=201)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_task = models.Task(
        title=task.title,
        interval=task.interval,
        user_id=current_user.id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.post("/tasks/{task_id}/complete", response_model=schemas.CompletionRead, status_code=201)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = get_owned_task(task_id, current_user, db)
    completion = models.Completion(task_id=task.id)
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion

@app.post("/auth/register", response_model=schemas.UserRead, status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    email = user.email.lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = models.User(email=email, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username.lower()).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

######################################################
#                      DELETE                        #
######################################################

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = get_owned_task(task_id, current_user, db)
    db.delete(task)
    db.commit()
    return None
