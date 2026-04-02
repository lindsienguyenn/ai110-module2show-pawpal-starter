from pawpal_system import CareTask, Pet, Owner, Scheduler


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
