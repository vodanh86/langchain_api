import re

# Biểu thức chính quy để phát hiện email
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
account_patterns = []
file_path = "regular.txt"
with open(file_path, "r") as file:
    for line in file:
        line = line.strip()
        if line:  # Bỏ qua dòng trống
            account_patterns.append(line)

# Biểu thức chính quy để phát hiện số tài khoản ngân hàng (10-16 chữ số)
account_number_pattern = r"\b\d{10,16}\b"

def detect_sensitive_info(text):
    # Phát hiện email
    email = re.search(email_pattern, text)
    if email:
        return True
    
    for pattern in account_patterns:
        if re.search(pattern, text):
            return True  # Nếu tìm thấy bất kỳ pattern nào khớp, trả về True
    
    return False