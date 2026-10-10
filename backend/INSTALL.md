# TRACE Backend - Installation Guide

## Prerequisites

- **Python 3.11 or higher** - Check with `python --version`
- **pip** package manager
- **Git** (optional, for version control)

## Step-by-Step Installation

### 1. Navigate to Backend Directory

Open Command Prompt or PowerShell:

```cmd
cd c:\Users\adity\codes\TRACE\backend
```

### 2. Create Virtual Environment

```cmd
python -m venv venv
```

This creates an isolated Python environment in the `venv` folder.

### 3. Activate Virtual Environment

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### 4. Install Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

This installs all required packages:
- FastAPI, Uvicorn
- SQLAlchemy, Pydantic
- Pandas, OpenPyXL, PyMuPDF
- LangChain, Google Generative AI
- Testing tools (pytest)

**Note:** This may take 2-5 minutes depending on your connection.

### 5. Configure Environment

Copy the example environment file:

```cmd
copy ..\.env.example ..\.env
```

Edit `.env` file (in the TRACE root directory) to set:
```
SECRET_KEY=your-secure-secret-key-minimum-32-characters-long
GEMINI_API_KEY=your-api-key-if-using-llm
LLM_ENABLED=false
```

### 6. Initialize Database

The database will auto-initialize on first run, or manually:

```cmd
python -c "from app.db.database import init_db; init_db()"
```

### 7. Seed Demo Data

```cmd
python scripts\seed_data.py
```

This creates:
- 4 demo users (one per role)
- Sample engagement
- Compliance references
- Anomaly ground truth manifest

### 8. Run the Server

```cmd
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use the convenience script:
```cmd
run_server.bat
```

### 9. Verify Installation

Open browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "llm_available": false,
  "ocr_available": false
}
```

## Testing the System

### 1. Run All Tests

```cmd
pytest
```

### 2. Run with Coverage

```cmd
pytest --cov=app --cov-report=html
```

View coverage report: Open `htmlcov\index.html` in browser

### 3. Test Authentication

Login as client:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"client_user\",\"password\":\"password123\"}"
```

## Optional: Enable OCR

### Windows
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR\`
3. Add to PATH: `C:\Program Files\Tesseract-OCR\`
4. Verify: `tesseract --version`

### macOS
```bash
brew install tesseract
```

### Linux
```bash
sudo apt-get install tesseract-ocr
```

## Optional: Enable LLM

1. Get API key from https://makersuite.google.com/app/apikey
2. Update `.env`:
   ```
   GEMINI_API_KEY=your-key-here
   LLM_ENABLED=true
   ```
3. Restart server

## Troubleshooting

### Issue: "python not found"
- Ensure Python 3.11+ is installed
- Try `python3` instead of `python`
- Add Python to PATH

### Issue: "pip not found"  
```cmd
python -m ensurepip --upgrade
```

### Issue: "Module not found"
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue: "Permission denied on venv"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "Database locked"
- SQLite doesn't handle concurrent writes well
- For production, use PostgreSQL
- For dev, ensure only one process accesses DB

### Issue: "Port 8000 already in use"
```cmd
# Use different port
uvicorn main:app --reload --port 8001
```

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs
2. **Test Authentication**: Login with demo users
3. **Create Engagement**: POST to `/api/v1/engagements/`
4. **Upload Files**: POST to `/api/v1/uploads/{engagement_id}/upload`
5. **Review Documentation**: See README.md for API details

## Demo Users

| Username | Password | Role |
|----------|----------|------|
| client_user | password123 | CLIENT_EMPLOYEE |
| ai_auditor | password123 | INDEPENDENT_AI_AUDITOR |
| human_auditor | password123 | HUMAN_AUDITOR |
| admin_user | password123 | PLATFORM_ADMIN |

**⚠️ SECURITY WARNING**: Change these passwords before production deployment!

## Development Workflow

1. Activate venv: `venv\Scripts\activate.bat`
2. Make code changes
3. Run tests: `pytest`
4. Start server: `uvicorn main:app --reload`
5. Test in browser/Postman

## Production Deployment Checklist

- [ ] Change SECRET_KEY to strong random value
- [ ] Change all default passwords
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper CORS origins
- [ ] Set up backup strategy
- [ ] Enable logging and monitoring
- [ ] Review and harden file upload limits
- [ ] Implement rate limiting
- [ ] Set up database migrations

## Support

For issues or questions, refer to:
- README.md for system overview
- Project specification files in root (AGENT.md, IDEA.md, etc.)
- API documentation at /docs endpoint
