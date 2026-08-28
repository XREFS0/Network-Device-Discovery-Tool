import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.core.config import Config
from app.database.connection import initialize_database
from app.ui.main_window import MainWindow

def setup_logging() -> None:
    """Set up application-wide file and console logging."""
    Config.ensure_dirs()
    
    # Create a formatting style without emojis
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Root Logger Setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Minimize verbose output from third-party libraries (e.g., Scapy)
    logging.getLogger("scapy").setLevel(logging.WARNING)

def main() -> None:
    # 1. Initialize logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application starting...")

    # 2. Initialize database
    try:
        initialize_database()
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)

    # 3. Initialize Qt Application
    app = QApplication(sys.argv)
    
    # Apply modern native style
    app.setStyle("Fusion")
    
    # Custom color palette for a professional look (slate gray / clean dark/light UI support)
    # The default Fusion theme looks great and highly native. We'll use the default styling
    # to maintain the standard desktop-native utility feeling.
    
    # 4. Show main window
    window = MainWindow()
    window.show()
    
    logger.info("Main UI window loaded. Entering Qt main loop.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
