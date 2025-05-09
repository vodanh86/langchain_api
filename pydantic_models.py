from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ModelName(str, Enum):
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.GPT4_O_MINI)

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName
    contexts: str

class DocumentInfo(BaseModel):
    id: int
    filename: str
    dept_id: int
    upload_link: str
    effective_date: str
    upload_timestamp: str

class DeleteFileRequest(BaseModel):
    file_id: int
    dept_id: int