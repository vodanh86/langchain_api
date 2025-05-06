from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader, UnstructuredPowerPointLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from typing import List
import pytesseract
from pdf2image import convert_from_path
from langchain_core.documents import Document
from hvac_util import get_azure_openai_config

# Lấy cấu hình từ Azure OpenAI
azure_config = get_azure_openai_config()

# Cấu hình OpenAIEmbeddings để sử dụng Azure OpenAI
embedding_function = AzureOpenAIEmbeddings(
    model="text_embedding_ada_002",
    # dimensions: Optional[int] = None, # Can specify dimensions with new text-embedding-3 models
    # openai_api_version=..., # If not provided, will read env variable AZURE_OPENAI_API_VERSION
)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200, length_function=len)
vectorstore = Chroma(persist_directory="./data/chroma_db", embedding_function=embedding_function)

def load_and_split_document(file_path: str):
    if file_path.endswith('.pdf'):
        try:
            # Thử tải bằng loader bình thường
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            # Nếu không có nội dung, fallback sang OCR
            if not documents or all(len(doc.page_content.strip()) == 0 for doc in documents):
                raise ValueError("Empty text content")
        except Exception:
            print("Falling back to OCR for scanned PDF...")
            # OCR xử lý
            images = convert_from_path(file_path)
            text = ""
            for i, image in enumerate(images):
                image_text = pytesseract.image_to_string(image, lang='vie')
                print(image_text)
                text += image_text
                text += "\n\n--- Page Break ---\n\n"
            print(text)
            documents = [Document(page_content=text, metadata={"source": file_path})]
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.pptx'):
        loader = UnstructuredPowerPointLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.xlsx'):
        loader = UnstructuredExcelLoader(file_path)
        documents = loader.load()
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
    
    return text_splitter.split_documents(documents)

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)
        # Add metadata to each split
        for split in splits:
            split.metadata['file_id'] = file_id
        vectorstore.add_documents(splits)
        # vectorstore.persist()
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        
        vectorstore._collection.delete(where={"file_id": file_id})
        print(f"Deleted all documents with file_id {file_id}")
        
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False
