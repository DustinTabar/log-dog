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
7. [How login and auth work](#how-login-and-auth-work)
8. [How intervals and streaks work](#how-intervals-and-streaks-work)
9. [Design decisions](#design-decisions)
10. [Where things stand](#where-things-stand)
11. [Known gaps](#known-gaps)
12. [What's next](#whats-next)
13. [Full roadmap](#full-roadmap)
14. [Lessons learned so far](#lessons-learned-so-far)

---

## The idea

Users sign up, log in, create tasks, and check them off. Each task has an **interval**: day, week, month, or year. Every check-off is saved with a date, and two numbers come out of that history:

- **Streak (dog length):** how many intervals in a row the task was done at least once. Miss an interval and the dog resets.
- **Period count (number inside the dog):** how many times the task was done in the current interval.

Both show up in the same view. "Brush teeth" (daily) might show a dog 12 segments long with a 2 inside: 12 days running, twice today. "Gym" (weekly) might show 5 and 3: 5 weeks running, three sessions this week.

Every task works the same way, whatever its interval. It can be checked off as many times as you like, and every check-off counts. Each user only ever sees their own tasks.

### Requirements

- User login ✅
- Add and delete tasks per user ✅
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
| Password hashing | **pwdlib** with **Argon2** | Current recommended hashing algorithm |
| Tokens | **PyJWT** | Creates and checks signed login tokens (JWTs) |
| Login form | **python-multipart** | Lets FastAPI read the standard OAuth2 login form |
| Config | **python-dotenv** | Loads `SECRET_KEY` from `backend/.env` |
| Frontend | **React + Vite** | Phase 6 |
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
    ├── .env                  # SECRET_KEY lives here (git-ignored, never committed)
    ├── requirements.txt      # pinned Python packages
    ├── logdog.db             # SQLite database (git-ignored, auto-created)
    ├── venv/                 # virtual environment (git-ignored)
    └── app/
        ├── __init__.py       # makes app/ a Python package
        ├── main.py           # FastAPI app and all endpoints
        ├── database.py       # engine, SessionLocal, Base, get_db()
        ├── models.py         # SQLAlchemy models: User, Task, Completion
        ├── schemas.py        # Pydantic schemas for users, tokens, tasks, completions, stats
        ├── security.py       # password hashing and token creation (no database code)
        ├── dependencies.py   # get_current_user(): turns a token into a logged-in user
        └── streaks.py        # interval definitions and streak math (no database code)
```

A `frontend/` folder will sit next to `backend/` once Phase 6 starts. Everything stays in one repo.

---

## Running it locally

### First-time setup

From the project root:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # prompt should show (venv)
pip install -r requirements.txt
```

Then create the secret key that signs login tokens. Generate one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

And save it in `backend/.env` (next to `requirements.txt`, not inside `app/`):

```
SECRET_KEY=paste_the_long_string_here
```

No quotes and no spaces around the `=`. The server refuses to start without it. **Never commit this file.** `.gitignore` already excludes it.

### Every time

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000 for the root check
- http://127.0.0.1:8000/health for the health check
- http://127.0.0.1:8000/docs for the interactive API docs (the best place to test endpoints)

Tables are created automatically on startup by `create_all()` in `main.py`.

### Testing in `/docs`

1. `POST /auth/register` with `{"email": "...", "password": "..."}` (password must be 8+ characters).
2. Click **Authorize** (top right, padlock icon). Enter your email as `username`, plus your password, and leave the other fields blank. `/docs` logs in for you and attaches the token to every request after that.
3. Every endpoint with a padlock now works as you. **Logout** in the same dialog drops the token.

To test as a second user, register another account, then Logout and Authorize as them.

### Handy tips

**Peeking at the database:** from `backend/`, run `sqlite3 logdog.db "SELECT * FROM users;"` (or `tasks`, `completions`). Without the sqlite3 CLI, this works too: `python -c "import sqlite3; print(sqlite3.connect('logdog.db').execute('SELECT * FROM users').fetchall())"`.

**Changing a table:** `create_all()` only builds tables that don't exist yet. It never changes an existing one. After changing a model's columns, delete `logdog.db`, restart the server, and register again.

**Testing auth with curl:**

```bash
curl -X POST http://127.0.0.1:8000/auth/login -d "username=you@example.com" -d "password=YOUR_PASSWORD"
curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer PASTE_TOKEN_HERE"
```

**zsh tip:** quote any package with brackets when installing, like `pip install "pwdlib[argon2]"`, or zsh will try to treat the brackets as a file pattern.

**Network tips (this dev machine):** IPv6 on the home network drops connections partway through, which broke `pip install` and `apt install`. The fix was telling the machine to prefer IPv4:

```bash
sudo sh -c 'echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf'
```

To undo it, delete that line from `/etc/gai.conf`. And if `apt install` fails with a 404, run `sudo apt update` first to refresh the package list.

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
| `User` | Email is stored lowercase. `hashed_password` holds an Argon2 hash, never the real password. `tasks` relationship cascades on delete |
| `Task` | Owned by one user. `interval` is `"day"` (default), `"week"`, `"month"`, or `"year"`. `completions` relationship cascades on delete |
| `Completion` | One row per check-off. Stores only the calendar date, set by `default=date.today` |

**Counts and streaks are not stored anywhere.** They're calculated from the completion rows every time stats are requested. See [Design decisions](#design-decisions).

Relationship strings like `relationship("User", back_populates="tasks")` must match the **class name** exactly (capital letters count), and `back_populates` names the attribute on the *other* class.

---

## API endpoints

🔒 = requires a login token (`Authorization: Bearer <token>` header). Without one, these return a **401**.

| Method | Path | Auth | What it does |
|---|---|---|---|
| GET | `/` | | Confirms the API is running |
| GET | `/health` | | Health check, used later by Docker and the host |
| POST | `/auth/register` | | Creates an account. Body: `{"email", "password"}`. Returns 201 with the user (never the password), 409 if the email is taken, 422 if the password is under 8 characters |
| POST | `/auth/login` | | Logs in. Takes a **form** (`username` = email, `password`), not JSON. Returns 200 with `{"access_token", "token_type": "bearer"}`, or 401 |
| GET | `/auth/me` | 🔒 | Returns the logged-in user |
| POST | `/tasks` | 🔒 | Creates a task owned by you. Body: `{"title", "interval"}` (interval is optional, defaults to `"day"`). Returns 201, or 422 for an unknown interval |
| GET | `/tasks` | 🔒 | Lists **your** tasks only |
| DELETE | `/tasks/{task_id}` | 🔒 | Deletes your task and its completions. Returns 204, or 404 |
| POST | `/tasks/{task_id}/complete` | 🔒 | Logs a check-off for today. Returns 201, or 404 |
| GET | `/tasks/{task_id}/stats` | 🔒 | Returns `{"task_id", "streak", "period_count"}`, or 404 |

Every task endpoint returns **404** for a task that belongs to someone else, exactly as if it didn't exist.

All endpoints are tested and working in `/docs`, including with two users.

**Reading `/docs` responses:** "Server response" is what actually happened. The "Responses" section below it is auto-generated documentation of what the endpoint *could* return. FastAPI adds the 422 entry on its own because of the type hints, and it doesn't list 401s or 404s raised inside a function.

---

## How login and auth work

**The server has no memory between requests.** Every request has to prove who's making it. The token is how that happens without sending the password every time.

### Phase 1: log in once, get a token

```
Client ── POST /auth/login (username, password) ──►  Server
                                                     1. find the user by email
                                                     2. verify_password() against the stored hash
                                                     3. create_access_token(user.id)
Client ◄── 200 {"access_token": "eyJ...", "token_type": "bearer"}
```

### Phase 2: every request after that, show the token

```
Client ── GET /tasks ──────────────────────────────►  Server
          Authorization: Bearer eyJ...
                                                     1. oauth2_scheme pulls the token from the header
                                                     2. jwt.decode() checks the signature and expiration
                                                     3. reads "sub", looks up that user
                                                     4. hands the user to the endpoint
Client ◄── 200 [your tasks]
```

### The pieces

| Piece | File | Job |
|---|---|---|
| `hash_password()` / `verify_password()` | `security.py` | Argon2 one-way hashing. The real password is never stored |
| `create_access_token()` | `security.py` | Builds a JWT with `sub` (user ID as a string) and `exp` (60 minutes out, in UTC), signed with `SECRET_KEY` |
| `oauth2_scheme` | `dependencies.py` | Reads the `Authorization: Bearer` header. Returns 401 "Not authenticated" if it's missing. `tokenUrl="auth/login"` powers the Authorize button |
| `get_current_user()` | `dependencies.py` | Decodes the token and loads the user. Any failure (bad signature, expired, missing `sub`, deleted user) returns the same 401 |
| `get_owned_task()` | `main.py` | Looks a task up by ID **and** owner. Returns 404 if either doesn't match |

**Adding auth to an endpoint** takes one parameter: `current_user: models.User = Depends(get_current_user)`. Leave it off, and the endpoint is open to anyone.

### Why the server can trust a token it never stored

A JWT has three parts separated by dots: **header . payload . signature**. The signature is a scramble of the header, the payload, and `SECRET_KEY`. When a token comes back, the server recomputes the signature and checks that it matches. Change anything in the payload (like `sub` or `exp`) and it won't match. Making a valid signature for a changed payload requires the secret key.

**Signed, not encrypted.** Anyone can read a token's payload (try pasting one into jwt.io). They just can't change it. Never put anything secret in a token.

### What the Authorize button does

It calls `/auth/login` with your form, keeps the token in that browser tab's memory, and adds the `Authorization` header to every request. Logout just throws the token away. The React frontend will do the same thing in Phase 7.

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

### Auth

**404, not 403, for other people's tasks.** A 403 ("forbidden") would admit the task exists. A 404 gives nothing away, so nobody can probe which task IDs are real.

**One login error for every failure.** A wrong password and an unknown email both get "Incorrect email or password." Different messages would let someone find out which emails have accounts (*user enumeration*). Same idea in `get_current_user`: every kind of bad token gets the same 401.

**The secret key lives in `.env`, not in code.** Anyone with the key can forge a login as any user. In Phase 10, the hosting service sets it as an environment variable, and the code doesn't change.

**The server fails loudly without a key.** `security.py` raises an error at startup if `SECRET_KEY` is missing, rather than quietly running with no key.

**Emails are stored lowercase**, so `Dustin@Example.com` and `dustin@example.com` are the same account.

**The login endpoint uses the OAuth2 standard form** (`username` and `password` form fields, not JSON). Following the standard is what makes the Authorize button in `/docs` work, and it's what most auth tooling expects.

**`security.py` has no database code; `dependencies.py` does.** Hashing and token helpers stay pure and easy to test. Anything that needs FastAPI or the database goes in `dependencies.py`.

**Ownership is checked in the query itself.** `get_owned_task()` filters by task ID and `user_id` together, so another user's task is never loaded at all.

### Tasks and streaks

**Every task behaves the same.** No caps, no task types. Any task can be checked off any number of times in its interval, and the only per-task setting is `interval`. (An earlier version had a `frequency_type`, then an `allow_multiple` flag. Both were removed once the rule became "every check-off counts.")

**Derived data, not stored counters.** There's no count column. The completions table is the single source of truth, and streaks and counts are calculated from it when needed. A stored counter would need a scheduled job to reset it every day, week, month, and year, and it could drift out of sync with the real history. If calculating ever gets slow, the fix is caching, not storing.

**Database code in `main.py`, math in `streaks.py`.** The stats endpoint pulls the completion dates and hands them to `calculate_stats()`, which only knows about lists of dates.

**Weeks start on Monday.** That's the ISO standard and Python's default. To switch to Sunday, only `start_of_week` changes.

### General

**Models vs. schemas.** Models (`models.py`) describe the database. Schemas (`schemas.py`) describe what the API accepts and returns. That's how `UserCreate` takes a plain password the database never sees, and `UserRead` leaves out `hashed_password` so it can't be returned by accident.

**Validation in the schema.** A `field_validator` checks `interval` against `INTERVALS`, and `Field(min_length=8)` enforces password length. Bad input gets a 422 before any endpoint code runs.

**Dependencies for things every request needs.** `get_db()` gives each request a fresh session and always closes it. `get_current_user()` builds on top of it. FastAPI resolves the whole chain automatically.

**`default` vs. `server_default`.** `default=date.today` means Python fills in the value. `server_default` hands the value to the database as SQL, so it only accepts SQL like `func.now()`, never a Python function.

**Timezones (on the radar).** "Today" uses the server's clock for now. Worth revisiting once real users exist, since a 9pm check-off in California can land on tomorrow in UTC. Token expirations already use UTC.

**`create_all()` for now, Alembic later.** Fine while the only data is test data. Once real data exists, Alembic migrations can change tables without deleting anything.

**Pydantic v2 style.** Use `model_config = {"from_attributes": True}`, not the old v1 `class Config: orm_mode = True`. Also `.model_dump()` instead of `.dict()`. Lots of tutorials online still show v1.

---

## Where things stand

**Current phase: Phases 0 through 5 are done. Phase 6 (frontend skeleton) is next.** The backend API is complete for a first version.

| Phase | Status |
|---|---|
| 0. Dev environment | ✅ Done |
| 1. Git, GitHub, folder layout | ✅ Done |
| 2. FastAPI skeleton | ✅ Done |
| 3. Database layer | ✅ Done |
| 4. Task CRUD API | ✅ Done |
| 5. User auth | ✅ Done |
| 6. Frontend skeleton | ⬜ Next |
| 7. Connect frontend to backend | ⬜ |
| 8. Dashboard and visualization | ⬜ |
| 9. Containerize | ⬜ |
| 10. Deploy online | ⬜ |
| 11. Polish | ⬜ |

**Phase 4 recap:**

- [x] `get_db()` session dependency
- [x] Create, list, and delete tasks
- [x] Completion endpoint
- [x] Intervals: day, week, month, year, defined in one place
- [x] Stats endpoint with streak and period count

**Phase 5 recap:**

- [x] pwdlib (Argon2), PyJWT, and python-multipart installed
- [x] `SECRET_KEY` in `backend/.env`
- [x] `security.py`: hashing and token helpers
- [x] `POST /auth/register` and `POST /auth/login`
- [x] `get_current_user` dependency and `GET /auth/me`
- [x] All task endpoints require login and only touch the user's own tasks
- [x] Hardcoded `user_id=1` removed
- [x] Tested with two users: no cross-user access

---

## Known gaps

None of these block Phase 6. Most get picked up in Phase 11 (Polish) or whenever they start to matter.

**Features:**
- No way to undo an accidental check-off. A `DELETE /completions/{id}` endpoint would cover it (with the same ownership check).
- No way to edit a task's title or interval. A `PATCH /tasks/{task_id}` endpoint would cover it.

**Auth:**
- Tokens last 60 minutes, and there's no refresh. After an hour, you log in again. Fine for now. Refresh tokens are a later upgrade.
- Logout only happens on the client side. A token stays valid until it expires, even after "logging out." That's normal for simple JWT setups.
- The email field isn't checked for a valid email format. Pydantic's `EmailStr` (needs the `email-validator` package) would add that.
- No limit on login attempts, so someone could guess passwords quickly. Rate limiting is a deployment-time concern.

**Code:**
- `database.py` has a typo in a variable name: `SQLALCHEMY_DATABAS_URL` (missing the E). It works because it's spelled the same both times, but it's worth fixing.
- No automated tests yet. `streaks.py` and `security.py` are the easiest first candidates for pytest, since neither touches the database.
- `main.py` is getting long. FastAPI's `APIRouter` can split it into `routers/auth.py` and `routers/tasks.py` when it starts feeling crowded.

---

## What's next

### Phase 6: Frontend skeleton

- Create a React + Vite app in `log-dog/frontend/`
- Learn the basic project layout: `index.html`, `src/main.jsx`, components
- Add React Router with a login page, a register page, and a dashboard page
- Build the login and register forms (not wired to the API yet)
- Rough out the dashboard layout with fake data: a task list, and a placeholder dog with a number inside

### Phase 7: Connect frontend to backend (preview)

- **Enable CORS in FastAPI.** The frontend runs on a different port (Vite's dev server, usually 5173), and browsers block cross-port requests unless the API allows them. This is the first thing that will break, and it's a one-time setup.
- Log in from the UI, keep the token, and attach the `Authorization` header to every request
- Load the real task list, create and delete tasks, check them off
- Show real streaks and counts from `/tasks/{id}/stats`

---

## Full roadmap

0. **Dev environment.** Node via nvm, Python venv, Git config, VS Code extensions.
1. **Version control.** Git, GitHub, one repo for frontend and backend.
2. **Backend skeleton.** Minimal FastAPI app with a health check.
3. **Database layer.** Schema design, SQLAlchemy models, SQLite.
4. **Task CRUD API.** Create, list, delete, log completions, stats.
5. **User auth.** Registration, login, password hashing, JWT, protected routes.
6. **Frontend skeleton.** React + Vite, routing, login and dashboard pages.
7. **Connect frontend to backend.** CORS, auth flow in the UI, real task list, add and delete.
8. **Dashboard and visualization.** The dachshund, streaks, history chart or heatmap.
9. **Containerize.** Dockerfiles, docker-compose, swap SQLite for Postgres. Docker isn't installed on the dev machine yet.
10. **Deploy online.** Hosting, environment variables (including `SECRET_KEY`), basic CI/CD.
11. **Polish.** Tests, error handling, final README.

Possible extras along the way: Alembic migrations, splitting `main.py` into routers, undo and edit endpoints.

---

## Lessons learned so far

### Python and debugging

- **Read the error before the code.** Start at the bottom of a traceback for the actual complaint, then find the last line that points at your own project.
- **Code inside a function only runs when the function is called.** A broken endpoint can sit there silently while the server starts fine.
- **`date` vs. `Date`:** lowercase `date` is Python's date class (`from datetime import date`). Capital `Date` is SQLAlchemy's column type. Different imports.
- **`date.today` vs. `date.today()`:** without parentheses you're passing the function to be called later (a column default). With parentheses you're calling it right now.
- **Functions are values.** They can be stored in a dictionary and looked up by name, which is how `INTERVALS` works.
- **The Python shell (`>>>`) is for one-off commands.** Setup steps like creating a user don't belong in a file.

### Databases and SQLAlchemy

- **"Failed to locate a name"** almost always means a typo or wrong capitalization in a `relationship()` string.
- **`Base`** collects table blueprints from every class that inherits from it, and `create_all()` builds them. That's why `main.py` has to import `models` even though it looks unused.
- **A session** is a Python object holding a borrowed connection, a map of objects it's tracking, and an open transaction. `add()` stages, `commit()` saves, `close()` throws away anything uncommitted.
- **SQLite can reuse IDs.** Without AUTOINCREMENT, a new row gets the highest existing ID plus one, so deleting the newest row frees its ID.
- **Derive, don't duplicate.** If a number can be calculated from data you already have, calculate it.

### APIs and auth

- **Status codes matter:** 200 OK, 201 created, 204 deleted with nothing to return, 401 not logged in, 404 not found, 409 conflict, 422 invalid input.
- **HTTP is stateless.** Every request has to carry its own proof of who's asking. That's what the `Authorization` header is for.
- **Headers are labeled extra info on a request,** separate from the body.
- **A JWT is signed, not encrypted.** Anyone can read it. Nobody can change it without the secret key.
- **Never store real passwords.** Hash them, then compare hashes at login.
- **Secrets go in `.env`,** never in code or on GitHub.
- **Dependencies can depend on other dependencies.** FastAPI works out the chain.

### Linux and tooling

- **Moving a project folder breaks the venv**, since a venv stores absolute paths. Delete it and recreate it.
- **`sudo echo ... >> file` doesn't work** because the `>>` runs as you, not as root. Use `sudo sh -c '...'` instead.
- **"Connection reset by peer" can mean broken IPv6.** Test with `curl -4` and `curl -6` to tell which one is failing.
- **Run `sudo apt update` before `apt install`** on a machine that hasn't been updated in a while.
- **Commit early and often.** Look at `git status` before every commit.