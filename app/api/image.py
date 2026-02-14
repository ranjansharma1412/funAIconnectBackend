
from flask import Blueprint, request, jsonify, current_app, send_file
from app.services.image_generator import ImageGenerator
import os
import uuid
import base64
from io import BytesIO

bp = Blueprint('image', __name__)

@bp.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        # Optional parameters
        num_inference_steps = data.get('num_inference_steps', 4)
        guidance_scale = data.get('guidance_scale', 0.0)

        # Get singleton instance
        generator = ImageGenerator()
        image = generator.generate_image(
            prompt, 
            num_inference_steps=num_inference_steps, 
            guidance_scale=guidance_scale
        )

        # Save image securely
        filename = f"{uuid.uuid4()}.png"
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        
        # Ensure directory exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        filepath = os.path.join(upload_folder, filename)
        image.save(filepath)

        # Convert to base64 for immediate display if requested, or return URL
        # Here we return the URL and base64 for convenience
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # Construct static URL
        image_url = f"/static/uploads/{filename}"

        return jsonify({
            'message': 'Image generated successfully',
            'image_url': image_url,
            'base64': img_str
        }), 200

    except Exception as e:
        print(f"Error generating image: {e}")
        return jsonify({'error': str(e)}), 500
