# Sử dụng image Python
FROM python:3.9-slim

# Cài đặt các thư viện yêu cầu
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

# Sao chép mã nguồn ứng dụng vào container
COPY . /app/

# Mở port 8000
EXPOSE 8000

# Chạy ứng dụng với Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
