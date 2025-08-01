import json
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader('../templates'))
template = env.get_template('weekly_template.html')

# Load planner config
with open('../planner_config.json') as f:
    config = json.load(f)

# Load events data
with open('../events_data.json') as f:
    all_events = json.load(f)['events']

# Choose a week to render (change this to test other weeks)
week_start = datetime(2025, 10, 6)  # Example: start of Autumn 1 Week 6
week_end = week_start + timedelta(days=6)


# Filter events for this week
def get_events_for_week(events, start, end):
    filtered = []
    for e in events:
        event_date = datetime.strptime(e['date'], "%Y-%m-%d")
        if start <= event_date <= end:
            filtered.append({"date": e['date'], "title": e['title']})
    return filtered


weekly_events = get_events_for_week(all_events, week_start, week_end)

# Dummy tasks (replace with dynamic input later)
due_this_week = [
    "Mark writing books",
    "Send home learning",
    "Upload reading levels"
]

due_next_week = [
    "Prep for Parents Evening",
    "Submit data to SLT"
]

# Render the HTML with context
output_html = template.render(
    date=week_start.strftime("%d %B %Y"),
    events=weekly_events,
    due_this_week=due_this_week,
    due_next_week=due_next_week,
    teacher_name=config["teacher_name"],
    school_name=config["school_name"]
)

# Write to output folder
with open("../output/weekly_example.html", "w", encoding="utf-8") as f:
    f.write(output_html)

print("✅ Weekly overview generated: output/weekly_example.html")


# Load and render the planner (timetable) page
planner_template = env.get_template('planner_template.html')

planner_html = planner_template.render(
    date=week_start.strftime("%d %B %Y"),
    weekly_slots=config["weekly_slots"],
    teacher_name=config["teacher_name"],
    school_name=config["school_name"]
)

# Save planner page
with open("../output/planner_example.html", "w", encoding="utf-8") as f:
    f.write(planner_html)

print("✅ Planner page generated: output/planner_example.html")
