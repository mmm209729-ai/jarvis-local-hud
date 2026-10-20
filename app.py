import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import requests
from icalendar import Calendar
import google.generativeai as genai

app = Flask(__name__)

# Prende le variabili dagli Environment di sistema (o dal file .env)
ICAL_URL = os.environ.get("GOOGLE_ICAL_URL_2", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/calendar")
def get_calendar():
    if not ICAL_URL:
        return jsonify([{"date": "Configura", "summary": "GOOGLE_ICAL_URL_2 non impostato."}])
    try:
        response = requests.get(ICAL_URL)
        if response.status_code != 200:
            return jsonify([{"date": "Errore", "summary": "Impossibile scaricare iCal"}])
        
        cal = Calendar.from_ical(response.content)
        events = []
        for component in cal.walk('vevent'):
            summary = component.get('summary')
            dtstart = component.get('dtstart')
            if dtstart and summary:
                dt = dtstart.dt
                events.append((dt, str(summary)))
                
        events.sort(key=lambda x: x[0] if isinstance(x[0], datetime) else datetime.min)
        
        result = []
        count = 0
        for dt, summary in events:
            if count >= 6:
                break
            date_str = dt.strftime("%d/%m %H:%M") if hasattr(dt, 'strftime') else str(dt)
            result.append({"date": date_str, "summary": summary})
            count += 1
        return jsonify(result)
    except Exception as e:
        return jsonify([{"date": "Errore", "summary": str(e)}])

@app.route("/api/briefing")
def get_briefing():
    if not GEMINI_API_KEY:
        return jsonify({"briefing": "GEMINI_API_KEY non configurata."})
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Sei J.A.R.V.I.S., assistente personale di Matteo. Fornisci un briefing operativo, sintetico e futuristico in italiano per oggi."
        response = model.generate_content(prompt)
        return jsonify({"briefing": response.text})
    except Exception as e:
        return jsonify({"briefing": f"Errore generazione briefing: {e}"})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    if not GEMINI_API_KEY:
        return jsonify({"reply": "API Key non impostata."})
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Errore di sistema: {e}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
