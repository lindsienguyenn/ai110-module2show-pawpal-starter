import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler, DailyPlan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state "vault" ---
# Check before creating so the Owner survives page reruns.
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

# --- Step 1: Owner + Pet setup ---
st.subheader("Owner & Pet Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=60)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet = Pet(name=pet_name, species=species, age=1)
    owner = Owner(name=owner_name, available_minutes=available_minutes)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.success(f"Saved! {owner_name} is caring for {pet_name} ({species}).")

# --- Step 2: Add tasks ---
st.divider()
st.subheader("Add Care Tasks")

if st.session_state.pet is None:
    st.info("Save an owner & pet above before adding tasks.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        category = st.selectbox("Category", ["exercise", "feeding", "medical", "grooming", "enrichment"])

    if st.button("Add task"):
        task = CareTask(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
        )
        st.session_state.pet.add_task(task)
        st.success(f"Added: {task_title}")

    # Show current task list
    pending = st.session_state.pet.get_pending_tasks()
    if pending:
        st.write(f"Tasks for {st.session_state.pet.name}:")
        st.table([
            {"title": t.title, "duration (min)": t.duration_minutes, "priority": t.priority, "category": t.category}
            for t in pending
        ])
    else:
        st.info("No tasks yet. Add one above.")

# --- Step 3: Generate schedule ---
st.divider()
st.subheader("Generate Today's Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner & pet first.")
    elif not st.session_state.pet.get_pending_tasks():
        st.warning("Please add at least one task first.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.build_plan()

        st.success(f"Plan ready! {plan.summary()['scheduled_count']} tasks scheduled, "
                   f"{plan.summary()['skipped_count']} skipped.")

        if plan.scheduled_tasks:
            st.markdown("**Scheduled:**")
            for task, reason in plan.scheduled_tasks:
                st.markdown(f"- {task}  \n  _{reason.split(': ', 1)[-1]}_")

        if plan.skipped_tasks:
            st.markdown("**Skipped:**")
            for task, reason in plan.skipped_tasks:
                st.markdown(f"- {task}  \n  _{reason.split(': ', 1)[-1]}_")

        st.info(f"Total time used: {plan.total_duration_minutes} / {st.session_state.owner.available_minutes} min")
