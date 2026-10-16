from datetime import datetime, date

from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    frequency_type: str = "daily"

class TaskRead(BaseModel):
    id: int
    title: str
    frequency_type: str
    created_at: datetime

    model_config = {"from_attributes": True}

class CompletionRead(BaseModel):
    id: int
    completed_date: date
    task_id: int

    model_config = {"from_attributes": True}
    