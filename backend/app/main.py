from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import engine, get_db

# Create any tables that don't exist yet
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Log Dog API")

@app.get("/")
def read_root():
    return {"message": "Log Dog API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/tasks", response_model=schemas.TaskRead, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session=Depends(get_db)):
    new_task = models.Task(
        title=task.title,
        frequency_type=task.frequency_type,
        user_id=1 # temp until auth exists in phase 5
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks", response_model=list[schemas.TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task.filter(models.Task.id == task_id). first())
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None