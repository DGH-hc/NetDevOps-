import logging
import os

# Logs directory
LOG_DIR = "/app/logs"   # <-- recommended path
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Logger config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # optional (logs to console)
    ]
)

logger = logging.getLogger("netdevops")
