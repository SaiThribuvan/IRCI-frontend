from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load API key securely
api_key = os.getenv("GOOGLE_GENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set the GOOGLE_GENAI_API_KEY environment variable.")

genai.configure(api_key=api_key)

BOT_NAME = "AI_BOT"

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Initialize the Generative AI model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Initial conversation context (can be modified)
initial_context = ""

def generate_response(user_message):
    try:
        combined_message = f"{initial_context}\nUser: {user_message}\n{BOT_NAME}:" if initial_context else f"User: {user_message}\n{BOT_NAME}:"
        
        result = model.generate_content([combined_message])
        
        if hasattr(result, "text"):
            return result.text.strip()  # Correct extraction of response
        else:
            return "No response from the model."
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Home route (For Testing)
@app.route("/", methods=['GET'])
def home():
    return jsonify({"message": "Flask chatbot is running!"}), 200

# Chatbot route (Handles user messages)
@app.route('/chat', methods=['POST'])
def chat():
    try: 
        data = request.get_json()

        # Ensure message is provided
        user_message = data.get('message')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Generate bot response
        bot_response = generate_response(user_message)
        return jsonify({'response': bot_response}), 200

    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Allows external access if needed
