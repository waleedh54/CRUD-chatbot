#  Admin Chatbot — User Management via Natural Language
A full-stack chatbot application that lets **admins manage users** (add, update, delete) using plain English commands. It uses a **hybrid NLU pipeline** — an LLM (NVIDIA-hosted Llama 3.1) as the primary intent parser with a regex-based rule parser as fallback — backed by a FastAPI REST API and a lightweight HTML/JS frontend.

---

##  Features

-  **Admin Authentication** — JWT-based login; only pre-approved admin emails can sign in
-  **Natural Language Interface** — type commands like *"Add john@example.com with phone +923001234567"*
-  **Hybrid NLU Pipeline** — LLM-first parsing with automatic fallback to regex rule parser
- **Multi-intent Support** — handle multiple actions in a single message
-  **SQLite Persistence** — lightweight database with SQLAlchemy ORM
- **Plain HTML/JS Frontend** — no build step required; open directly in the browser

---

## Project Structure

```
Chatbot task/
├── backend/
│   ├── main.py            # FastAPI app, routes, CORS, startup seeding
│   ├── auth.py            # JWT creation & verification
│   ├── crud.py            # Database operations (create/read/update/delete)
│   ├── database.py        # SQLAlchemy engine & session
│   ├── models.py          # ORM models (Admin, User)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── requirements.txt   # Python dependencies
│   ├── .env               # Environment variables (API keys, secrets)
│   └── nlu/
│       ├── intent_handler.py  # Orchestrates LLM → rule fallback pipeline
│       ├── llm_parser.py      # NVIDIA / OpenAI-compatible LLM parser
│       └── rule_parser.py     # Regex-based fallback parser
└── frontend/
    ├── index.html         # Chat UI (protected, requires login)
    ├── login.html         # Admin login page
    ├── app.js             # Frontend logic (auth, chat, API calls)
    └── style.css          # Styling
```

---

##  Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Python · FastAPI · Uvicorn |
| Auth       | JWT (`python-jose`) |
| Database   | SQLite · SQLAlchemy |
| NLU (LLM)  | NVIDIA API · Llama 3.1 8B Instruct (via OpenAI-compatible client) |
| NLU (Fallback) | Regex rule parser |
| Frontend   | Vanilla HTML · CSS · JavaScript |

---

##  How to Run

### Prerequisites

- **Python 3.10+** installed and on your PATH
- An **NVIDIA API key** (or any OpenAI-compatible endpoint)

---

### 1. Clone / Open the Project

```powershell
cd "d:\Chatbot task"
```

---

### 2. Set Up the Backend

```powershell
cd backend

# (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Edit `backend/.env` to match your setup:

```env
# NVIDIA (or OpenAI-compatible) LLM credentials
NVIDIA_API_KEY=your_api_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.1-8b-instruct

# JWT secret & token expiry
SECRET_KEY=change_this_to_a_strong_random_string
ACCESS_TOKEN_EXPIRE_MINUTES=120

# SQLite database path
DATABASE_URL=sqlite:///./chatbot.db

# Comma-separated admin emails allowed to log in
ADMIN_EMAILS=admin1@company.com,admin2@company.com
```

> **Note:** The emails listed in `ADMIN_EMAILS` are automatically seeded into the database on startup. Only these emails can log in.

---

### 4. Start the Backend Server

```powershell
# From the backend/ directory (with venv active)
uvicorn main:app --reload
```

The API will be available at **`http://127.0.0.1:8000`**.

You can explore the interactive API docs at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

### 5. Open the Frontend

No build step needed — just open the login page directly in your browser:

```
d:\Chatbot task\frontend\login.html
```

Or navigate to it via **File → Open File** in your browser.

---

### 6. Log In & Chat

1. Enter one of the admin emails listed in your `ADMIN_EMAILS` env variable
2. Click **Login**
3. Start chatting! Try commands like:

| Example Command | What it does |
|----------------|--------------|
| `Add user john@example.com` | Registers a new user |
| `Add john@example.com with phone +923001234567` | Adds a user with extra fields |
| `Delete the user jane@example.com` | Removes a user by email |
| `Update bob@example.com set phone to +1234567890` | Updates a user's field |
| `Remove John Smith` | Deletes a user by name |

---

## 🔑 API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| `POST` | `/auth/login` | ❌ | Login with admin email, get JWT token |
| `POST` | `/chat` | ✅ | Send a natural-language message |
| `GET` | `/users` | ✅ | List all registered users |
| `GET` | `/health` | ❌ | Health check |

---

## 🧠 How the NLU Pipeline Works

```
User Message
     │
     ▼
 LLM Parser (NVIDIA Llama 3.1)
     │ success? → extract intent(s) → execute → reply
     │ fails?
     ▼
 Rule Parser (Regex)
     │ → extract intent → execute → reply
```

1. **LLM Parser** sends the message to a Llama 3.1 model and parses the JSON response for `action`, `email`, `name`, and `fields`.
2. If the LLM call fails or returns an unexpected format, the **Rule Parser** uses regular expressions to detect `add`, `delete`, or `update` intents.
3. Extracted intents are executed against the SQLite database via CRUD operations.

---

## 🛠️ Development Tips

- **Hot reload** is enabled via `--reload` in Uvicorn — the server restarts automatically on code changes.
- Logs include the NLU source (`llm` or `rule`) and intent details to help with debugging.
- The SQLite database file (`chatbot.db`) is created automatically on first run inside the `backend/` directory.
- To reset the database, simply delete `backend/chatbot.db` and restart the server.
