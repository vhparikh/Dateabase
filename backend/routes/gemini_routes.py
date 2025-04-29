from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai

# Configure Gemini API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

gemini_bp = Blueprint('gemini_bp', __name__)

@gemini_bp.route('/api/check-inappropriate', methods=['POST'])
def check_inappropriate():
    # Get the text content from the request
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'is_inappropriate': False, 'error': 'No text provided'}), 400
    
    try:
        # Check if Gemini API is configured
        if not GEMINI_API_KEY:
            return jsonify({'is_inappropriate': False, 'error': 'Gemini API not configured'}), 500
        
        # Use Gemini to check for inappropriate content
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        prompt = f"Determine whether the following text is inappropriate based on general social norms, ethics, legal standards, or safety concerns. Respond only with \"true\" or \"false\".\n\nText: \"{text}\""
        
        result = model.generate_content(prompt)
        output = result.text.strip().lower()
        
        # Log the result for debugging
        print(f"Gemini check result for text: '{text[:30]}...' => {output}")
        
        # Return the result
        return jsonify({'is_inappropriate': output == 'true'})
    
    except Exception as e:
        print(f"Error checking inappropriate content: {str(e)}")
        # Fallback: if error, assume not inappropriate
        return jsonify({'is_inappropriate': False, 'error': str(e)}), 500