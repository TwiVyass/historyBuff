import os
import sys
from flask import Flask, render_template, request, session
import pymongo
import certifi
from openai import OpenAI
from dotenv import load_dotenv
import json

# --- Load Environment Variables ---
load_dotenv()

# --- Initialize Flask App ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# --- Initialize OpenAI Client ---
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    print("FATAL ERROR: The OPENAI_API_KEY environment variable is missing.")
    sys.exit(1)
client = OpenAI(api_key=API_KEY)

# --- Configuration ---
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-3.5-turbo"
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DB_NAME = "fashion_muse_db"
MONGO_COLLECTION_NAME = "garments"
INDEX_NAME = "vector_index"

# --- Helper Functions ---

def get_mongo_collection():
    """Establishes a connection to MongoDB and returns the collection object."""
    ca = certifi.where()
    mongo_client = pymongo.MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=ca)
    db = mongo_client[MONGO_DB_NAME]
    return db[MONGO_COLLECTION_NAME]

def get_embedding_from_text(text_query: str) -> list | None:
    """Gets a vector embedding for a given text query using OpenAI."""
    try:
        response = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text_query
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting OpenAI embedding: {e}")
        return None

def vector_search(collection, query_vector: list, num_results: int = 12) -> list:
    """Performs a vector search on the MongoDB collection."""
    pipeline = [
        {
            "$vectorSearch": {
                "index": INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 150,
                "limit": num_results,
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "artistDisplayName": 1,
                "primaryImage": 1,
                "objectURL": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(collection.aggregate(pipeline))

# --- Chatbot Response Generator ---

def generate_chatbot_response(query: str, search_results: list, chat_history: list) -> dict:
    context_string = ""
    if search_results:
        context_string = "\nFor additional context, I found these relevant items in my collection:\n"
        for item in search_results:
            context_string += f"- A piece titled '{item.get('title', 'N/A')}' by {item.get('artistDisplayName', 'an unknown artist')}.\n"

    system_prompt = """
You are HauteBot, a world-class expert on historical fashion. Your personality is engaging, insightful, and highly conversational.

--- YOUR CORE INSTRUCTION ---
You will be given a user's query and sometimes a "CONTEXT" block with specific examples. Treat this context as your own private research notes. Use the details from this context to make your points more vivid and specific.

**Your single most important rule is to ALWAYS respond with a valid JSON object.** This is not optional.

--- HANDLING IMPOSSIBLE REQUESTS ---
If the user asks for something you cannot provide (like images, videos, or real-time web data), you must:
1. Acknowledge the limitation in a friendly way as your first point.
2. Fulfill the rest of their request to the best of your ability using text.
3. Do not mention the term 'Your collection'. The user does NOT have a collection.
This limitation MUST be part of the JSON response.

--- RESPONSE FORMAT & STYLE RULES ---
- You MUST respond with a valid JSON object with two keys: "title" and "points".
- Speak directly and conversationally.
- Elaborate on each point in the "points" array. Explain the "why" behind the fashion.
- NEVER mention the existence of your context, collection, or that you performed a search. Present all information as your own inherent expertise.
"""

    # Rebuild history to be API-compliant
    api_history = []
    for message in chat_history:
        if message['role'] == 'assistant':
            string_content = f"Title: {message['content'].get('title', '')}\n"
            for point in message['content'].get('points', []):
                string_content += f"- {point}\n"
            api_history.append({'role': 'assistant', 'content': string_content})
        else:
            api_history.append(message)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(api_history)
    messages.append({"role": "user", "content": query + context_string})

    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )
        json_string = response.choices[0].message.content.strip()
        try:
            parsed_response = json.loads(json_string)
            return parsed_response
        except json.JSONDecodeError:
            print(f"--- WARNING: AI did not return valid JSON. ---\n{json_string}")
            return {"title": "Response", "points": [json_string]}
    except Exception as e:
        print(f"Error generating OpenAI chatbot response: {e}")
        return {"title": "Error", "points": ["I'm sorry, I had trouble thinking of a response."]}

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        session.pop('chat_history', None)

    if request.method == 'POST':
        if 'chat_history' not in session:
            session['chat_history'] = []

        query_text = request.form.get('query')
        if query_text:
            print(f"\n--- NEW MESSAGE ---")
            print(f"Received query: '{query_text}'")

            collection = get_mongo_collection()
            query_vector = get_embedding_from_text(query_text)

            results = []
            if query_vector:
                results = vector_search(collection, query_vector, num_results=3)

            assistant_response = generate_chatbot_response(query_text, results, session['chat_history'])

            session['chat_history'].append({'role': 'user', 'content': query_text})
            session['chat_history'].append({'role': 'assistant', 'content': assistant_response})
            session.modified = True

        chat_history = session.get('chat_history', [])
        return render_template('index.html', chat_history=chat_history)

    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
