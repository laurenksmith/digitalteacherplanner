# flask_app.py
from flask import Flask, render_template, request, redirect, url_for
import json
import os
from uuid import uuid4
from datetime import datetime, timedelta


app = Flask(__name__)


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d'):
    return datetime.strptime(value, '%Y-%m-%d').strftime(format)


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
        'id': str(uuid4()),
        'title': request.form['title'],
        'date': request.form['date'],
        'notes': request.form['notes']
    }
    events.append(new_event)
    save_events(events)
    return redirect(url_for('index'))


@app.route('/edit/<event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    events = load_events()
    event = next((e for e in events if e['id'] == event_id), None)

    if request.method == 'POST':
        if event:
            event['title'] = request.form['title']
            event['date'] = request.form['date']
            event['notes'] = request.form['notes']
            save_events(events)
        return redirect(url_for('index'))

    return render_template('edit.html', event=event)


@app.route('/delete/<event_id>')
def delete_event(event_id):
    events = load_events()
    events = [e for e in events if e['id'] != event_id]
    save_events(events)
    return redirect(url_for('index'))


@app.route('/week')
def week_redirect():
    today = datetime.today().date()
    return redirect(url_for('week_view', date=today.isoformat()))


@app.route('/week/<date>')
def week_view(date):
    try:
        base_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD.", 400

    start_of_week = base_date - timedelta(days=base_date.weekday())
    end_of_week = start_of_week + timedelta(days=4)
    next_week_start = end_of_week + timedelta(days=1)
    next_week_end = next_week_start + timedelta(days=6)

    events = load_events()
    week_events = { (start_of_week + timedelta(days=i)).isoformat(): [] for i in range(5) }
    upcoming_tasks = []

    for event in events:
        event_date = event.get('date')
        if event_date in week_events:
            week_events[event_date].append(event)
        else:
            try:
                event_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
                if next_week_start <= event_dt <= next_week_end:
                    upcoming_tasks.append(event)
            except:
                continue

    return render_template('weekly.html', week_events=week_events, upcoming_tasks=upcoming_tasks, start=start_of_week, end=end_of_week)


if __name__ == '__main__':
    app.run(debug=True)
