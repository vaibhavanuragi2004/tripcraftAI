# ✈️🤖 TripCraftAI

**TripCraftAI** is an intelligent travel itinerary generation and management application.  
It leverages the power of Large Language Models (LLMs) to create **personalized, culturally-aware, and optimized travel plans** for tourists in India. Beyond planning, it serves as a **travel companion** — with live tracking, weather alerts, budget insight, and contextual AI help.

![App Screenshot](https://i.imgur.com/G5iE1jN.png)

---

## ✨ Features

- 🤖 **AI-Powered Itinerary Generation**: Creates detailed, day-by-day itineraries based on user inputs like destination, duration, budget, and interests using **Llama 3.1** via LangChain.
- 🗂️ **Itinerary Management**: View, manage, and track all your travel plans in one place.
- 📈 **Live Progress Tracking**: Mark checkpoints as complete and visualize your trip’s progress in real-time.
- 💬 **Context-Aware Chatbot**: Your own travel assistant that understands your trip and provides helpful advice.
- 📄 **PDF Downloads**: Generate a beautifully formatted PDF version of any itinerary.
- 💡 **Smart Recommendations**: Suggests new destinations using a content-based recommendation engine trained on past trip data.
- 🌦️ **Weather Integration**: Real-time weather alerts using OpenWeatherMap for trip safety and planning.
- 💸 **Budget Optimization**: Automatically allocates your budget for accommodation, food, activities, and transport.
- 🚂 **Railway Code Finder**: Uses an LLM to fetch Indian Railway station codes for any city (e.g., *Varanasi* → *BSB*).

---
#PPT-LINK
https://drive.google.com/drive/folders/1bGAr_SKIhsM6PsVk2qbbqm31QZaLh4z0

## 📄 Project Slides (PPT)

[🔗 Download TripCraftAI Project Slides (PPT)](media/submission20251 (1).pptx)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask (Python) |
| **Database** | PostgreSQL (Production), SQLite (Dev) |
| **AI / LLMs** | LangChain + Groq (Llama 3.1) |
| **Machine Learning** | Pandas, Scikit-learn (TF-IDF, Cosine Similarity) |
| **Frontend** | HTML, CSS, Bootstrap, React, JavaScript, Jinja2 |
| **PDF Export** | FPDF2 |
| **Weather API** | OpenWeatherMap |
| **Train Codes** | Custom LLM-based Query Engine |

---

## 📌 How to Run Locally

```bash
git clone https://github.com/yourusername/tripcraftai.git
cd tripcraftai
pip install -r dependenciess.txt

# Set your environment variables in a .env file
# Example:
# POSTGRES_USER=youruser
# POSTGRES_PASSWORD=yourpassword

python main.py
