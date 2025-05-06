from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record, increment_user_question_count, get_user_question_count
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import uuid
import json
import logging

logging.basicConfig(filename='data/app.log', level=logging.INFO)
app = FastAPI()

# Lấy giới hạn số câu hỏi từ file .env
MAX_QUESTIONS_PER_DAY = int(os.getenv("MAX_QUESTIONS_PER_DAY", 10))

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):

    user_id = query_input.session_id  # Giả sử `user_id` là một trường trong request
    print("user id " + str(user_id))
    session_id = query_input.session_id
    logging.info(
        f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    # Kiểm tra số lượng câu hỏi của người dùng
    question_count = get_user_question_count(user_id) if user_id else 0
    print("question count " + str(question_count))
    if question_count >= MAX_QUESTIONS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"You have reached the daily limit of {MAX_QUESTIONS_PER_DAY} questions."
        )

    # Tăng số lượng câu hỏi của người dùng
    increment_user_question_count(user_id)

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })

    contexts = answer["context"]
    references = []
    for context in contexts:
        metadata = context.metadata
        #references.append(f"Trang: {metadata['page']}, Tài liệu: {metadata['source']}\n")

    answer = answer['answer']
    #answer = answer['answer'] + "\n\n" + "\n".join(references)
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, contexts = str(contexts), session_id=session_id, model=query_input.model)

from fastapi import UploadFile, File, HTTPException
import os
import shutil

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ["pdf", "docx", "html", "txt", "csv", "json", "xlsx", "xlsx", "pptx"]
    file_extension = os.path.splitext(file.filename)[1].lower().strip(".")
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")
    
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}
