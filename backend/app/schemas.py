from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from app.streaks import INTERVALS


class TaskCreate(BaseModel):
    title: str
    interval: str = "day"

    @field_validator("interval")
    @classmethod
    def check_interval(cls, value: str) -> str:
        if value not in INTERVALS:
            raise ValueError(f"interval must be one of: {', '.join(INTERVALS)}")
        return value


class TaskRead(BaseModel):
    id: int
    title: str
    interval: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompletionRead(BaseModel):
    id: int
    completed_date: date
    task_id: int

    model_config = {"from_attributes": True}


class TaskStats(BaseModel):
    task_id: int
    streak: int
    period_count: int


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str