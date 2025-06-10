import os
import sys
from flask import Flask, render_template, request
import pymongo
import certifi
from openai import OpenAI
from flask import Flask, render_template, request, session
from dotenv import load_dotenv # <-- IMPORT THIS
import json

# --- Load Environment Variables ---
load_dotenv()


# --- Initialize Flask App ---
app = Flask(__name__)
# NEW: Load the secret key from the environment
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')


# --- Initialize OpenAI Client ---
# NEW: Load the API key from the environment
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    print("FATAL ERROR: The OPENAI_API_KEY environment variable is missing.")
    sys.exit(1)
client = OpenAI(api_key=API_KEY)


# --- Configuration ---
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-3.5-turbo"
# NEW: Load the MongoDB connection string from the environment
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DB_NAME = "fashion_muse_db"
MONGO_COLLECTION_NAME = "garments"
INDEX_NAME = "vector_index"

# ... the rest of your app.py file stays exactly the same ...

# --- Initialize OpenAI Client ---
# We will pass the key directly into the code as you requested.
# WARNING: This is not secure for public code (like on GitHub), but it's fine for running on your own machine.

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


# In app.py, REPLACE the old generate_chatbot_response function with this new one:

# In app.py, replace the entire function with this one.

def generate_chatbot_response(query: str, search_results: list, chat_history: list) -> dict:
    context_string = ""
    if search_results:
        context_string = "\nFor additional context, I found these relevant items in my collection:\n"
        for item in search_results:
            context_string += f"- A piece titled '{item.get('title', 'N/A')}' by {item.get('artistDisplayName', 'an unknown artist')}.\n"

        # In generate_chatbot_response function in app.py

            # In app.py, inside the generate_chatbot_response function:
            # REPLACE the old system_prompt with this one.

        # In app.py, inside the generate_chatbot_response function:
        # REPLACE the old system_prompt with this one.

    system_prompt = """You are FashionMuse, a world-class expert on historical fashion. Your personality is engaging, insightful, and highly conversational.

    --- YOUR CORE INSTRUCTION ---
    You will be given a user's query and sometimes a "CONTEXT" block with specific examples. Treat this context as your own private research notes. Use the details from this context to make your points more vivid and specific.

    **Your single most important rule is to ALWAYS respond with a valid JSON object.** This is not optional.

    --- HANDLING IMPOSSIBLE REQUESTS ---
    If the user asks for something you cannot provide (like images, videos, or real-time web data), you must:
    1. Acknowledge the limitation in a friendly way as your first point.
    2. Fulfill the rest of their request to the best of your ability using text.
    This limitation MUST be part of the JSON response.

    --- RESPONSE FORMAT & STYLE RULES ---
    - You MUST respond with a valid JSON object with two keys: "title" and "points".
    - Speak directly and conversationally.
    - Elaborate on each point in the "points" array. Explain the "why" behind the fashion.
    - NEVER mention the existence of your context, collection, or that you performed a search. Present all information as your own inherent expertise.

    Example of handling an impossible request:
    {
      "title": "The Evolution of Feathered Hats",
      "points": [
        "While I can't show you images directly in this chat, I can certainly walk you through the fascinating history of feathered hats!",
        "The tradition goes way back. In ancient civilizations like the Aztecs, feathers were powerful symbols of status and connection to the divine, not just simple decoration.",
        "During the Renaissance in Europe, they became a sign of extravagance. Nobility used exotic plumes from ostriches and peacocks to showcase immense wealth and sophistication.",
        "By the Victorian era, they were a staple of women's fashion, though it led to a controversial period where entire birds were sometimes used, sparking early conservation movements.",
        "Today, designers on the runway use them as works of art, reinterpreting these historical styles in bold, avant-garde ways."
      ]
    }
    --- END RULES ---
    """
    # --- THIS IS THE FIX ---
    # We rebuild the history to be API-compliant, converting the assistant's
    # dictionary responses back into simple strings for context.
    api_history = []
    for message in chat_history:
        if message['role'] == 'assistant':
            # Convert the structured dictionary content back into a simple string.
            string_content = f"Title: {message['content'].get('title', '')}\n"
            for point in message['content'].get('points', []):
                string_content += f"- {point}\n"
            api_history.append({'role': 'assistant', 'content': string_content})
        else:
            # User messages are already strings, so they are fine.
            api_history.append(message)
    # --- END FIX ---


    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(api_history) # Use the new, clean history
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


# Now, REPLACE the old index route with this new one:

@app.route('/', methods=['GET', 'POST'])
def index():
    # On the first visit to the page, clear any old chat history.
    if request.method == 'GET':
        session.pop('chat_history', None)

    # This is our main logic block for when the user sends a message.
    if request.method == 'POST':
        # 1. Initialize chat history in the session if it doesn't exist.
        if 'chat_history' not in session:
            session['chat_history'] = []

        query_text = request.form.get('query')
        if query_text:
            print(f"\n--- NEW MESSAGE ---")
            print(f"Received query: '{query_text}'")

            collection = get_mongo_collection()
            query_vector = get_embedding_from_text(query_text)

            # 2. Vector search still runs to find relevant items for context.
            results = []
            if query_vector:
                results = vector_search(collection, query_vector, num_results=3)  # Fewer results needed

            # 3. Generate a response using the NEW function that includes chat history.
            # We pass the user's query, the search results, AND the history from the session.
            assistant_response = generate_chatbot_response(query_text, results, session['chat_history'])

            # 4. Update the session history with the new exchange.
            session['chat_history'].append({'role': 'user', 'content': query_text})
            session['chat_history'].append({'role': 'assistant', 'content': assistant_response})
            session.modified = True  # Tell Flask the session has changed

    # 5. Pass the entire chat history to the template.
    chat_history = session.get('chat_history', [])
    return render_template('index.html', chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True, port=8080)