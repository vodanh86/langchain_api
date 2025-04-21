import sqlite3
from datetime import datetime
import logging

logging.basicConfig(filename='data/db.log', level=logging.INFO)
DB_NAME = "data/rag_app.db"

def get_db_connection():
    logging.info("Establishing database connection.")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_application_logs():
    logging.info("Creating table 'application_logs' if it does not exist.")
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
    logging.info(f"Inserting log into 'application_logs': session_id={session_id}, user_query={user_query}, model={model}")
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                 (session_id, user_query, gpt_response, model))
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    logging.info(f"Fetching chat history for session_id={session_id}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    conn.close()
    return messages

def create_document_store():
    logging.info("Creating table 'document_store' if it does not exist.")
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def insert_document_record(filename):
    logging.info(f"Inserting document record into 'document_store': filename={filename}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store (filename) VALUES (?)', (filename,))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"Document record inserted with id={file_id}.")
    return file_id

def delete_document_record(file_id):
    logging.info(f"Deleting document record from 'document_store': file_id={file_id}.")
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    logging.info(f"Document record with id={file_id} deleted successfully.")
    return True

def get_all_documents():
    logging.info("Fetching all documents from 'document_store'.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = cursor.fetchall()
    conn.close()
    logging.info(f"Fetched {len(documents)} documents.")
    return [dict(doc) for doc in documents]

# Initialize the database tables
create_application_logs()
create_document_store()