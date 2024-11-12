import os
import os.path
import logging
import logging.handlers

# Directory name for saving log files
LOG_FOLDER = 'logs'

# Log file name
LOG_NAME = 'scraper.log'

# Full path to the log file
LOG_PATH = os.path.join(LOG_FOLDER, LOG_NAME)

# Maximum log file size
LOG_SIZE = 2 * 1024 * 1024

# Log files count for cyclic rotation
LOG_BACKUPS = 2

# Setting up configuration for logging
def setup_logging():
    logFormatter = logging.Formatter(
        fmt='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    if not os.path.exists(LOG_FOLDER):
        try:
            os.mkdir(LOG_FOLDER)
        except OSError:
            logging.warning("Can't create log folder.")

    if os.path.exists(LOG_FOLDER):
        fileHandler = logging.handlers.RotatingFileHandler(
            LOG_PATH, mode='a', encoding='utf-8', maxBytes=LOG_SIZE,
            backupCount=LOG_BACKUPS)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
