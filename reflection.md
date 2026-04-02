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

**Later revision — restructured during full implementation:**
During the core implementation phase, the design shifted to better match the instruction requirements: `Pet` now owns its `tasks` list directly, and `Owner` manages a `pets: list[Pet]` instead of a single pet. `Scheduler` now takes only `Owner` and retrieves all tasks via `owner.get_all_tasks()`, which loops through each pet's pending tasks. This makes the data flow cleaner: Pet → Owner → Scheduler. `CareTask` also gained a `frequency` attribute ("daily", "weekly", "as-needed") and a `mark_complete()` method to better represent a real task lifecycle.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: (1) **time budget** — `Owner.available_minutes` caps the total duration of scheduled tasks; (2) **priority** — tasks are ranked by a composite score that boosts feeding and medical tasks above grooming and enrichment; (3) **category exclusivity** — only one feeding and one exercise task can be scheduled per day to prevent redundant care.

Priority and time budget mattered most because a pet owner's core problem is "I only have 60 minutes — what absolutely must happen?" Category exclusivity came second as a safety check to avoid scheduling both pets' breakfast tasks when only one feeding slot makes sense.

**b. Tradeoffs**

The scheduler uses a **greedy, first-fit strategy**: it picks the highest-scoring task that fits in the remaining time budget, then moves on. It never backtracks or tries a different combination to fit more tasks.

For example, if a 50-minute high-priority task is picked first and leaves only 10 minutes, a set of three 9-minute medium-priority tasks that would collectively be more valuable all get skipped. A more optimal algorithm (like a knapsack solver) would find the better combination — but it would be significantly harder to implement, test, and explain to a user.

The greedy approach is reasonable here because pet care tasks are not interchangeable optimisation problems — a high-priority medical task genuinely should go first, even if it crowds out lower-priority tasks. The tradeoff favours predictability and transparency over theoretical optimality.

---

## 3. AI Collaboration

**a. How you used AI**

I used VS Code Copilot across every phase of the project:

- **Design brainstorming** — used Copilot Chat with `#codebase` to generate the initial Mermaid UML diagram from a natural language description of the five classes, then again to review the skeleton for missing relationships.
- **Code generation** — used Agent Mode and Inline Chat to generate class stubs from the UML, then flesh out method bodies incrementally (e.g., `build_plan()`, `detect_conflicts()`).
- **Test planning** — opened a dedicated chat session to ask for edge case suggestions across five test areas, then implemented each test myself based on that plan.
- **Documentation** — used the Generate Documentation smart action to add docstrings to all methods at once.

The most effective prompts were specific and structural: providing the class names, method signatures, and asking Copilot to target a named method rather than the whole file. Vague prompts ("improve my scheduler") produced generic suggestions; targeted prompts ("based on `#file:pawpal_system.py`, how should `Scheduler._rank_tasks()` handle equal-priority tasks?") produced actionable ones.

**b. Judgment and verification**

The clearest example of rejecting a suggestion was when Copilot proposed rewriting `detect_conflicts()` using `itertools.combinations` to make it more "Pythonic." The suggestion was technically correct and shorter, but it replaced an explicit nested loop with a function that a reader needs to know about to understand. I kept the original version because readability mattered more than brevity here — a future reader (or a student) should be able to trace exactly what pairs of tasks are being compared without needing to know the `itertools` library.

I verified this by reading both versions side by side and asking: "if someone unfamiliar with this code needed to debug a false conflict warning, which version would they understand faster?" The explicit loop won.

I also rejected Copilot's suggestion to move `has_time_for()` from `Owner` to `Scheduler`. I evaluated it by asking whether the method's logic depended on `Owner`'s data alone (yes — just `available_minutes`) or required knowledge of the scheduling process (no). Since it only reads owner state, it belongs on `Owner`. Moving it to `Scheduler` would have made `Scheduler` responsible for both scheduling decisions and owner state — a violation of single responsibility.

**c. Separate chat sessions**

Using separate chat sessions for each phase (design, implementation, testing, documentation) was essential for staying focused. When all phases share one context window, Copilot's suggestions start blending concerns — a testing session that has implementation history may suggest changes to production code rather than just tests. Fresh sessions kept each phase clean. The discipline also mirrors real team workflows where different concerns are handled in separate PRs or tickets.

**d. Being the lead architect**

The key lesson was that AI tools are fast at generating plausible-looking code but have no stake in the overall design coherence. Copilot would happily suggest adding `tasks` to `Owner` AND keeping tasks on `Pet` AND passing tasks into `Scheduler` — all in the same session — without flagging the contradiction. Staying the lead architect meant holding the mental model of "where does data live and who owns it" and using that to accept, reject, or modify every suggestion. The AI accelerated the work; the design judgment had to come from me.

---

## 4. Testing and Verification

**a. What you tested**

20 pytest tests across five areas: task behavior (`mark_complete`, `add_task`), scoring and priority (`task_score` category boost), scheduling (time budget enforcement, empty plan, all tasks exceeding budget), sorting (`sort_by_time` chronological order, duplicate start times), recurring tasks (daily auto-creates next occurrence due tomorrow, as-needed does not), conflict detection (overlapping windows produce warnings, non-overlapping do not), and filtering (by pet name, nonexistent name, exact case match).

These tests mattered because the scheduler's core promise is "I will pick the right tasks in the right order within your time limit." Without tests for the edge cases — empty task list, all tasks too long, duplicate categories — it's easy to ship a scheduler that works for the happy path but silently fails the moment an owner has an unusual setup.

**b. Confidence**

4 out of 5. The logic layer (`pawpal_system.py`) is well covered and I'm confident it behaves correctly for all tested cases. The gap is the Streamlit UI — session state behavior, button interactions, and the multi-owner switching are only manually verified. If I had more time I would test: tasks with `due_date` in the past (should still schedule for daily), an owner with zero `available_minutes`, and `detect_conflicts()` with three overlapping tasks (not just two).

---

## 5. Reflection

**a. What went well**

The part I'm most satisfied with is the data flow architecture: `CareTask` → `Pet` → `Owner` → `Scheduler` → `DailyPlan`. Each class has a clear, single responsibility and the dependencies only flow in one direction. This made it straightforward to test each layer in isolation and to extend the system (e.g., adding multi-owner support to the UI) without touching the backend logic at all.

**b. What you would improve**

If I had another iteration I would add a `start_time` input validation step — right now the app accepts any string in the `start_time` field and would crash on `detect_conflicts()` if the format is wrong (e.g., "8am" instead of "08:00"). I would also redesign the category exclusivity logic in `build_plan()` to be configurable rather than hardcoded, so owners could decide for themselves whether to allow two feeding tasks.

**c. Key takeaway**

The most important thing I learned is that AI collaboration requires you to hold the design in your head more explicitly than when coding alone. When working solo, design decisions accumulate naturally in your memory. When working with AI, the tool has no memory of those decisions between sessions — it will suggest things that contradict earlier choices unless you re-establish context every time. Writing the UML first and keeping `reflection.md` updated wasn't just a course requirement; it was the mechanism that kept the AI working toward a coherent system instead of generating plausible-but-inconsistent code.
