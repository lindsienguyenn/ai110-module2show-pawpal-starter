# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed five classes for PawPal+:

- **Pet** — holds the animal's basic info (name, species, age, special needs) and can suggest species-appropriate default tasks via `get_default_tasks()`.
- **Owner** — stores the person's name, daily time budget (`available_minutes`), and preferences. Has a `has_time_for(task)` method to check if a task fits within remaining time.
- **CareTask** — represents a single care activity with a title, duration, priority (low/medium/high), category (feeding, exercise, medical, etc.), and completion status. Includes `priority_value()` to convert priority strings to integers for sorting.
- **Scheduler** — the core engine. Takes an `Owner`, a `Pet`, and a list of `CareTask` objects. Ranks tasks by priority, fits them into the owner's time budget, and produces a `DailyPlan`.
- **DailyPlan** — the output object. Holds scheduled tasks, skipped tasks, and total duration. Responsible for formatting and summarizing the plan for display in the UI.

The key design decision was keeping `Scheduler` as a separate engine class rather than putting scheduling logic inside `Owner` or `Pet`, so the logic layer stays isolated and testable.

**b. Design changes**

After asking Copilot to review `pawpal_system.py`, it identified several potential issues. Here is what I changed and what I kept:

**Accepted — `CareTask.priority_value()` should raise on invalid input:**
Copilot flagged that an unknown priority string would silently fail. I agreed — it's better to raise a `ValueError` immediately so bugs surface early rather than producing a wrong schedule quietly.

**Accepted — Type `DailyPlan.scheduled_tasks` and `skipped_tasks` explicitly:**
Both were typed as generic `list`. Copilot suggested `list[tuple[CareTask, str]]` (task + reason string) for clarity. This makes `display()` easier to implement and the intent more obvious.

**Declined — Moving `has_time_for()` from `Owner` to `Scheduler`:**
Copilot suggested this method might belong on `Scheduler` since scheduling is its responsibility. I kept it on `Owner` because it only reads `Owner.available_minutes` — it's a question the owner can answer about themselves. `Scheduler` calls it but doesn't own it.

**Declined — Adding `tasks: list[CareTask]` to `Owner`:**
Copilot suggested `Owner` should hold the task list directly. I kept tasks on `Scheduler` because tasks are inputs to the scheduling process, not inherent properties of the owner. This keeps `Owner` as a simple data object.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
