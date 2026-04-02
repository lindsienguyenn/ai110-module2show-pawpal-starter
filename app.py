import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state vault ---
if "owners" not in st.session_state:
    st.session_state.owners = {}   # dict: owner_name -> Owner

# --- Section 1: Owner setup ---
st.subheader("1. Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=60)

if st.button("Save owner"):
    if owner_name not in st.session_state.owners:
        st.session_state.owners[owner_name] = Owner(name=owner_name, available_minutes=available_minutes)
        st.success(f"New owner added: {owner_name}")
    else:
        st.session_state.owners[owner_name].available_minutes = available_minutes
        st.success(f"Updated {owner_name}'s time budget to {available_minutes} min")

if st.session_state.owners:
    st.write("Registered owners:")
    st.table([{"name": o.name, "available minutes": o.available_minutes, "pets": len(o.pets)}
              for o in st.session_state.owners.values()])

# --- Select active owner ---
if not st.session_state.owners:
    st.info("Add at least one owner above to continue.")
    st.stop()

st.divider()
active_owner_name = st.selectbox("Working as owner", list(st.session_state.owners.keys()))
owner = st.session_state.owners[active_owner_name]

# --- Section 2: Add a pet ---
st.subheader(f"2. Add a Pet for {active_owner_name}")

col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species, age=1)
    owner.add_pet(new_pet)
    st.success(f"Added pet: {pet_name} ({species}) for {active_owner_name}")

if owner.pets:
    st.write(f"{active_owner_name}'s pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)}
              for p in owner.pets])
else:
    st.info(f"No pets yet for {active_owner_name}.")

# --- Section 3: Add a care task ---
st.divider()
st.subheader("3. Add a Care Task")

if not owner.pets:
    st.info("Add at least one pet above before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Select pet", pet_names)
    selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

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

    pending = selected_pet.get_pending_tasks()
    if pending:
        scheduler_preview = Scheduler(owner)
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

        conflicts = scheduler_preview.detect_conflicts(pending)
        if conflicts:
            st.warning("**Scheduling conflicts detected — review before generating your plan:**")
            for warning in conflicts:
                st.warning(warning.replace("WARNING: ", ""))
    else:
        st.info(f"No tasks for {selected_pet.name} yet.")

# --- Section 4: Generate schedule ---
st.divider()
st.subheader("4. Generate Today's Schedule")

filter_options = ["All pets"] + [p.name for p in owner.pets]
filter_choice = st.selectbox("Schedule tasks for", filter_options)

if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Please add at least one task to a pet first.")
    else:
        scheduler = Scheduler(owner)
        pet_filter = None if filter_choice == "All pets" else [filter_choice]
        plan = scheduler.build_plan(pet_names=pet_filter)
        summary = plan.summary()

        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled", summary["scheduled_count"])
        col2.metric("Skipped", summary["skipped_count"])
        col3.metric("Time used (min)", f"{summary['total_duration_minutes']} / {owner.available_minutes}")

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

        if plan.skipped_tasks:
            st.warning("Some tasks were skipped:")
            for task, reason in plan.skipped_tasks:
                st.warning(f"**{task.title}** ({task.priority} priority, {task.duration_minutes} min)  \n"
                           f"Reason: {reason.split(': ', 1)[-1]}")

        used = summary["total_duration_minutes"]
        total = owner.available_minutes
        st.caption(f"Time budget: {used} of {total} min used")
        st.progress(min(used / total, 1.0))
