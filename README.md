# Querio — AI-Powered Data Analyst

Querio lets you ask questions about your CSV data in plain English. 
It writes Python/pandas code, executes it safely, and returns the answer — 
including charts and AI-generated insights.

## Features
- Natural language to pandas code generation (Groq LLM)
- Safe code execution sandbox
- Auto-generated EDA charts (bar, histogram, scatter, pie, box)
- AI-written storytelling insights for each chart
- Dynamic example questions based on uploaded dataset
- Clean, responsive Streamlit UI

## Tech Stack
- Python
- Streamlit (UI)
- Groq API (LLM)
- LangChain (PythonREPLTool)
- Pandas
- Plotly (charts)

## Setup

1. Clone the repo
   git clone https://github.com/your-username/querio.git
   cd querio

2. Create a virtual environment
   python -m venv venv
   source venv/bin/activate   (Mac/Linux)
   venv\Scripts\activate      (Windows)

3. Install dependencies
   pip install -r requirements.txt

4. Add your API key
   Copy .env.example to .env and add your Groq API key

5. Run the app
   streamlit run app.py --server.port 8080

## Screenshots

### Home
![Home](screenshots/home.png)

### Text Answer
![Text Answer](screenshots/text-answer.png)

### Chart with AI Insight
![Chart Insight](screenshots/chart-insight.png)
## Safety
AI-generated code runs through a safety filter (safety.py) that blocks 
dangerous operations like file system access, imports of os/sys/subprocess, etc.
