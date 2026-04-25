from pydantic import BaseModel

class DocumentStatus(BaseModel):
    filename: str
    status: str
