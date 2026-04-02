from pawpal_system import CareTask, Pet, Owner, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

# Tasks added OUT OF ORDER intentionally to test sort_by_time()
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_task(CareTask("Evening walk",   20, "medium", "exercise",   "daily", "17:00"))
mochi.add_task(CareTask("Feed breakfast", 10, "high",   "feeding",    "daily", "08:00"))
mochi.add_task(CareTask("Morning walk",   20, "high",   "exercise",   "daily", "07:00"))
mochi.add_task(CareTask("Brush fur",      15, "low",    "grooming",   "weekly","09:00"))

luna = Pet(name="Luna", species="cat", age=5)
luna.add_task(CareTask("Feed breakfast",  5,  "high",   "feeding",    "daily", "08:30"))
luna.add_task(CareTask("Clean litter",    10, "medium", "grooming",   "daily", "09:00"))
luna.add_task(CareTask("Playtime",        20, "low",    "enrichment", "daily", "08:45"))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# --- 1. Sort by time ---
print("=== Today's Schedule ===")
print(f"Owner: {owner.name}  |  Budget: {owner.available_minutes} min")
print(f"Pets: {', '.join(p.name for p in owner.pets)}\n")

all_due = scheduler.get_due_tasks()
sorted_tasks = scheduler.sort_by_time(all_due)
print("--- Tasks sorted by start time ---")
for t in sorted_tasks:
    print(f"  {t}")

# --- 2. Filter tasks ---
print("\n--- Filter: Mochi's tasks only ---")
mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
for t in mochi_tasks:
    print(f"  {t}")

print("\n--- Filter: pending tasks only ---")
pending = scheduler.filter_tasks(completed=False)
for t in pending:
    print(f"  {t}")

# --- 3. Recurring task auto-renewal ---
print("\n--- Recurring task: mark Mochi's feed complete ---")
feed_task = next(t for t in mochi.tasks if t.title == "Feed breakfast")
print(f"  Before: {feed_task}")
scheduler.mark_task_complete(feed_task, mochi)
print(f"  After:  {feed_task}")
new_task = mochi.tasks[-1]
print(f"  Next occurrence created: {new_task.title} due {new_task.due_date}")

# --- 4. Conflict detection ---
print("\n--- Conflict detection ---")
# Luna has Feed breakfast at 08:30 and Playtime at 08:45 — they overlap
conflicts = scheduler.detect_conflicts(luna.get_pending_tasks())
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

# --- Full schedule ---
print("\n")
plan = scheduler.build_plan()
print(plan.display())
print("\n--- Summary ---")
for key, value in plan.summary().items():
    print(f"  {key}: {value}")
