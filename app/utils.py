import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

import cloudinary
import cloudinary.uploader

# Configure Cloudinary
cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_API_SECRET'),
  secure = True
)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file_storage):
    if not file_storage or file_storage.filename == '':
        return None
    
    if allowed_file(file_storage.filename):
        try:
            upload_result = cloudinary.uploader.upload(file_storage)
            return upload_result.get('secure_url')
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            return None
    
    return None
