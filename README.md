# Web Application for Competitive Keyword Analysis

A full-stack application for competitive keyword analysis built with **FastAPI** (backend) and **React + Vite** (frontend).

## Project Structure

```
├── apps/
│   ├── api/          # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/        # API routes
│   │   │   ├── core/       # Config and settings
│   │   │   ├── db/         # Database session
│   │   │   ├── schemas/    # Pydantic schemas
│   │   │   ├── services/   # Business logic
│   │   │   └── main.py     # App entrypoint
│   │   └── requirements.txt
│   └── web/          # React frontend
│       ├── src/
│       └── package.json
└── infra/            # Infrastructure configs
```

## Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **npm** or **yarn**

---

## Backend Setup (FastAPI)

### 1. Navigate to the API directory

```bash
cd apps/api
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create environment file (optional)

```bash
cp .env.example .env  # If .env.example exists
```

Or create `.env` manually with:

```env
APP_NAME=Keyword Analysis API
ENVIRONMENT=dev
CORS_ORIGINS=["http://localhost:5173"]
```

### 5. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Frontend Setup (React + Vite)

### 1. Navigate to the web directory

```bash
cd apps/web
```

### 2. Install dependencies

```bash
npm install
```

### 3. Run the development server

```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

---

## Running Both Services

For full-stack development, you need to run both services simultaneously in separate terminals:

**Terminal 1 - Backend:**
```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
npm run dev
```

---

## IDE Setup (VS Code / Cursor)

The project includes configuration files for proper Python interpreter resolution:

- `.vscode/settings.json` - VS Code/Cursor settings
- `pyrightconfig.json` - Pylance language server config

These ensure that import resolution works correctly when opening the project.

**If you see import errors**, run:
1. `Cmd+Shift+P` (or `Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `./apps/api/.venv/bin/python`

---

## Tech Stack

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

### Frontend
- [React 19](https://react.dev/) - UI library
- [Vite](https://vitejs.dev/) - Build tool
- [TypeScript](https://www.typescriptlang.org/) - Type safety

---

## License

MIT
