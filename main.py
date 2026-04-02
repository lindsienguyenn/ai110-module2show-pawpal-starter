from pawpal_system import CareTask, Pet, Owner, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=60)

# Pet 1: a dog
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_task(CareTask("Morning walk", 20, "high", "exercise"))
mochi.add_task(CareTask("Feed breakfast", 10, "high", "feeding"))
mochi.add_task(CareTask("Brush fur", 15, "low", "grooming"))

# Pet 2: a cat
luna = Pet(name="Luna", species="cat", age=5)
luna.add_task(CareTask("Feed breakfast", 5, "high", "feeding"))
luna.add_task(CareTask("Clean litter box", 10, "medium", "grooming"))
luna.add_task(CareTask("Playtime", 20, "low", "enrichment"))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner)
plan = scheduler.build_plan()

print("=== Today's Schedule ===")
print(f"Owner: {owner.name}  |  Time budget: {owner.available_minutes} min")
print(f"Pets: {', '.join(p.name for p in owner.pets)}\n")
print(plan.display())
print("\n--- Summary ---")
for key, value in plan.summary().items():
    print(f"  {key}: {value}")
