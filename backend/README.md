# AI Tutor Backend - Production RAG

This is the production-ready backend for the AI Tutor application, built with FastAPI and designed for RAG (Retrieval-Augmented Generation).

## Structure

- `app/`: Main application code
  - `api/`: API routes and endpoints
  - `core/`: Configuration and security
  - `db/`: Database connections and vector store logic
  - `models/`: Database models
  - `schemas/`: Pydantic models for request/response
  - `services/`: Business logic (RAG, Embeddings, LLM)
- `tests/`: Unit and integration tests
- `data/`: Local storage for vector database and documents

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and security settings
   ```

## Security

The API is protected by an API Key requirement.
- Header: `X-API-KEY`
- Value: (Set in your `.env` file)

CORS is restricted to the origins specified in `BACKEND_CORS_ORIGINS`.

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
