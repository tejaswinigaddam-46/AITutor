# AI Tutor - RAG Application

A comprehensive AI-powered tutor application built with a FastAPI backend and a React (Vite) frontend. This project implements a Retrieval-Augmented Generation (RAG) pipeline to provide intelligent tutoring based on uploaded documents.

---

## 🚀 Features

- **Document Management**: Upload and manage educational documents.
- **RAG Pipeline**: Advanced Retrieval-Augmented Generation using LangChain and Vector Databases.
- **Secure API**: Protected by API Key authentication and restricted CORS.
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS.
- **Flexible Vector Storage**: Support for multiple vector databases including PGVector and ChromaDB.

---

## 📂 Project Structure

```text
AITutor/
├── backend/                         # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/                  # Versioned API routes (ai, documents, conversations, questions)
│   │   ├── core/                    # Settings + security (API key, JWT, CORS)
│   │   ├── db/                      # DB/session/vector DB wiring
│   │   ├── modules/                 # Orchestration + LLM + RAG logic
│   │   ├── schemas/                 # Pydantic schemas
│   │   └── main.py                  # FastAPI app entrypoint
│   ├── tests/                       # Backend tests
│   ├── .env.example                 # Backend env template
│   └── requirements.txt             # Python dependencies
├── frontend/                        # React + Vite application
│   ├── public/                      # Static assets
│   ├── src/
│   │   ├── App.jsx                  # Main UI
│   │   └── api.js                   # Axios client + API calls
│   ├── vite.config.js               # Vite dev server config
│   └── package.json                 # Frontend dependencies and scripts
└── Readme.md                        # Project documentation (you are here)
```

---

## 🛠️ Getting Started

### Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+
- **Database**: PostgreSQL with `pgvector` extension 

---

### 1. Backend Setup

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Copy the example environment file and update it with your keys:
    ```bash
    cp .env.example .env
    ```
    Key variables to set:
    - `API_KEY`: Your custom security key for API access.
    - `EMBEDDING_API_KEY` / `GROQ_API_KEY`: For AI services.
    - `DB_*`: Database credentials.

5.  **Run the Backend**:
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.
    
    Primary base path (versioned): `http://localhost:8000/api/v1`

---

### 2. Frontend Setup

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Configure Environment Variables**:
    Create a `.env` file in the `frontend` folder:
    ```bash
    VITE_API_URL=http://localhost:8000/api/v1
    VITE_API_KEY=your-super-secret-api-key
    ```
    Ensure your backend CORS allows the Vite origin (default: `http://localhost:5173`).

4.  **Run the Frontend**:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## 🧪 Testing

### Backend
Run tests using `pytest`:
```bash
cd backend
pytest
```

---

## 🔒 Security

- **API Security**: All endpoints require an `X-API-KEY` header.
- **CORS**: Configured to only allow requests from trusted origins defined in the backend `.env`.

---

## 🧰 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/), [LangChain](https://www.langchain.com/), [Pydantic](https://docs.pydantic.dev/), [OpenAI/Groq](https://openai.com/).
- **Frontend**: [React](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Lucide React](https://lucide.dev/).
- **Storage**: [PostgreSQL](https://www.postgresql.org/) + [PGVector](https://github.com/pgvector/pgvector), [ChromaDB](https://www.trychroma.com/).

---

## 📄 License

[Specify License here, e.g., MIT]
