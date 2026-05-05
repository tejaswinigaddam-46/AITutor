from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentStatus
from app.modules.orchestration.document_service import document_service
import json

router = APIRouter()

@router.post("/upload", response_model=DocumentStatus)
async def upload_document(
    curriculum_book_name: str,
    document_id: int,
    subject: str,
    json_file: UploadFile = File(...),
    md_file: UploadFile = File(...)
):
    try:
        json_data = json.load(json_file.file)
        md_content = (await md_file.read()).decode("utf-8")
        
        result = await document_service.process_and_store_document(
            curriculum_book_name, document_id, subject, json_data, md_content
        )
        return {"filename": md_file.filename, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list)
async def list_documents():
    """
    List all documents in the vector store (grouped by curriculum_book_name).
    """
    try:
        from app.db.session import db_session
        from psycopg2.extras import RealDictCursor
        
        # The schema uses curriculum_book_name but doesn't have a 'subject' column directly
        # It's an enum, so we just get the unique names
        query = "SELECT DISTINCT curriculum_book_name FROM document_chunks;"
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                # Map results to include a fallback subject for now since it's not in the table
                for row in results:
                    row['subject'] = row['curriculum_book_name'].split('_')[-1].capitalize()
                return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
