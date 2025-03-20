from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import logging
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs

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
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize the Generative AI model: {str(e)}")

# File to store chat history
CHAT_HISTORY_FILE = "data.json"

# Function to load chat history from the JSON file
def load_chat_history():
    try:
        if not os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, "w") as file:
                json.dump([], file)  # Create an empty list if the file doesn't exist
            return []
        
        with open(CHAT_HISTORY_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading chat history: {str(e)}")
        return []

# Function to save chat history to the JSON file
def save_chat_history(chat_history):
    try:
        with open(CHAT_HISTORY_FILE, "w") as file:
            json.dump(chat_history, file, indent=4)
        logging.info("Chat history saved to data.json")
    except Exception as e:
        logging.error(f"Error saving chat history: {str(e)}")

# Function to generate a response using the AI model
def generate_response(user_message):
    try:
        combined_message = f"User: {user_message}\n{BOT_NAME}:"
        result = model.generate_content([combined_message])
        
        if hasattr(result, "text"):
            return result.text.strip()
        else:
            return "No response from the model."
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Home route (For Testing)
@app.route("/", methods=['GET'])
def home():
    return render_template('index.html')

# Chatbot route (Handles user messages)
@app.route('/chat', methods=['POST'])
def chat():
    try: 
        data = request.get_json()
        logging.debug(f"Received data: {data}")

        # Ensure message is provided
        user_message = data.get('message')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Generate bot response
        bot_response = generate_response(user_message)
        logging.debug(f"Generated bot response: {bot_response}")

        # Load existing chat history
        chat_history = load_chat_history()
        logging.debug(f"Loaded chat history: {chat_history}")

        # Add new chat entry
        chat_history.append({
            "user_input": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Save updated chat history
        save_chat_history(chat_history)

        return jsonify({'response': bot_response}), 200

    except Exception as e:
        logging.error(f"Error in /chat route: {str(e)}")
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Route to fetch chat history
@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    try:
        chat_history = load_chat_history()
        return jsonify({'chat_history': chat_history}), 200
    except Exception as e:
        logging.error(f"Error in /chat/history route: {str(e)}")
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Route to serve the chatbot interface
@app.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


'''
##Old app.py code
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import sqlite3
import logging
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs

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
try:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize the Generative AI model: {str(e)}")

# Connect to SQLite database and create table if it doesn't exist
def initialize_db():
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")

# Function to insert chat data into the database
def save_chat_to_db(user_input, bot_response):
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        logging.debug(f"Attempting to save: User Input: {user_input}, Bot Response: {bot_response}")
        cursor.execute('''
            INSERT INTO chat_history (user_input, bot_response)
            VALUES (?, ?)
        ''', (user_input, bot_response))
        conn.commit()
        conn.close()
        logging.info(f"Stored in database - User Input: {user_input}, Bot Response: {bot_response}")
    except Exception as e:
        logging.error(f"Error saving to database: {str(e)}")

# Function to fetch chat history from the database
def fetch_chat_history():
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM chat_history ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Error fetching chat history: {str(e)}")
        return []

# Function to generate a response using the AI model
def generate_response(user_message):
    try:
        combined_message = f"User: {user_message}\n{BOT_NAME}:"
        result = model.generate_content([combined_message])
        
        if hasattr(result, "text"):
            return result.text.strip()
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

        # Save chat data to the database
        save_chat_to_db(user_message, bot_response)

        return jsonify({'response': bot_response}), 200

    except Exception as e:
        logging.error(f"Error in /chat route: {str(e)}")
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Route to fetch chat history
@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    try:
        rows = fetch_chat_history()

        # Format the data for JSON response
        chat_history = []
        for row in rows:
            chat_history.append({
                'id': row[0],
                'user_input': row[1],
                'bot_response': row[2],
                'timestamp': row[3]
            })

        return jsonify({'chat_history': chat_history}), 200
    except Exception as e:
        logging.error(f"Error in /chat/history route: {str(e)}")
        return jsonify({'error': f"Internal Server Error: {str(e)}"}), 500

# Initialize the database when the app starts
initialize_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)##
'''