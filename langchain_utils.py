import json
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain, load_summarize_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from hvac_util import get_azure_openai_config
from chroma_utils import vectorstore, load_document
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Lấy cấu hình từ Azure OpenAI
azure_config = get_azure_openai_config()
output_parser = StrOutputParser()
# Khởi tạo RAG Chain một lần
rag_chain_cache = None

# Set up prompts and chains
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

    # Prompt tùy chỉnh để tóm tắt theo đầu mục và ý nhỏ
summary_prompt = """
    You are a highly intelligent AI assistant. Summarize the following document into major headings, each with subpoints. 
    Ensure that:
    - Document name: name extraced from content
    - The summary is in Vietnamese.
    - There is no limit on the output length.
    - Major headings are numbered (1., 2., 3., ...).
    - The content is clear, complete, and accurate.

    Here is the document content:
    {text}

    Please return the summary in the requested format.
    """

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI assistant for An Binh Bank. Provide accurate, concise, and clear answers strictly based on the bank's internal guidelines and provided context. Do not make assumptions or provide information outside the given context. Always use Vietnamese. Ensure confidentiality and refer to internal documents when necessary."
    "If the user's question is relevant to the provided context, include the names of the referenced files in the response. Otherwise, do not include any file references. "
    "If user ask for list of documents, provide the Available Documents in the format: '1. Document Name 1, 2. Document Name 2, ...'"),
    ("system", "Context: {context}"),
    ("system", "Available Documents: {documents}"),  # Thêm danh sách tài liệu vào prompt
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def get_rag_chain_cached(model="gpt-4o"):
    global rag_chain_cache
    if rag_chain_cache is None:
        rag_chain_cache = get_rag_chain(model)
    return rag_chain_cache

def get_rag_chain(model):

    llm = AzureChatOpenAI(
        azure_ad_token=azure_config["api_key"],
        azure_endpoint=azure_config["endpoint"],
        azure_deployment=azure_config["deployment_name"],
        api_version=azure_config["api_version"],
        temperature=0,
    )

    # Lấy danh sách tài liệu từ VectorDB
    docs = vectorstore.get(where={"is_summary": True})
    document_set = set()

    for doc in docs["metadatas"]:
        document_set.add(doc["source"])
   
    document_list_str = "\n".join(document_set)

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt.partial(documents=document_list_str))
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain)
    return rag_chain

def summarize_document(file_path: str, file_name: str) -> str:
    # Load tài liệu từ file
    documents = load_document(file_path)
    
    # Tạo chain tóm tắt
    llm = AzureChatOpenAI(
        azure_ad_token=azure_config["api_key"],
        azure_endpoint=azure_config["endpoint"],
        azure_deployment=azure_config["deployment_name"],
        api_version=azure_config["api_version"],
        temperature=0,
    )
    summarize_chain = load_summarize_chain(llm, chain_type="stuff", prompt=PromptTemplate(template=summary_prompt, input_variables=["text"]))
    # Tóm tắt tài liệu
    summary = file_name + " " + summarize_chain.run(documents)
    return summary