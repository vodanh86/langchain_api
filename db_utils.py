import sqlite3
from datetime import datetime
from logger import db_logger

DB_NAME = "data/rag_app.db"

# Dictionary lưu số lượt câu hỏi của người dùng
user_question_count = {}

def get_user_question_count(user_id: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{user_id}:{today}"
    return user_question_count.get(key, 0)

def increment_user_question_count(user_id: str):
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{user_id}:{today}"
    if key in user_question_count:
        user_question_count[key] += 1
    else:
        user_question_count[key] = 1

def get_db_connection():
    db_logger.info("Establishing database connection.")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_application_logs():
    db_logger.info("Creating table 'application_logs' if it does not exist.")
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     gpt_response TEXT,
                     model TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()


def insert_application_logs(session_id, user_query, gpt_response, model):
    db_logger.info(
        f"Inserting log into 'application_logs': session_id={session_id}, user_query={user_query}, model={model}")
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                 (session_id, user_query, gpt_response, model))
    conn.commit()
    conn.close()


def get_chat_history(session_id):
    db_logger.info(
        f"Fetching the last 10 chat history entries for session_id={session_id}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    # Truy vấn 10 câu hỏi gần nhất
    cursor.execute(
        'SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at DESC LIMIT 10', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    conn.close()
    # Đảo ngược danh sách để trả về theo thứ tự thời gian (cũ -> mới)
    messages.reverse()
    return messages


def create_document_store():
    db_logger.info("Creating table 'document_store' if it does not exist.")
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dept_id INTEGER,
                    filename TEXT,
                    upload_link TEXT,
                    effective_date TEXT,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()


def insert_document_record(dept_id, filename, upload_link, effective_date):
    db_logger.info(
        f"Inserting document record into 'document_store': filename={filename}, upload_link={upload_link}, effective_date={effective_date}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO document_store (filename, dept_id, upload_link, effective_date) VALUES (?, ?, ?, ?)",
        (filename, dept_id, upload_link, effective_date)
    )
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    db_logger.info(f"Document record inserted with id={file_id}.")
    return file_id

def get_document_by_id(file_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM document_store WHERE id = ?", (file_id,))
    document = cursor.fetchone()
    return dict(document) if document else None

def delete_document_record(file_id):
    db_logger.info(
        f"Deleting document record from 'document_store': file_id={file_id}.")
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    db_logger.info(f"Document record with id={file_id} deleted successfully.")
    return True

def get_all_documents(dept_id):
    db_logger.info("Fetching all documents from 'document_store'.")
    conn = get_db_connection()
    cursor = conn.cursor()
    if dept_id == 0:
        cursor.execute("SELECT id, filename, dept_id, upload_timestamp, upload_link, effective_date FROM document_store  ORDER BY upload_timestamp DESC")
    else:
        cursor.execute("SELECT id, filename, dept_id, upload_timestamp, upload_link, effective_date FROM document_store WHERE dept_id = ? ORDER BY upload_timestamp DESC", (dept_id,))
    documents = cursor.fetchall()
    conn.close()
    db_logger.info(f"Fetched {len(documents)} documents.")
    return [dict(doc) for doc in documents]


# Initialize the database tables
create_application_logs()
create_document_store()
