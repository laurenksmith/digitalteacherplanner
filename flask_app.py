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
    today_iso = datetime.today().date().isoformat()
    return render_template('index.html', events=events, today_iso=today_iso)


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

    return render_template(
        'weekly_template.html',
        week_events=week_events,
        upcoming_tasks=upcoming_tasks,
        start=start_of_week,
        end=end_of_week,
        timedelta=timedelta
    )


@app.route('/month')
def month_redirect():
    today = datetime.today().date()
    return redirect(url_for('month_view', year=today.year, month=today.month))


@app.route('/month/<int:year>/<int:month>')
def month_view(year, month):
    try:
        start_of_month = datetime(year, month, 1).date()
    except ValueError:
        return "Invalid date", 400

    # Work out end_of_month
    if month == 12:
        end_of_month = datetime(year, 12, 31).date()
    else:
        end_of_month = datetime(year, month + 1, 1).date() - timedelta(days=1)

    # Grid bounds (Mon..Sun)
    calendar_start = start_of_month - timedelta(days=start_of_month.weekday())
    calendar_end   = end_of_month   + timedelta(days=(6 - end_of_month.weekday()))

    # --- DEBUG: what is rendering
    print(f"month_view: Loading year={year}, month={month}")
    print(f"DEBUG: start_of_month = {start_of_month}, label = {start_of_month.strftime('%B')}, actual month = {month}")

    # Build event_map only for dates inside the grid
    events = load_events()
    event_map = {}
    print(f"[MONTH DEBUG] total events loaded = {len(events)}")

    for idx, event in enumerate(events):
        try:
            raw = event.get('date')
            d = datetime.strptime(raw, '%Y-%m-%d').date()
            in_range = calendar_start <= d <= calendar_end
            # DEBUG per event
            print(f"[MONTH DEBUG] checking #{idx}: {event!r}")
            print(f"[MONTH DEBUG] └ parsed date={d}, in_range={in_range}, month={d.month}, target={month}")

            if in_range:
                event_map.setdefault(d.isoformat(), []).append(event)
                print(f"[MONTH DEBUG] ✓ added on {d}: '{event.get('title','')}'")
            else:
                print(f"[MONTH DEBUG] ✗ skipped (outside grid): {d}")
        except Exception as e:
            print(f"[MONTH DEBUG] !! error on #{idx}: {event!r} -> {e!r}")
            continue

    print("[MONTH DEBUG] summary:",
          {k: len(v) for k, v in sorted(event_map.items())})

    # Create the list of dates to render
    dates = []
    d = calendar_start
    while d <= calendar_end:
        dates.append(d)
        d += timedelta(days=1)

    # Extra debug to confirm the grid length
    print(f"[MONTH DEBUG] dates generated: {len(dates)} from {calendar_start} .. {calendar_end}")

    # Prev/next helpers
    prev_month = month - 1
    prev_year  = year
    next_month = month + 1
    next_year  = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    if next_month == 13:
        next_month = 1
        next_year += 1

    return render_template(
        'monthly_template.html',
        year=year,
        month=month,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
        event_map=event_map,
        today=datetime.today().date(),
        dates=dates,
        start_of_month=start_of_month,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month
    )


@app.route('/year')
def yearly_redirect():
    return redirect(url_for('yearly_view'))


@app.route('/yearly')
def yearly_view():
    events = load_events()
    today = datetime.today().date()
    year = today.year

    # Create a structure to count events in each month
    month_data = {month: [] for month in range(1, 13)}

    for event in events:
        try:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event_date.year == year:
                month_data[event_date.month].append(event)
        except (KeyError, ValueError):
            continue

    return render_template(
        'yearly_template.html',
        year=year,
        month_data=month_data,
        today=today
    )


if __name__ == '__main__':
    app.run(debug=True)
