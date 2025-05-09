from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

# Cấu hình logger cho ứng dụng
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.INFO)

# Sử dụng TimedRotatingFileHandler cho ứng dụng
app_handler = TimedRotatingFileHandler(
    "logs/app.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
app_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
app_handler.setFormatter(app_formatter)
app_handler.suffix = "%Y-%m-%d"  # Định dạng tên file log theo ngày
app_logger.addHandler(app_handler)

# Cấu hình logger cho cơ sở dữ liệu
db_logger = logging.getLogger("db_logger")
db_logger.setLevel(logging.INFO)

# Sử dụng TimedRotatingFileHandler cho cơ sở dữ liệu
db_handler = TimedRotatingFileHandler(
    "logs/db.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
db_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
db_handler.setFormatter(db_formatter)
db_handler.suffix = "%Y-%m-%d"  # Định dạng tên file log theo ngày
db_logger.addHandler(db_handler)