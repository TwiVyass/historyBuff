# HauteBot 🧵✨

**HauteBot is your AI-powered fashion historian and creative design muse.**

Built to inspire and educate, HauteBot is an intelligent assistant that allows users to explore fashion through the ages—one conversation at a time. Whether you're curious about 1920s flapper trends or want to visualize avant-garde concepts, HauteBot bridges the gap between history and creativity with the power of AI.

Think of it as your digital fashion mentor—one that talks, remembers, and illustrates.

**Try it out: https://historybuff.onrender.com/**

---

## ✨ Features

- **Conversational Fashion Expert:** Ask about styles from specific eras, trends, or movements. HauteBot understands context and gives rich, historically-grounded answers.
- **AI-Powered Visual Creator:** Want to see "a futuristic sari" or "Gothic revival meets punk"? Just ask—HauteBot can generate stunning visuals powered by DALL·E 3.
- **Smart Fashion Retrieval (RAG):** HauteBot searches a curated dataset of garments from The Met using real-time vector similarity search to give accurate examples.
- **Interactive Chat History:** Easily revisit your past queries and generated images in a clean, scrollable modal—perfect for inspiration tracking.
- **Readable & Structured Output:** Responses are parsed and presented in a visually clean layout with bullet points and section headers for easy reading.

---

## System Architecture

HauteBot uses a multi-agent architecture to intelligently route user inputs, whether they’re asking for information or an image.

1. **Central Router:** Interprets the user’s intent and forwards the query.
2. **Historian Agent:**
   - Embeds queries using OpenAI's embedding model
   - Retrieves garment matches using MongoDB Atlas Vector Search.
   - Generates a response using OpenAI’s GPT model.

---

## Tech Stack

### Core & Backend
- Python + Flask
- Gunicorn (production server)

### AI & ML
- OpenAI gpt-3.5-turbo model
- OpenAI text-embedding-3-small model

### Database
- MongoDB Atlas (with Vector Search)

### Frontend
- HTML + Jinja2
- CSS3
- Vanilla JavaScript

### Deployment
- Render (cloud platform)
- Git + GitLab (version control)

---

## Running Locally

To run this project on your local machine:

### 1. Prerequisites
- Python 3.11+
- Git
- MongoDB Atlas account
- OpenAI API key
- Google Cloud project with Vertex AI enabled

### 2. Clone the Repository
```bash
git clone https://github.com/TwiVyass/historyBuff
cd historyBuff
