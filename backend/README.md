# Searchify.AI Backend

Backend API for Searchify.AI - An AI-powered research assistant.

## Features

- User authentication (signup, login, token-based authentication)
- User profile management
- Secure password handling with bcrypt
- JWT token-based authentication
- Database migrations with Alembic
- PostgreSQL database support

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) - High-performance web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation and settings management
- [JWT](https://jwt.io/) - JSON Web Tokens for authentication
- [Alembic](https://alembic.sqlalchemy.org/) - Database migration tool
- [PostgreSQL](https://www.postgresql.org/) - Relational database

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/searchify-backend.git
cd searchify-backend
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file based on `.env.example` and fill in your database credentials and other settings.

```
# Environment
ENVIRONMENT=development

# Database connection
DATABASE_URL=postgresql://username:password@localhost:5432/searchify

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

5. Initialize the database:

```bash
python init_db.py
```

### Running the Application

Run the application with:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API Documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/logout` - Logout (clear session)
- `GET /api/v1/auth/verify` - Verify token validity
- `GET /api/v1/users/me` - Get current user profile

### Health Check

- `GET /health` - Check API health

## Development

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Revert migrations:

```bash
alembic downgrade -1  # Go back one revision
```

## Testing

Run tests with:

```bash
pytest
```

## Security

- All passwords are hashed using bcrypt
- Authentication is handled via JWT tokens
- Environment variables are used for sensitive information
- CORS is configured to restrict access to specific origins 