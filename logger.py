import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import config

os.makedirs(config.LOGS_FOLDER, exist_ok=True)

log_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

system_logger = logging.getLogger('printshop')
system_logger.setLevel(logging.INFO)

log_file = os.path.join(config.LOGS_FOLDER, 'printshop.log')
file_handler = RotatingFileHandler(
    log_file, maxBytes=5*1024*1024, backupCount=30, encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
system_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
system_logger.addHandler(console_handler)


def log_order(action, order_number, details=None):
    msg = f"ORDER [{action}] {order_number}"
    if details:
        msg += f" | {details}"
    system_logger.info(msg)


def log_error(source, message):
    system_logger.error(f"[{source}] {message}")


def log_login(username, success=True):
    status = "SUCCESS" if success else "FAILED"
    system_logger.info(f"LOGIN [{status}] {username}")


def log_print(order_number, worker_name, result):
    system_logger.info(f"PRINT [{order_number}] by {worker_name}: {result}")
