import os
import sys
from flask import Flask, render_template, request
import pymongo
import certifi
from openai import OpenAI
from flask import Flask, render_template, request, session
from dotenv import load_dotenv # <-- IMPORT THIS

# --- Load Environment Variables ---
load_dotenv() # <-- ADD THIS LINE AT THE TOP

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


def generate_chatbot_response(query: str, search_results: list) -> str:
    """Generates a natural language response using an OpenAI chat model."""
    if not search_results:
        return "I couldn't find any items in my historical collection that matched your description. Could you try being more specific or using different keywords?"

    context_string = ""
    for i, item in enumerate(search_results[:4]):
        context_string += f"Item {i + 1}: A piece titled '{item.get('title', 'N/A')}' by {item.get('artistDisplayName', 'an unknown artist')}.\n"

    system_prompt = """You are FashionMuse, a helpful and knowledgeable AI design assistant specializing in historical fashion.
    You will be given a user's request and some search results from a historical collection.
    Your task is to generate a friendly, insightful, and conversational response based on this information.
    Briefly describe the general style you see in the results and mention one or two specific examples from the context to inspire the user.
    Keep the response to 2-3 sentences."""

    user_prompt = f"""
    User's request: "{query}"

    Relevant items from my collection:
    --- CONTEXT ---
    {context_string}
    --- END CONTEXT ---
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating OpenAI chatbot response: {e}")
        return "I'm sorry, I had a little trouble thinking of a response. Please try your search again."


# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    chatbot_text = None

    if request.method == 'POST':
        query_text = request.form.get('query')
        if query_text:
            print(f"\n--- NEW SEARCH ---")
            print(f"Received query: '{query_text}'")

            collection = get_mongo_collection()
            query_vector = get_embedding_from_text(query_text)

            if query_vector:
                results = vector_search(collection, query_vector)
                chatbot_text = generate_chatbot_response(query_text, results)
            else:
                results = []
                chatbot_text = "I'm sorry, I had trouble understanding that query. Could you rephrase it?"

    return render_template('index.html', chatbot_text=chatbot_text, results=results)


# --- Main Entry Point ---
if __name__ == '__main__':
    app.run(debug=True, port=8080)