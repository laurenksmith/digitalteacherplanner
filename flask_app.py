# starter_flask_app.py
from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

DATA_FILE = 'events_data.json'

# Load existing events or create empty list
def load_events():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save events to file
def save_events(events):
    with open(DATA_FILE, 'w') as f:
        json.dump(events, f, indent=2)

@app.route('/')
def index():
    events = load_events()
    return render_template('index.html', events=events)

@app.route('/add', methods=['POST'])
def add_event():
    events = load_events()
    new_event = {
        'title': request.form['title'],
        'date': request.form['date'],
        'notes': request.form['notes']
    }
    events.append(new_event)
    save_events(events)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
