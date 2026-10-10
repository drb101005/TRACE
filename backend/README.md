# TRACE Backend - AI-Run Statutory Revenue Audit

Backend API for evidence-led, reproducible, explainable AI-assisted statutory revenue audits.

## Features

- **Four-role authorization**: Client Employee, Independent AI Auditor, Human Auditor, Platform Administrator
- **Immutable uploads**: SHA-256 hashing, versioned data with provenance
- **Hybrid sampling**: Risk-based + mandatory coverage + seeded random (reproducible)
- **Audit integrity**: Append-only hash-linked event chain
- **Evidence management**: OCR support for scanned documents
- **Compliance tracking**: Versioned reference management
- **LLM-optional**: Core audit logic works without AI models

## Tech Stack

- Python 3.11+
- FastAPI + Pydantic v2
- SQLAlchemy 2 + SQLite
- Pandas, OpenPyXL, PyMuPDF
- Tesseract OCR (optional)
- LangChain + Gemini (optional)

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- pip or poetry

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` at the project root:

```bash
# From the TRACE directory
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`: Use a secure random key (minimum 32 characters)
- `GEMINI_API_KEY`: Optional, for LLM features
- `LLM_ENABLED`: Set to `true` if using LLM

### 4. Initialize Database

The database will be created automatically on first run. To manually initialize:

```bash
cd backend
python -c "from app.db.database import init_db; init_db()"
```

### 5. Seed Demo Data

```bash
cd backend
python scripts/seed_data.py
```

This creates:
- Four demo users (one per role)
- Sample engagement
- Synthetic sales data with planted anomalies

### 6. Run the Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Demo Users

After seeding, you can log in with:

| Role | Username | Password |
|------|----------|----------|
| Client Employee | client_user | password123 |
| AI Auditor | ai_auditor | password123 |
| Human Auditor | human_auditor | password123 |
| Platform Admin | admin_user | password123 |

## API Overview

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user

### Engagements
- `POST /api/v1/engagements/` - Create engagement
- `GET /api/v1/engagements/` - List engagements
- `GET /api/v1/engagements/{id}` - Get engagement details
- `PATCH /api/v1/engagements/{id}` - Update engagement

### File Uploads
- `POST /api/v1/uploads/{engagement_id}/upload` - Upload file
- `GET /api/v1/uploads/{engagement_id}/uploads` - List uploads
- `POST /api/v1/uploads/{engagement_id}/validate/{artifact_id}` - Validate file

### Health
- `GET /health` - System health and dependency status

## Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py
│   │   ├── engagements.py
│   │   ├── uploads.py
│   │   └── health.py
│   ├── agents/           # AI agent implementations
│   ├── core/             # Core utilities
│   │   ├── config.py     # Settings management
│   │   ├── security.py   # Auth & authorization
│   │   └── errors.py     # Exception handling
│   ├── db/               # Database layer
│   │   ├── database.py   # Connection & session
│   │   └── models.py     # SQLAlchemy models
│   ├── domain/           # Domain models
│   │   ├── enums.py      # Enumerations
│   │   └── schemas.py    # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── ingestion.py
│   │   ├── validation.py
│   │   ├── sampling.py
│   │   └── audit_log.py
│   └── mcp_server/       # MCP server implementation
├── data/
│   └── demo/             # Synthetic demo data
├── tests/                # Test suite
├── uploads/              # File storage (created at runtime)
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Optional: OCR Support

To enable OCR for scanned PDFs and images:

1. Install Tesseract:
   - **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

2. Install Python wrapper:
   ```bash
   pip install pytesseract
   ```

3. Verify installation:
   ```bash
   python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
   ```

## Optional: LLM Support

To enable AI agent features with Google Gemini:

1. Get API key from https://makersuite.google.com/app/apikey

2. Update `.env`:
   ```
   GEMINI_API_KEY=your-api-key-here
   LLM_ENABLED=true
   ```

3. The system will work without LLM using deterministic fallbacks

## Running Tests

```bash
cd backend
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Security Notes

- **Demo mode**: The seed script creates users with default passwords. Change these in production.
- **Secret key**: Generate a secure SECRET_KEY for production using: `openssl rand -hex 32`
- **HTTPS**: Use HTTPS in production, never expose over plain HTTP
- **File uploads**: Uploads are stored with calculated hashes to detect tampering
- **Audit chain**: All operations are logged in an append-only hash chain

## Authorization Model

| Action | Client Employee | AI Auditor | Human Auditor | Platform Admin |
|--------|----------------|------------|---------------|----------------|
| Create engagement | ✓ | ✗ | ✗ | ✓ |
| Upload files | ✓ | ✗ | ✗ | ✓ |
| View business data | Own only | ✓ | ✓ | ✓ |
| Run audit checks | ✗ | ✓ | ✓ | ✓ |
| Approve findings | ✗ | ✗ | ✓ | ✗ |
| Modify source data | ✗ | ✗ | ✗ | ✗* |

\* Platform Admin cannot modify by default; any exception requires explicit logging

## Troubleshooting

### Database locked error
SQLite may show "database is locked" with concurrent writes. This is expected in dev mode. For production, use PostgreSQL.

### Import errors
Ensure you're in the correct directory and virtual environment is activated:
```bash
cd backend
python -c "import app; print('OK')"
```

### File upload fails
Check `MAX_UPLOAD_SIZE_MB` in `.env` and ensure sufficient disk space.

## Next Steps

1. ✓ Backend structure and core services
2. ✓ Authentication and authorization
3. ✓ File upload and validation
4. TODO: Complete agent implementations
5. TODO: MCP server with tools
6. TODO: Export/report generation
7. TODO: Complete test coverage
8. TODO: Synthetic demo data with anomalies

## License

Proprietary - Hackathon Project
