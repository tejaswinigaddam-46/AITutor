import numpy as np
from psycopg2.extras import Json, RealDictCursor
from app.db.session import db_session

class VectorStore:
    def insert_chunk(self, chunk_data: dict):
        """
        Inserts a single document chunk into the database.
        """
        query = """
        INSERT INTO document_chunks (
            curriculum_book_name, document_id, book_name, chapter, page_number,
            chunk_index, total_chunks, content, embedding, chunk_metadata, content_hash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        embedding = chunk_data.get('embedding')
        if isinstance(embedding, list):
            embedding = np.array(embedding)
            
        params = (
            chunk_data['curriculum_book_name'],
            chunk_data['document_id'],
            chunk_data.get('book_name'),
            chunk_data.get('chapter'),
            chunk_data.get('page_number'),
            chunk_data['chunk_index'],
            chunk_data['total_chunks'],
            chunk_data['content'],
            embedding,
            Json(chunk_data.get('chunk_metadata', {})),
            chunk_data.get('content_hash')
        )

        with db_session.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                new_id = cursor.fetchone()[0]
                conn.commit()
                return new_id

    def similarity_search(self, query_embedding, limit=5, book_name=None):
        """
        Performs a vector similarity search (cosine distance).
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
            
        query = """
        SELECT id, curriculum_book_name, document_id, book_name, chapter, page_number, 
               chunk_index, total_chunks, content, chunk_metadata, 
               (embedding <=> %s) AS distance
        FROM document_chunks
        """
        params = [query_embedding]
        
        if book_name:
            query += " WHERE curriculum_book_name = %s"
            params.append(book_name)
            
        query += " ORDER BY distance ASC LIMIT %s;"
        params.append(limit)
        
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(params))
                return cursor.fetchall()

    def get_chunk(self, chunk_id: int):
        """Retrieves a document chunk by its ID."""
        query = "SELECT * FROM document_chunks WHERE id = %s;"
        with db_session.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (chunk_id,))
                return cursor.fetchone()

vector_store = VectorStore()
