from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # A user has many tasks
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks" 

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    interval = Column(String, nullable=False, default="day")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # A task belongs to one user
    owner = relationship("User", back_populates="tasks")
    # A task has many completions
    completions = relationship("Completion", back_populates="task", cascade="all, delete-orphan")


class Completion(Base):
    __tablename__ = "completions"

    id = Column(Integer, primary_key=True, index=True)
    completed_date = Column(Date, nullable=False, default=date.today)

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    # A completion belongs to one task
    task = relationship("Task", back_populates="completions")
