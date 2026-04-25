import json
import re
import tiktoken
from typing import List, Dict
from app.services.embedding_service import embedding_service
from app.db.vector_store import vector_store

class DocumentService:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.encoding = tiktoken.encoding_for_model(model)

    def get_tokens(self, text: str) -> List[int]:
        return self.encoding.encode(text)

    def count_tokens(self, text: str) -> int:
        return len(self.get_tokens(text))

    def extract_chapter(self, text: str) -> str:
        match = re.search(r'(?:>>|>)?\s*Chapter\s*\d+.*', text, re.IGNORECASE)
        if match:
            return match.group(0).strip(' >')
        return None

    def extract_topic(self, text: str) -> str:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            if line.startswith('<::') or line.startswith('<!--') or line.startswith('> '):
                continue
            if line.startswith('#') or line.isupper() or (len(line) < 60 and not line.startswith('*')):
                return line.strip('#* ')
        return "General Science"

    def chunk_document(self, json_data: dict, md_content: str, subject: str, target_tokens: int = 800, overlap_tokens: int = 100) -> List[dict]:
        """
        Chunks a document based on markdown anchors and token limits.
        """
        md_sections = {}
        pattern = r"<a id='([a-f0-9-]+)'></a>(.*?)(?=<a id='|$)"
        matches = re.finditer(pattern, md_content, re.DOTALL)
        for match in matches:
            md_sections[match.group(1)] = match.group(2).strip()

        json_chunks = json_data.get('chunks', [])
        enriched_chunks = []
        
        current_chunk_ids = []
        current_tokens = 0
        current_chapter = "Unknown"
        prev_context_end = ""
        
        i = 0
        while i < len(json_chunks):
            json_chunk = json_chunks[i]
            chunk_id = json_chunk['id']
            chunk_md = md_sections.get(chunk_id, json_chunk.get('markdown', ''))
            
            new_chapter = self.extract_chapter(chunk_md)
            if new_chapter:
                current_chapter = new_chapter
                
            chunk_tokens = self.count_tokens(chunk_md)
            
            if current_tokens + chunk_tokens > target_tokens and current_chunk_ids:
                enriched_chunk = self._create_enriched_chunk(
                    current_chunk_ids, json_chunks, md_sections, 
                    current_chapter, prev_context_end, len(enriched_chunks), subject
                )
                enriched_chunks.append(enriched_chunk)
                
                last_content = enriched_chunk['chunk_content']['content']
                tokens = self.get_tokens(last_content)
                overlap_text = self.encoding.decode(tokens[-overlap_tokens:])
                prev_context_end = overlap_text
                
                current_chunk_ids = []
                current_tokens = 0
                continue
            
            current_chunk_ids.append(chunk_id)
            current_tokens += chunk_tokens
            i += 1
            
        if current_chunk_ids:
            enriched_chunks.append(self._create_enriched_chunk(
                current_chunk_ids, json_chunks, md_sections, 
                current_chapter, prev_context_end, len(enriched_chunks), subject
            ))

        total = len(enriched_chunks)
        for chunk in enriched_chunks:
            chunk['metadata']['total_chunks'] = total
            
        # COMMENT: To extract chunking results to a file for debugging
        # with open("debug_chunks.json", "w") as f:
        #     json.dump(enriched_chunks, f, indent=2)
            
        return enriched_chunks

    def _create_enriched_chunk(self, chunk_ids, all_json_chunks, md_sections, chapter, prev_context_end, index, subject):
        json_subset = [c for c in all_json_chunks if c['id'] in chunk_ids]
        content_parts = [md_sections.get(cid, "") for cid in chunk_ids]
        full_content = "\n\n".join(content_parts)

        raw_types = set(c['type'] for c in json_subset)
        mapped_types = set()
        for t in raw_types:
            if t == "figure": mapped_types.add("diagram")
            elif t == "text": mapped_types.add("text")
            else: mapped_types.add(t)
        
        if re.search(r'[A-Z][a-z]?\d*|\+|→|═|≡', full_content):
            mapped_types.add("Formula")
        
        types = sorted(list(mapped_types))
        pages = list(set(c['grounding']['page'] for c in json_subset))
        pages.sort()
        
        topic = self.extract_topic(full_content)
        tokens = self.count_tokens(full_content)
        
        return {
            "metadata": {
                "chunk_id": index + 1,
                "total_chunks": 0,
                "chunk_size": tokens,
                "subject": subject,
                "chapter": chapter,
                "prev_context_end": prev_context_end,
                "topic": topic,
                "types included": types,
                "page numbers included": pages
            },
            "chunk_content": {
                "content": full_content
            }
        }

    async def process_and_store_document(self, curriculum_book_name: str, document_id: int, subject: str, json_data: dict, md_content: str):
        """
        Full pipeline: Chunk -> Embed -> Store
        """
        chunks = self.chunk_document(json_data, md_content, subject)
        
        for chunk in chunks:
            content = chunk['chunk_content']['content']
            metadata = chunk['metadata']
            
            # Embed
            embeddings = await embedding_service.get_embeddings([content])
            if not embeddings:
                continue
            
            # Store
            db_chunk = {
                "curriculum_book_name": curriculum_book_name,
                "document_id": document_id,
                "book_name": metadata.get("subject"),
                "chapter": metadata.get("chapter"),
                "page_number": metadata.get("page numbers included")[0] if metadata.get("page numbers included") else None,
                "chunk_index": metadata.get("chunk_id"),
                "total_chunks": metadata.get("total_chunks"),
                "content": content,
                "embedding": embeddings[0],
                "chunk_metadata": metadata,
                "content_hash": None # Could add hashing logic here
            }
            vector_store.insert_chunk(db_chunk)
            
        return {"status": "success", "chunks_processed": len(chunks)}

document_service = DocumentService()
