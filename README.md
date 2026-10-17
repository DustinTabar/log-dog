# Log Dog 🐕

A habit tracker and to-do app where your streak grows a dachshund. The more intervals in a row you show up, the longer the dog gets.

Log Dog is a learning project for full stack development: a Python API, a React frontend, a real database, user login, containerization, and online hosting. The code is typed out by hand on purpose, so every line gets read at least once.

---

## Table of contents

1. [The idea](#the-idea)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Running it locally](#running-it-locally)
5. [Data model](#data-model)
6. [API endpoints](#api-endpoints)
7. [How intervals and streaks work](#how-intervals-and-streaks-work)
8. [Design decisions](#design-decisions)
9. [Where things stand](#where-things-stand)
10. [Known gaps](#known-gaps)
11. [What's next](#whats-next)
12. [Full roadmap](#full-roadmap)
13. [Lessons learned so far](#lessons-learned-so-far)

---

## The idea

Users sign in, create tasks, and check them off. Each task has an **interval**: day, week, month, or year. Every check-off is saved with a date, and two numbers come out of that history:

- **Streak (dog length):** how many intervals in a row the task was done at least once. Miss an interval and the dog resets.
- **Period count (number inside the dog):** how many times the task was done in the current interval.

Both show up in the same view. "Brush teeth" (daily) might show a dog 12 segments long with a 2 inside: 12 days running, twice today. "Gym" (weekly) might show 5 and 3: 5 weeks running, three sessions this week.

Every task works the same way, whatever its interval. It can be checked off as many times as you like, and every check-off counts.

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

Dev environment: Ubuntu 26, zsh, VS Code (Python, Pylance, Ruff extensions), Node v24 via nvm, sqlite3 CLI.

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
        ├── schemas.py        # Pydantic schemas: TaskCreate, TaskRead, CompletionRead, TaskStats
        └── streaks.py        # interval definitions and streak math (no database code)
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

**Placeholder user:** until auth exists, every task is owned by `user_id=1`. With a fresh database, create that user once. Open a second terminal, `cd` into `backend/`, activate the venv, run `python`, and type these lines one at a time at the `>>>` prompt:

```python
from app.database import SessionLocal
from app import models
db = SessionLocal()
db.add(models.User(email="dustin@example.com", hashed_password="placeholder"))
db.commit()
db.close()
exit()
```

**Peeking at the database:** from `backend/`, run `sqlite3 logdog.db "SELECT * FROM completions;"`. Without the sqlite3 CLI, this works too: `python -c "import sqlite3; print(sqlite3.connect('logdog.db').execute('SELECT * FROM completions').fetchall())"`.

**Changing a table:** `create_all()` only builds tables that don't exist yet. It never changes an existing one. After changing a model's columns, delete `logdog.db`, restart the server, and recreate the placeholder user.

**zsh tip:** quote any package with brackets when installing, like `pip install "uvicorn[standard]"`, or zsh will try to treat the brackets as a file pattern.

**apt tip:** if `apt install` fails with a 404, run `sudo apt update` first to refresh the package list.

---

## Data model

Three tables. A user has many tasks, and a task has many completions.

```
users                    tasks                      completions
─────────────            ─────────────────          ──────────────────
id (PK)          ◄────   user_id (FK)               id (PK)
email (unique)           id (PK)            ◄────   task_id (FK)
hashed_password          title                      completed_date
created_at               interval                   
                         created_at                 
```

| Model | Notes |
|---|---|
| `User` | `tasks` relationship with `cascade="all, delete-orphan"`, so deleting a user cleans up their tasks |
| `Task` | `interval` is `"day"` (default), `"week"`, `"month"`, or `"year"`. `completions` relationship also cascades |
| `Completion` | One row per check-off. Stores only the calendar date, set by `default=date.today` |

**Counts and streaks are not stored anywhere.** They're calculated from the completion rows every time stats are requested. See [Design decisions](#design-decisions).

Relationship strings like `relationship("User", back_populates="tasks")` must match the **class name** exactly (capital letters count), and `back_populates` names the attribute on the *other* class.

---

## API endpoints

| Method | Path | What it does |
|---|---|---|
| GET | `/` | Confirms the API is running |
| GET | `/health` | Health check, used later by Docker and the host |
| POST | `/tasks` | Creates a task. Body: `{"title": "...", "interval": "week"}` (interval is optional, defaults to `"day"`). Returns 201, or 422 for an unknown interval |
| GET | `/tasks` | Lists all tasks |
| DELETE | `/tasks/{task_id}` | Deletes a task and its completions. Returns 204, or 404 if it doesn't exist |
| POST | `/tasks/{task_id}/complete` | Logs a check-off for today. Returns 201 with the completion, or 404 |
| GET | `/tasks/{task_id}/stats` | Returns `{"task_id", "streak", "period_count"}`, or 404 |

All endpoints are tested and working in `/docs`.

**Reading `/docs` responses:** "Server response" is what actually happened. The "Responses" section below it is auto-generated documentation of what the endpoint *could* return. FastAPI adds the 422 entry on its own because of the type hints, and it doesn't list 404s raised inside a function.

---

## How intervals and streaks work

All the logic lives in `backend/app/streaks.py`, with no database code, so it's easy to test on its own.

**Every interval comes down to one question: when does it start?** Each interval has a function that takes any date and returns the first day of the interval it falls in:

| Interval | Start of the interval | Example for Fri Oct 16, 2026 |
|---|---|---|
| day | the date itself | Oct 16, 2026 |
| week | that week's Monday | Oct 12, 2026 |
| month | the 1st | Oct 1, 2026 |
| year | Jan 1 | Jan 1, 2026 |

Two dates are in the same interval if they have the same start date.

**The `INTERVALS` dictionary** maps each name to its start function. It's the single place intervals are defined. The schema validator checks incoming tasks against its keys, and the streak math looks functions up in it.

**Adding a new interval** (quarter, for example) takes two edits, both in `streaks.py`:

```python
def start_of_quarter(d: date) -> date:
    first_month = 3 * ((d.month - 1) // 3) + 1
    return d.replace(month=first_month, day=1)

INTERVALS = {
    ...
    "quarter": start_of_quarter,
}
```

That's it. Validation, the 422 error message, and the streak math all pick it up. Since `interval` is stored as plain text, no database change is needed either.

**Stepping back one interval** works the same way for every interval: go back one day from the start of the current one, then snap to the start of whatever interval that lands in. That's why a new interval only needs a start function.

**The streak calculation:**

1. Turn every completion date into the start of its interval, and collect them in a set (`done_periods`).
2. **Period count** = completions whose interval start matches the current interval's start.
3. **Streak:** start at the current interval if it's been done, otherwise start at the previous one (the grace rule). Walk backward one interval at a time, adding 1, until hitting an interval that isn't in the set.

**The grace rule:** the dog doesn't shrink until a whole interval goes by without a check-off. If you brushed your teeth yesterday and the day before, the dog still shows 2 this morning, before you've brushed. It only resets if all of today passes without a check-off.

---

## Design decisions

**Every task behaves the same.** No caps, no task types. Any task can be checked off any number of times in its interval, and the only per-task setting is `interval`. (An earlier version had a `frequency_type` and then an `allow_multiple` flag that rejected repeat check-offs with a 409. Both were removed once the rule became "every check-off counts.")

**Derived data, not stored counters.** There's no count column. The completions table is the single source of truth, and streaks and counts are calculated from it when needed. A stored counter would need a scheduled job to reset it every day, week, month, and year, and it could drift out of sync with the real history. If calculating ever gets slow, the fix is caching, not storing.

**Database code in `main.py`, math in `streaks.py`.** The stats endpoint pulls the completion dates and hands them to `calculate_stats()`, which only knows about lists of dates. That keeps the math easy to read and easy to test without a database.

**Weeks start on Monday.** That's the ISO standard and Python's default (`date.weekday()` returns 0 for Monday). To switch to Sunday, only `start_of_week` changes.

**Models vs. schemas.** Models (`models.py`) describe the database. Schemas (`schemas.py`) describe what the API accepts and returns. They're kept separate on purpose, so things like `hashed_password` never leak out of the API and users can't pick their own IDs.

**Validation in the schema.** `TaskCreate` uses a `field_validator` to check `interval` against `INTERVALS`. Bad input gets a 422 before any endpoint code runs.

**One session per request.** `get_db()` in `database.py` hands every request a fresh session and always closes it afterward (the `try / finally`). Endpoints get it with `db: Session = Depends(get_db)`.

**`default` vs. `server_default`.** `default=date.today` means Python fills in the value. `server_default` hands the value to the database as SQL, so it only accepts SQL like `func.now()`, never a Python function.

**Timezones (on the radar).** "Today" uses the server's clock for now. Worth revisiting once real users exist, since a 9pm check-off in California can land on tomorrow in UTC.

**`create_all()` for now, Alembic later.** Fine while the only data is test data. Once real data exists, Alembic migrations can change tables without deleting anything.

**Pydantic v2 style.** Use `model_config = {"from_attributes": True}`, not the old v1 `class Config: orm_mode = True`. Also `.model_dump()` instead of `.dict()`. Lots of tutorials online still show v1.

---

## Where things stand

**Current phase: Phase 4 (Task CRUD API) is done. Phase 5 (User auth) is next.**

| Phase | Status |
|---|---|
| 0. Dev environment | ✅ Done |
| 1. Git, GitHub, folder layout | ✅ Done |
| 2. FastAPI skeleton | ✅ Done |
| 3. Database layer | ✅ Done |
| 4. Task CRUD API | ✅ Done |
| 5. User auth | ⬜ Next |
| 6. Frontend skeleton | ⬜ |
| 7. Connect frontend to backend | ⬜ |
| 8. Dashboard and visualization | ⬜ |
| 9. Containerize | ⬜ |
| 10. Deploy online | ⬜ |
| 11. Polish | ⬜ |

**Phase 4 recap:**

- [x] `get_db()` session dependency
- [x] Schemas for tasks, completions, and stats
- [x] Create, list, and delete tasks (fixed a misplaced parenthesis in delete)
- [x] Fixed the `completed_date` default (a full timestamp in a date column crashed on read)
- [x] Completion endpoint
- [x] Intervals: day, week, month, year, defined in one place
- [x] Stats endpoint with streak and period count

---

## Known gaps

These are all expected at this stage, and most are handled by later phases.

- `GET /tasks` returns every task in the database, not just the current user's. Phase 5.
- `POST /tasks` hardcodes `user_id=1`. Phase 5.
- No way to undo an accidental check-off. A `DELETE /completions/{id}` endpoint would cover it.
- No way to edit a task's title or interval. A `PATCH /tasks/{task_id}` endpoint would cover it.
- `database.py` has a typo in a variable name: `SQLALCHEMY_DATABAS_URL` (missing the E). It works because it's spelled the same both times, but it's worth fixing.
- No automated tests yet. `calculate_stats()` is the best first candidate for pytest.

---

## What's next

### Phase 5: User auth

- Install password hashing and JWT libraries
- `POST /auth/register` and `POST /auth/login` endpoints
- Hash passwords on signup, never store the plain password
- Issue a JWT token on login
- A `get_current_user` dependency (same idea as `get_db`) that reads the token
- Replace the hardcoded `user_id=1` and filter all task queries by the logged-in user
- Make sure a user can't delete, complete, or see stats for someone else's task (return 404, not 403, so you don't reveal it exists)

### Nice to have before or during Phase 5

- Undo a check-off (`DELETE /completions/{id}`)
- Edit a task (`PATCH /tasks/{task_id}`)
- First pytest tests for `streaks.py`

---

## Full roadmap

0. **Dev environment.** Node via nvm, Python venv, Git config, VS Code extensions.
1. **Version control.** Git, GitHub, one repo for frontend and backend.
2. **Backend skeleton.** Minimal FastAPI app with a health check.
3. **Database layer.** Schema design, SQLAlchemy models, SQLite.
4. **Task CRUD API.** Create, list, delete, log completions, stats.
5. **User auth.** Registration, login, password hashing, JWT, protected routes.
6. **Frontend skeleton.** React + Vite, routing, login and dashboard pages.
7. **Connect frontend to backend.** Auth flow in the UI, real task list, add and delete.
8. **Dashboard and visualization.** The dachshund, streaks, history chart or heatmap.
9. **Containerize.** Dockerfiles, docker-compose, swap SQLite for Postgres. Docker isn't installed on the dev machine yet.
10. **Deploy online.** Hosting, environment variables, basic CI/CD.
11. **Polish.** Tests, error handling, final README.

Possible extras along the way: Alembic migrations, and moving routes out of `main.py` into separate router files once it gets crowded.

---

## Lessons learned so far

- **Read the error before the code.** Python tracebacks name the file and line. Start at the bottom for the actual complaint, then find the last line that points at your own project.
- **"Failed to locate a name" in SQLAlchemy** almost always means a typo or wrong capitalization in a `relationship()` string.
- **`date` vs. `Date`:** lowercase `date` is Python's date class (`from datetime import date`). Capital `Date` is SQLAlchemy's column type. Different imports.
- **`date.today` vs. `date.today()`:** without parentheses you're passing the function to be called later (a column default). With parentheses you're calling it right now to get today's date.
- **Code inside a function only runs when the function is called.** A broken endpoint can sit there silently while the server starts fine.
- **Moving a project folder breaks the venv**, since a venv stores absolute paths. Delete it and recreate it. Git history moves with the folder just fine.
- **`Base`** collects table blueprints from every class that inherits from it, and `create_all()` builds them. That's why `main.py` has to import `models` even though it looks unused.
- **A session** is a Python object holding a borrowed connection, a map of objects it's tracking, and an open transaction. `add()` stages, `commit()` saves, `close()` throws away anything uncommitted.
- **Status codes matter:** 201 for created, 204 for deleted with nothing to return, 404 for not found, 422 for invalid input.
- **SQLite can reuse IDs.** Without AUTOINCREMENT, a new row gets the highest existing ID plus one, so deleting the newest row frees its ID.
- **Functions are values.** They can be stored in a dictionary and looked up by name, which is how `INTERVALS` works.
- **Commit early and often.** Two weeks of work sitting uncommitted is a lot to lose to one bad `rm`.