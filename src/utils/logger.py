import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("./log_file3.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger()

log_level = os.getenv("LOG_LEVEL", "INFO")
logger.setLevel(log_level.upper())  # overrides the above level setting
