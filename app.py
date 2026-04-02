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
    # Only create a fresh Owner if one doesn't exist yet; preserve existing pets otherwise
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
        # → calls owner.add_pet(pet): registers the pet with the owner
        new_pet = Pet(name=pet_name, species=species, age=1)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"Added pet: {pet_name} ({species})")

    if st.session_state.owner.pets:
        st.write("Pets registered:")
        st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)}
                  for p in st.session_state.owner.pets])

# --- Section 3: Add a task to a pet ---
st.divider()
st.subheader("3. Add a Care Task")

if not st.session_state.owner or not st.session_state.owner.pets:
    st.info("Add at least one pet above before adding tasks.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Select pet", pet_names)
    # Look up the actual Pet object from the owner's list
    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)

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
        task = CareTask(title=task_title, duration_minutes=int(duration),
                        priority=priority, category=category)
        # → calls pet.add_task(task): attaches the task to the selected pet
        selected_pet.add_task(task)
        st.success(f"Added '{task_title}' to {selected_pet_name}")

    pending = selected_pet.get_pending_tasks()
    if pending:
        st.write(f"Tasks for {selected_pet.name}:")
        st.table([{"title": t.title, "duration (min)": t.duration_minutes,
                   "priority": t.priority, "category": t.category}
                  for t in pending])
    else:
        st.info(f"No tasks for {selected_pet.name} yet.")

# --- Section 4: Generate schedule ---
st.divider()
st.subheader("4. Generate Today's Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    elif not st.session_state.owner.get_all_tasks():
        st.warning("Please add at least one task to a pet first.")
    else:
        # → Scheduler.build_plan() pulls tasks from owner.get_all_tasks()
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.build_plan()
        summary = plan.summary()

        st.success(f"Plan ready: {summary['scheduled_count']} scheduled, "
                   f"{summary['skipped_count']} skipped, "
                   f"{summary['total_duration_minutes']} min used.")

        if plan.scheduled_tasks:
            st.markdown("**Scheduled:**")
            for task, reason in plan.scheduled_tasks:
                st.markdown(f"- {task}  \n  _{reason.split(': ', 1)[-1]}_")

        if plan.skipped_tasks:
            st.markdown("**Skipped:**")
            for task, reason in plan.skipped_tasks:
                st.markdown(f"- {task}  \n  _{reason.split(': ', 1)[-1]}_")

        st.info(f"Time used: {plan.total_duration_minutes} / "
                f"{st.session_state.owner.available_minutes} min")
