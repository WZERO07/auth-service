# Auth Service

A lightweight authentication REST API built with FastAPI, providing user
registration and JWT-based login with secure password hashing and SQLite
persistence.

## Features

- User registration with hashed password storage (bcrypt via passlib)
- Login with JWT (JSON Web Token) issuance on valid credentials
- Input validation via Pydantic (valid email, password requirements)
- SQLite persistence via SQLAlchemy

## Tech Stack

| Tool | Purpose |
|------|---------|
| **FastAPI** | Web framework for building the REST API |
| **Uvicorn** | ASGI server that runs the application |
| **SQLAlchemy** | ORM for interacting with the SQLite database |
| **SQLite** | Lightweight, file-based database used for persistence |
| **Pydantic** | Data validation and serialization for request/response schemas |
| **Passlib (bcrypt)** | Secure password hashing |
| **python-jose** | JWT creation and signing |

## Requirements

- Python 3.10 or higher

## Setup

1. Clone the repository:
```bash
   git clone <https://github.com/WZERO07/auth-service.git>
   cd auth-service
```

2. Create a virtual environment:
```bash
   python3 -m venv venv
```

3. Activate it:
   - Linux/macOS: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

4. Install the dependencies:
```bash
   pip install -r requirements.txt
```

## Running the project

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`, and the interactive
documentation (Swagger UI) at `http://localhost:8000/docs` — the easiest
way to try the endpoints without a separate HTTP client.

## API Endpoints

### `POST /register`

Creates a new user.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com"
}
```

### `POST /login`

Validates credentials and returns a JWT.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

## Notes

- The JWT `SECRET_KEY` is currently a hardcoded constant in `app/security.py`,
  intended for local development. In a production deployment, this should be
  loaded from an environment variable instead.
- The SQLite database file (`app.db`) is created automatically on first run
  and is not committed to version control (see `.gitignore`).

  ## Roadmap
- [x] Registration & login with JWT
- [ ] Protected routes with token validation
- [ ] Refresh tokens & logout
- [ ] Role-based authorization
- [ ] PostgreSQL, migrations, containerization
