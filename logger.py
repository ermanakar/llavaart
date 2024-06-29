import logging

def configure_logging(log_level=logging.INFO):
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

def get_logger(name):
    return logging.getLogger(name)
