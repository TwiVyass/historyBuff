import sys
from openai import OpenAI
import pymongo
import certifi

# --- Configuration (Copy from your app.py) ---

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# PASTE YOUR SAME OPENAI API KEY HERE
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# Good, secure code
import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("FATAL ERROR: OPENAI_API_KEY not found in .env file.")
else:
    client = OpenAI(api_key=API_KEY)
    # ... rest of your script's logic goes here

# --- Main Script ---

def migrate_database():
    """
    Connects to MongoDB, fetches all documents, and updates them with new
    embeddings from OpenAI.
    """
    print("--- Starting Database Migration ---")

    # 1. Connect to services
    try:
        if not API_KEY or API_KEY == "PASTE_YOUR_KEY_HERE":
            print("FATAL ERROR: The OpenAI API key is missing.")
            sys.exit(1)

        print("Connecting to OpenAI...")
        openai_client = OpenAI(api_key=API_KEY)

        print("Connecting to MongoDB...")
        ca = certifi.where()
        mongo_client = pymongo.MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=ca)
        db = mongo_client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        print("Connections successful.")
    except Exception as e:
        print(f"Error connecting to services: {e}")
        sys.exit(1)

    # 2. Fetch all documents from the collection
    try:
        documents = list(collection.find({}))
        total_docs = len(documents)
        if total_docs == 0:
            print("No documents found in the collection. Nothing to do.")
            sys.exit(0)
        print(f"Found {total_docs} documents to process.")
    except Exception as e:
        print(f"Error fetching documents: {e}")
        sys.exit(1)

    # 3. Iterate, re-embed, and update each document
    for i, doc in enumerate(documents):
        doc_id = doc["_id"]
        text_to_embed = doc.get("title", "") # We'll use the title for the embedding

        if not text_to_embed:
            print(f"[{i+1}/{total_docs}] Skipping document {doc_id} (no title).")
            continue

        print(f"[{i+1}/{total_docs}] Processing document: {text_to_embed[:50]}...")

        try:
            # Get the new embedding from OpenAI
            response = openai_client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text_to_embed
            )
            new_embedding = response.data[0].embedding

            # Update the document in MongoDB with the new embedding
            collection.update_one(
                {"_id": doc_id},
                {"$set": {"embedding": new_embedding}}
            )
        except Exception as e:
            print(f"!!----> FAILED to update document {doc_id}. Error: {e}")
            print("!!----> Please check the error and try again.")
            # For a serious project, you might log this error and continue. For now, we stop.
            sys.exit(1)

    print("\n--- Migration Complete! ---")
    print("All documents have been updated with new 1536-dimension embeddings.")
    print("Now, please update your MongoDB Atlas search index.")

if __name__ == '__main__':
    migrate_database()