# Log Dog 🐕

A habit tracker and to-do app where your streak grows a dachshund. The more days in a row you show up, the longer the dog gets.

Log Dog is a learning project for full stack development: a Python API, a React frontend, a real database, user login, containerization, and online hosting. The code is typed out by hand on purpose, so every line gets read at least once.

---

## Table of contents

1. [The idea](#the-idea)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Running it locally](#running-it-locally)
5. [Data model](#data-model)
6. [API endpoints](#api-endpoints)
7. [Design decisions](#design-decisions)
8. [Where things stand](#where-things-stand)
9. [Known bugs and gaps](#known-bugs-and-gaps)
10. [What's next](#whats-next)
11. [Full roadmap](#full-roadmap)
12. [Lessons learned so far](#lessons-learned-so-far)

---

## The idea

Users sign in, create habits or to-dos, and check them off. Every check-off is saved with a date, which powers two numbers on each task:

- **Dog length (streak):** how many days you showed up. Counts distinct days with at least one completion.
- **Rep counter:** how many times you've done the task in total.

Consistency vs. volume. The dog measures the first, the counter measures the second.

### Requirements

- User login
- Add and delete tasks per user
- A dashboard to visualize progress
- Hosted online, not just locally
- Final form is containerized

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | **FastAPI** (Python 3.14) | Modern Python API standard, type hints, free interactive docs at `/docs` |
| Server | **uvicorn** | Runs the FastAPI app |
| ORM | **SQLAlchemy 2.x** | Write Python classes instead of raw SQL. Makes the SQLite to Postgres swap nearly free |
| Validation | **Pydantic v2** | Defines what the API accepts and returns (schemas) |
| Database | **SQLite** now, **PostgreSQL** at deploy | SQLite is just a file, zero setup. Postgres for production |
| Frontend | **React + Vite** | Not started yet (Phase 6) |
| Auth | **JWT** with hashed passwords | Not started yet (Phase 5) |
| Containers | **Docker + docker-compose** | Phase 9 |
| Hosting | Railway or Render | Phase 10 |

Dev environment: Ubuntu 26, zsh, VS Code (Python, Pylance, Ruff extensions), Node v24 via nvm.

---

## Project structure

```
log-dog/
├── .gitignore
├── README.md
└── backend/
    ├── requirements.txt      # pinned Python packages
    ├── logdog.db             # SQLite database (git-ignored, auto-created)
    ├── venv/                 # virtual environment (git-ignored)
    └── app/
        ├── __init__.py       # makes app/ a Python package
        ├── main.py           # FastAPI app and all endpoints
        ├── database.py       # engine, SessionLocal, Base, get_db()
        ├── models.py         # SQLAlchemy models: User, Task, Completion
        └── schemas.py        # Pydantic schemas: TaskCreate, TaskRead, CompletionRead
```

A `frontend/` folder will sit next to `backend/` once Phase 6 starts. Everything stays in one repo.

---

## Running it locally

From the project root:

```bash
cd backend
python3 -m venv venv              # only the first time
source venv/bin/activate          # prompt should show (venv)
pip install -r requirements.txt   # only the first time, or after pulling new packages
uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000 for the root check
- http://127.0.0.1:8000/health for the health check
- http://127.0.0.1:8000/docs for the interactive API docs (the best place to test endpoints)

Tables are created automatically on startup by `create_all()` in `main.py`.

**Placeholder user:** until auth exists, every task is owned by `user_id=1`. If you start with a fresh database, create that user once from a Python shell inside `backend/` with the venv active:

```python
from app.database import SessionLocal
from app import models

db = SessionLocal()
db.add(models.User(email="dustin@example.com", hashed_password="placeholder"))
db.commit()
db.close()
```

**zsh tip:** quote any package with brackets when installing, like `pip install "uvicorn[standard]"`, or zsh will try to treat the brackets as a file pattern.

---

## Data model

Three tables. A user has many tasks, and a task has many completions.

```
users                    tasks                      completions
─────────────            ─────────────────          ──────────────────
id (PK)          ◄────   user_id (FK)               id (PK)
email (unique)           id (PK)            ◄────   task_id (FK)
hashed_password          title                      completed_date
created_at               frequency_type             
                         created_at                 
```

| Model | Notes |
|---|---|
| `User` | `tasks` relationship with `cascade="all, delete-orphan"`, so deleting a user cleans up their tasks |
| `Task` | `frequency_type` is `"daily"` (default) or `"repeatable"`. `completions` relationship also cascades |
| `Completion` | One row per check-off. Only stores the calendar date, not the time |

Relationship strings like `relationship("User", back_populates="tasks")` must match the **class name** exactly (capital letters count), and `back_populates` names the attribute on the *other* class.

---

## API endpoints

| Method | Path | Status | What it does |
|---|---|---|---|
| GET | `/` | ✅ Working | Confirms the API is running |
| GET | `/health` | ✅ Working | Health check, used later by Docker and the host |
| POST | `/tasks` | ✅ Working | Creates a task. Body: `{"title": "...", "frequency_type": "daily"}`. Returns 201 |
| GET | `/tasks` | ✅ Working | Lists all tasks |
| DELETE | `/tasks/{task_id}` | ❌ Crashes | Deletes a task, returns 204 or 404. Has a typo, see [Known bugs](#known-bugs-and-gaps) |
| POST | `/tasks/{task_id}/complete` | ⬜ Not written | Logs a completion for today. Schema is ready, endpoint isn't |
| GET | `/tasks/{task_id}/stats` | ⬜ Planned | Returns streak (dog length) and rep count |

---

## Design decisions

**Models vs. schemas.** Models (`models.py`) describe the database. Schemas (`schemas.py`) describe what the API accepts and returns. They're kept separate on purpose, so things like `hashed_password` never leak out of the API and users can't pick their own IDs.

**One session per request.** `get_db()` in `database.py` hands every request a fresh session and always closes it afterward (the `try / finally`). Endpoints get it with `db: Session = Depends(get_db)`.

**Daily vs. repeatable tasks.** Both write to the same `completions` table. The only difference is one rule at insert time: a daily task rejects a second completion on the same day. That rule lives in the endpoint code, not a database constraint, because a unique constraint on `(task_id, date)` would break repeatable tasks.

**Streak definition.** Distinct days with at least one completion, no matter the task type. Doing a repeatable task 12 times in a day still grows the dog by one.

**Timezones (on the radar).** "Today" depends on where the user is. For now we use server time and accept it. Worth revisiting once real users exist, since a 9pm check-off in California can land on tomorrow in UTC.

**`create_all()` for now, Alembic later.** `create_all()` builds missing tables but never changes existing ones. If a column changes, the quick fix in dev is deleting `logdog.db` and letting it rebuild. The proper fix is Alembic migrations, which we can add later.

**Pydantic v2 style.** Use `model_config = {"from_attributes": True}`, not the old v1 `class Config: orm_mode = True`. Also `.model_dump()` instead of `.dict()`. Lots of tutorials online still show v1.

---

## Where things stand

**Current phase: 4 of 11 (Task CRUD API), about two-thirds done.**

| Phase | Status |
|---|---|
| 0. Dev environment | ✅ Done |
| 1. Git, GitHub, folder layout | ✅ Done |
| 2. FastAPI skeleton | ✅ Done |
| 3. Database layer | ✅ Done |
| 4. Task CRUD API | 🟡 In progress |
| 5. User auth | ⬜ |
| 6. Frontend skeleton | ⬜ |
| 7. Connect frontend to backend | ⬜ |
| 8. Dashboard and visualization | ⬜ |
| 9. Containerize | ⬜ |
| 10. Deploy online | ⬜ |
| 11. Polish | ⬜ |

**Phase 4 checklist:**

- [x] `get_db()` session dependency
- [x] `TaskCreate`, `TaskRead`, `CompletionRead` schemas
- [x] `POST /tasks` (tested, returned 201)
- [x] `GET /tasks`
- [ ] Fix and test `DELETE /tasks/{task_id}`
- [ ] Fix the `completed_date` default
- [ ] Write and test `POST /tasks/{task_id}/complete`
- [ ] Add the once-per-day rule for daily tasks
- [ ] Add a stats endpoint (streak + rep count)
- [ ] Commit and push

**Git status:** the last commit is from July 2. Everything since then is **not committed**: changes to `database.py`, `main.py`, `models.py`, and the new `schemas.py`. GitHub currently shows an empty `models.py` and a `main.py` with only the two health endpoints.

**Database contents:** one placeholder user (`dustin@example.com`) and one task (`walk the dog`, daily). No completions yet.

---

## Known bugs and gaps

### 1. `DELETE /tasks/{task_id}` crashes with a 500

In `main.py`, a parenthesis is in the wrong spot, so `.filter()` gets called on the model class instead of on the query:

```python
# current (broken)
task = db.query(models.Task.filter(models.Task.id == task_id). first())

# fixed
task = db.query(models.Task).filter(models.Task.id == task_id).first()
```

The server still starts fine, because Python only runs that line when the endpoint is called. That's why it hasn't shown up yet.

### 2. `completed_date` will crash the completion endpoint

In `models.py`, `Completion.completed_date` uses `server_default=func.now()`. In SQLite that stores a full timestamp (`2026-10-16 22:44:42`) in a column declared as a `Date`, and SQLAlchemy throws a `ValueError` when it tries to read it back. Swap it for a Python-side default that gives a plain date:

```python
from datetime import date

completed_date = Column(Date, nullable=False, default=date.today)
```

Note it's `date.today` without parentheses, so SQLAlchemy calls it fresh each time a row is added. Since the column itself isn't changing, no need to delete the database for this one.

### 3. Small stuff

- `database.py` has a typo in a variable name: `SQLALCHEMY_DATABAS_URL` (missing the E). It works because it's spelled the same way both times, but it's worth fixing.
- `GET /tasks` returns every task in the database, not just the current user's. Expected for now, Phase 5 fixes it.
- `POST /tasks` hardcodes `user_id=1`. Also Phase 5.
- `frequency_type` accepts any string. Could be locked down to `"daily"` or `"repeatable"` with a `Literal` type in the schema.

---

## What's next

### Finish Phase 4

1. **Fix the delete bug** (bug 1 above), then test it in `/docs`: delete a throwaway task and check you get a 204, then try a made-up ID and check you get a 404.
2. **Fix `completed_date`** (bug 2 above).
3. **Add the completion endpoint** to the bottom of `main.py`:

   ```python
   @app.post("/tasks/{task_id}/complete", response_model=schemas.CompletionRead, status_code=201)
   def complete_task(task_id: int, db: Session = Depends(get_db)):
       task = db.query(models.Task).filter(models.Task.id == task_id).first()
       if task is None:
           raise HTTPException(status_code=404, detail="Task not found")

       completion = models.Completion(task_id=task.id)
       db.add(completion)
       db.commit()
       db.refresh(completion)
       return completion
   ```

   Test it on task 1 in `/docs`.
4. **Add the daily rule.** Before creating the completion, if `task.frequency_type == "daily"` and a completion for this task already exists with today's date, reject it with a `409 Conflict`.
5. **Add a stats endpoint** like `GET /tasks/{task_id}/stats` returning `{"streak_days": ..., "total_completions": ...}`. This is the data the dachshund will be drawn from.
6. **Commit and push.** Good point to break it into a couple of commits, like "Add task CRUD and completion endpoints" and "Fix completion date default."

### Then Phase 5: User auth

- Install password hashing and JWT libraries
- `POST /auth/register` and `POST /auth/login` endpoints
- Hash passwords on signup, never store the plain password
- Issue a JWT token on login
- A `get_current_user` dependency (same idea as `get_db`) that reads the token
- Replace the hardcoded `user_id=1` and filter all task queries by the logged-in user
- Make sure a user can't delete or complete someone else's task (return 404, not 403, so you don't reveal it exists)

---

## Full roadmap

0. **Dev environment.** Node via nvm, Python venv, Git config, VS Code extensions.
1. **Version control.** Git, GitHub, one repo for frontend and backend.
2. **Backend skeleton.** Minimal FastAPI app with a health check.
3. **Database layer.** Schema design, SQLAlchemy models, SQLite.
4. **Task CRUD API.** Create, list, delete, log completions.
5. **User auth.** Registration, login, password hashing, JWT, protected routes.
6. **Frontend skeleton.** React + Vite, routing, login and dashboard pages.
7. **Connect frontend to backend.** Auth flow in the UI, real task list, add and delete.
8. **Dashboard and visualization.** The dachshund, streaks, history chart or heatmap.
9. **Containerize.** Dockerfiles, docker-compose, swap SQLite for Postgres. Docker isn't installed on the dev machine yet.
10. **Deploy online.** Hosting, environment variables, basic CI/CD.
11. **Polish.** Tests, error handling, final README.

Possible extras along the way: an update endpoint (`PATCH /tasks/{task_id}` to rename a task), Alembic migrations, and moving routes out of `main.py` into separate router files once it gets crowded.

---

## Lessons learned so far

- **Read the error before the code.** Python tracebacks name the file and line.
- **"Failed to locate a name" in SQLAlchemy** almost always means a typo or wrong capitalization in a `relationship()` string.
- **Moving a project folder breaks the venv**, since a venv stores absolute paths. Delete it and recreate it. Git history moves with the folder just fine.
- **`Base`** collects table blueprints from every class that inherits from it, and `create_all()` builds them. That's why `main.py` has to import `models` even though it looks unused.
- **A session** is a Python object holding a borrowed connection, a map of objects it's tracking, and an open transaction. `add()` stages, `commit()` saves, `close()` throws away anything uncommitted.
- **Status codes matter:** 201 for created, 204 for deleted with nothing to return, 404 for not found, 409 for a conflict like a duplicate daily check-off.
- **Commit early and often.** Two weeks of work sitting uncommitted is a lot to lose to one bad `rm`.