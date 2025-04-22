# Sử dụng image Python
FROM python:3.9-slim

# Cài đặt các thư viện yêu cầu
COPY requirements.txt /app/
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install -r requirements.txt

# Sao chép mã nguồn ứng dụng vào container
COPY . /app/

# Mở port 8000
EXPOSE 8000

# Chạy ứng dụng với Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
