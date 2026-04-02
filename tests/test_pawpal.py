from pawpal_system import CareTask, Pet, Owner, Scheduler


# --- Existing tests ---

def test_mark_complete_changes_status():
    task = CareTask("Morning walk", 20, "high", "exercise")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(CareTask("Feed breakfast", 10, "high", "feeding"))
    assert len(pet.tasks) == 1
    pet.add_task(CareTask("Brush fur", 15, "low", "grooming"))
    assert len(pet.tasks) == 2


def test_feeding_scores_higher_than_grooming():
    feeding = CareTask("Feed breakfast", 10, "medium", "feeding")
    grooming = CareTask("Brush fur", 10, "medium", "grooming")
    assert feeding.task_score() > grooming.task_score()


def test_daily_task_is_due_today():
    task = CareTask("Feed breakfast", 10, "high", "feeding", frequency="daily")
    assert task.is_due_today() is True


def test_as_needed_task_is_not_due_today():
    task = CareTask("Vet visit", 60, "high", "medical", frequency="as-needed")
    assert task.is_due_today() is False


def test_filter_tasks_by_pet_name():
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=2)
    mochi.add_task(CareTask("Walk", 20, "high", "exercise"))
    luna.add_task(CareTask("Feed", 5, "high", "feeding"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi_tasks = owner.get_all_tasks(pet_names=["Mochi"])
    assert len(mochi_tasks) == 1
    assert mochi_tasks[0].title == "Walk"


def test_conflict_detection_skips_duplicate_feeding():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Feed breakfast", 5, "high", "feeding"))
    pet.add_task(CareTask("Feed dinner", 5, "high", "feeding"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    scheduled_titles = [t.title for t, _ in plan.scheduled_tasks]
    skipped_titles = [t.title for t, _ in plan.skipped_tasks]

    assert len([t for t in scheduled_titles if "Feed" in t]) == 1
    assert any("Feed" in t for t in skipped_titles)


def test_schedule_respects_time_budget():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Long walk", 50, "high", "exercise"))
    pet.add_task(CareTask("Bath", 40, "medium", "grooming"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    assert plan.total_duration_minutes <= owner.available_minutes
    assert len(plan.skipped_tasks) == 1


# --- New edge case tests ---

# 1. Scheduling edge cases

def test_scheduler_with_no_tasks_returns_empty_plan():
    pet = Pet(name="Mochi", species="dog", age=3)
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    assert plan.scheduled_tasks == []
    assert plan.skipped_tasks == []
    assert plan.total_duration_minutes == 0


def test_scheduler_all_tasks_exceed_time_budget_skips_all():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Long walk", 90, "high", "exercise"))
    pet.add_task(CareTask("Bath", 80, "medium", "grooming"))

    owner = Owner(name="Jordan", available_minutes=30)
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 2


# 2. Sorting edge cases

def test_sort_two_tasks_same_start_time_no_tasks_lost():
    pet = Pet(name="Mochi", species="dog", age=3)
    t1 = CareTask("Feed breakfast", 10, "high", "feeding", start_time="08:00")
    t2 = CareTask("Brush fur", 15, "low", "grooming", start_time="08:00")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    assert len(sorted_tasks) == 2  # no tasks lost


def test_no_overlap_tasks_produce_no_conflict_warnings():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Morning walk", 20, "high", "exercise", start_time="07:00"))
    pet.add_task(CareTask("Feed breakfast", 10, "high", "feeding", start_time="08:00"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_conflicts(pet.tasks)
    assert warnings == []


# 3. Recurring task edge cases

def test_mark_task_complete_as_needed_does_not_create_new_occurrence():
    pet = Pet(name="Mochi", species="dog", age=3)
    task = CareTask("Vet visit", 60, "high", "medical", frequency="as-needed")
    pet.add_task(task)

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(pet)

    task_count_before = len(pet.tasks)
    Scheduler(owner).mark_task_complete(task, pet)

    assert task.completed is True
    assert len(pet.tasks) == task_count_before  # no new task added


def test_mark_task_complete_daily_creates_next_occurrence():
    pet = Pet(name="Mochi", species="dog", age=3)
    task = CareTask("Feed breakfast", 10, "high", "feeding", frequency="daily")
    pet.add_task(task)

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    Scheduler(owner).mark_task_complete(task, pet)

    assert task.completed is True
    assert len(pet.tasks) == 2  # original + next occurrence
    assert pet.tasks[-1].completed is False


# 4. Conflict detection edge cases

def test_conflict_detection_same_start_time_raises_warning():
    pet = Pet(name="Mochi", species="dog", age=3)
    t1 = CareTask("Morning walk", 30, "high", "exercise", start_time="08:00")
    t2 = CareTask("Feed breakfast", 10, "high", "feeding", start_time="08:00")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(name="Jordan", available_minutes=60)
    warnings = Scheduler(owner).detect_conflicts(pet.tasks)
    assert len(warnings) >= 1
    assert any("08:00" in w for w in warnings)


# 5. Filtering edge cases

def test_filter_by_nonexistent_pet_name_returns_empty_list():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Walk", 20, "high", "exercise"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    result = owner.get_all_tasks(pet_names=["Nonexistent"])
    assert result == []


def test_filter_by_exact_name_match_only():
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Walk", 20, "high", "exercise"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)

    # lowercase mismatch should return nothing (exact match required)
    result = owner.get_all_tasks(pet_names=["mochi"])
    assert result == []


# --- Required suite: sorting, recurrence, conflict detection ---

def test_sorting_returns_chronological_order():
    """Tasks added out of order must be returned earliest start_time first."""
    from datetime import datetime
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(CareTask("Evening walk",   20, "medium", "exercise", start_time="17:00"))
    pet.add_task(CareTask("Feed breakfast", 10, "high",   "feeding",  start_time="08:00"))
    pet.add_task(CareTask("Morning walk",   20, "high",   "exercise", start_time="07:00"))

    owner = Owner(name="Jordan", available_minutes=90)
    owner.add_pet(pet)
    sorted_tasks = Scheduler(owner).sort_by_time(pet.tasks)

    times = [datetime.strptime(t.start_time, "%H:%M") for t in sorted_tasks]
    assert times == sorted(times)


def test_daily_recurrence_due_date_is_tomorrow():
    """Completing a daily task must produce a new task due exactly one day later."""
    from datetime import datetime, timedelta
    pet = Pet(name="Mochi", species="dog", age=3)
    task = CareTask("Feed breakfast", 10, "high", "feeding", frequency="daily")
    pet.add_task(task)

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)
    Scheduler(owner).mark_task_complete(task, pet)

    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_task = pet.tasks[-1]
    assert next_task.due_date == tomorrow
    assert next_task.completed is False


def test_conflict_detection_flags_overlapping_times():
    """Two tasks whose windows overlap must produce at least one warning message."""
    pet = Pet(name="Luna", species="cat", age=2)
    # Playtime at 08:45 for 20 min ends at 09:05 — overlaps with Clean litter at 09:00
    pet.add_task(CareTask("Playtime",    20, "low",    "enrichment", start_time="08:45"))
    pet.add_task(CareTask("Clean litter", 10, "medium", "grooming",  start_time="09:00"))

    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(pet)
    warnings = Scheduler(owner).detect_conflicts(pet.tasks)

    assert len(warnings) >= 1
    assert any("Playtime" in w or "Clean litter" in w for w in warnings)
