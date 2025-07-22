# utils/logger.py
import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

class EmojiLogger:
    """
    Hybrid logging system that outputs to both terminal and file
    using the existing emoji+timestamp style from the scheduler.
    """
    
    def __init__(self, name: str = "telegram_bot", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup both file and console handlers"""
        
        # File handler - daily rotating logs
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{self.name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter - simple format that preserves emoji style
        formatter = logging.Formatter('%(asctime)s - %(message)s', 
                                    datefmt='%Y-%m-%d %H:%M:%S')
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def story(self, message: str):
        """
        Log story-like narrative events that appear in both console and file.
        Use for meaningful user-facing events that tell the story.
        """
        self.logger.info(message)
    
    def info(self, message: str):
        """Log info message with emoji style"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message with emoji style"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message with emoji style"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message (file only)"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Log critical error message"""
        self.logger.critical(message)

# Global logger instance
logger = EmojiLogger()

def get_logger(name: Optional[str] = None) -> EmojiLogger:
    """Get logger instance"""
    if name:
        return EmojiLogger(name)
    return logger 