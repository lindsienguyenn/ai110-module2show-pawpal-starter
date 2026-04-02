import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state vault ---
if "owner" not in st.session_state:
    st.session_state.owner = None

# --- Section 1: Owner setup ---
st.subheader("1. Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=60)

if st.button("Save owner"):
    if st.session_state.owner is None:
        st.session_state.owner = Owner(name=owner_name, available_minutes=available_minutes)
    else:
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = available_minutes
    st.success(f"Owner saved: {owner_name} ({available_minutes} min available today)")

# --- Section 2: Add a pet ---
st.divider()
st.subheader("2. Add a Pet")

if st.session_state.owner is None:
    st.info("Save an owner above first.")
else:
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Add pet"):
        new_pet = Pet(name=pet_name, species=species, age=1)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"Added pet: {pet_name} ({species})")

    if st.session_state.owner.pets:
        st.write("Pets registered:")
        st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)}
                  for p in st.session_state.owner.pets])

# --- Section 3: Add a care task ---
st.divider()
st.subheader("3. Add a Care Task")

if not st.session_state.owner or not st.session_state.owner.pets:
    st.info("Add at least one pet above before adding tasks.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Select pet", pet_names)
    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        category = st.selectbox("Category", ["exercise", "feeding", "medical", "grooming", "enrichment"])
    with col5:
        start_time = st.text_input("Start time (HH:MM)", value="08:00")

    if st.button("Add task"):
        task = CareTask(title=task_title, duration_minutes=int(duration),
                        priority=priority, category=category, start_time=start_time)
        selected_pet.add_task(task)
        st.success(f"Added '{task_title}' to {selected_pet_name}")

    # Show tasks sorted by start time
    pending = selected_pet.get_pending_tasks()
    if pending:
        scheduler_preview = Scheduler(st.session_state.owner)
        sorted_pending = scheduler_preview.sort_by_time(pending)
        st.write(f"Tasks for {selected_pet.name} (sorted by start time):")
        st.table([{
            "start time": t.start_time,
            "title": t.title,
            "duration (min)": t.duration_minutes,
            "priority": t.priority,
            "category": t.category,
            "frequency": t.frequency,
        } for t in sorted_pending])

        # Show conflict warnings immediately so owner can fix before scheduling
        conflicts = scheduler_preview.detect_conflicts(pending)
        if conflicts:
            st.warning("**Scheduling conflicts detected — review before generating your plan:**")
            for warning in conflicts:
                # Strip the "WARNING: " prefix for cleaner UI display
                st.warning(warning.replace("WARNING: ", ""))
    else:
        st.info(f"No tasks for {selected_pet.name} yet.")

# --- Section 4: Generate schedule ---
st.divider()
st.subheader("4. Generate Today's Schedule")

# Optional filter: let owner schedule only one pet at a time
if st.session_state.owner and st.session_state.owner.pets:
    all_pet_names = [p.name for p in st.session_state.owner.pets]
    filter_options = ["All pets"] + all_pet_names
    filter_choice = st.selectbox("Schedule tasks for", filter_options)

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    elif not st.session_state.owner.get_all_tasks():
        st.warning("Please add at least one task to a pet first.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        pet_filter = None if filter_choice == "All pets" else [filter_choice]
        plan = scheduler.build_plan(pet_names=pet_filter)
        summary = plan.summary()

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled", summary["scheduled_count"])
        col2.metric("Skipped", summary["skipped_count"])
        col3.metric("Time used (min)", f"{summary['total_duration_minutes']} / {st.session_state.owner.available_minutes}")

        # Scheduled tasks table (sorted by start time)
        if plan.scheduled_tasks:
            st.success("Scheduled tasks:")
            scheduled_sorted = scheduler.sort_by_time([t for t, _ in plan.scheduled_tasks])
            st.table([{
                "start time": t.start_time,
                "title": t.title,
                "priority": t.priority,
                "duration (min)": t.duration_minutes,
                "category": t.category,
            } for t in scheduled_sorted])

        # Skipped tasks — show as warnings with reasons
        if plan.skipped_tasks:
            st.warning("Some tasks were skipped:")
            for task, reason in plan.skipped_tasks:
                st.warning(f"**{task.title}** ({task.priority} priority, {task.duration_minutes} min)  \n"
                           f"Reason: {reason.split(': ', 1)[-1]}")

        # Time budget progress bar
        used = summary["total_duration_minutes"]
        total = st.session_state.owner.available_minutes
        st.caption(f"Time budget: {used} of {total} min used")
        st.progress(min(used / total, 1.0))
