# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler goes beyond a simple priority sort. Four algorithmic improvements make it more useful for real pet care planning:

**Sort by time** — `Scheduler.sort_by_time()` orders any task list by `start_time` (HH:MM), so the daily plan reads chronologically from morning to evening.

**Filter tasks** — `Scheduler.filter_tasks()` lets you query tasks by pet name or completion status. Useful for displaying only one pet's tasks or showing what's already done.

**Recurring task automation** — `Scheduler.mark_task_complete()` marks a task done and automatically creates the next occurrence using Python's `timedelta`. Daily tasks reappear tomorrow; weekly tasks reappear in 7 days.

**Conflict detection** — `Scheduler.detect_conflicts()` scans scheduled tasks and emits a warning message (rather than crashing) when two tasks' time windows overlap. For example, a 20-minute task at 08:45 conflicts with one starting at 09:00.
