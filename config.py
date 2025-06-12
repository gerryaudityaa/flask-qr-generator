import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images', 'uploads')
    QR_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'qr_codes')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    
    @property
    def now(self):
        from datetime import datetime
        return datetime.now()