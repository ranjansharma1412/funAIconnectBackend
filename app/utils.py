import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
import io

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
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_webp(file_storage):
    """
    Converts uploaded image to WebP format if it is a PNG or JPEG.
    Returns a BytesIO object with the WebP image, or the original file_storage if conversion isn't applicable.
    """
    if not file_storage or not getattr(file_storage, 'filename', None):
        return file_storage

    filename = file_storage.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
        return file_storage
        
    try:
        # Load the image using Pillow and the Werkzeug FileStorage stream
        image = Image.open(file_storage)
        
        # Ensure image is in a format compatible with WebP (WebP supports RGB and RGBA)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')
            
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='WEBP', quality=80)
        img_byte_arr.seek(0)
        
        # Emulate filename for downstream validation routines
        new_filename = filename.rsplit('.', 1)[0] + '.webp'
        img_byte_arr.name = new_filename
        
        return img_byte_arr
    except Exception as e:
        print(f"Error converting to WebP: {e}")
        file_storage.seek(0)
        return file_storage

def save_image(file_storage):
    if not file_storage or file_storage.filename == '':
        return None
        
    try:
        processed_file = convert_to_webp(file_storage)
        
        # Determine the filename to check against allowed expressions
        check_name = getattr(processed_file, 'filename', getattr(processed_file, 'name', file_storage.filename))
        
        if allowed_file(check_name):
            # Pass format='webp' to Cloudinary if we dynamically created the buffer
            upload_kwargs = {'resource_type': 'auto'}
            if hasattr(processed_file, 'name') and processed_file.name.endswith('.webp'):
                upload_kwargs['format'] = 'webp'
                
            upload_result = cloudinary.uploader.upload(processed_file, **upload_kwargs)
            return upload_result.get('secure_url')
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None
    
    return None
