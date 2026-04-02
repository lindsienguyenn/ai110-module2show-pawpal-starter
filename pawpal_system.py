from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CareTask:
    """A single pet care activity."""
    title: str
    duration_minutes: int
    priority: str        # "low", "medium", "high"
    category: str        # "feeding", "exercise", "medical", "grooming", "enrichment"
    frequency: str = "daily"   # "daily", "weekly", "as-needed"
    completed: bool = False

    def priority_value(self) -> int:
        """Return a numeric value for the priority to enable sorting."""
        mapping = {"high": 3, "medium": 2, "low": 1}
        if self.priority not in mapping:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be 'low', 'medium', or 'high'.")
        return mapping[self.priority]

    def task_score(self) -> int:
        """Return a composite score for ranking: weighs priority, urgency category, and brevity."""
        category_boost = 20 if self.category in ("feeding", "medical") else 0
        return self.priority_value() * 10 + (100 - self.duration_minutes) + category_boost

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule based on its frequency."""
        if self.frequency == "daily":
            return True
        if self.frequency == "weekly":
            return datetime.today().weekday() == 0  # Mondays
        # "as-needed" tasks are never auto-scheduled; owner adds them manually
        return False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        """Return a readable string showing priority, title, duration, and status."""
        status = "done" if self.completed else "pending"
        return f"[{self.priority.upper()}] {self.title} ({self.duration_minutes} min) [{status}]"


@dataclass
class Pet:
    """A pet with its own list of care tasks."""
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask):
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> list[CareTask]:
        """Return only tasks that have not been completed."""
        return [t for t in self.tasks if not t.completed]

    def get_default_tasks(self) -> list[CareTask]:
        """Return a species-appropriate list of default care tasks."""
        if self.species == "dog":
            return [
                CareTask("Morning walk", 20, "high", "exercise", "daily"),
                CareTask("Feed breakfast", 10, "high", "feeding", "daily"),
                CareTask("Feed dinner", 10, "high", "feeding", "daily"),
            ]
        if self.species == "cat":
            return [
                CareTask("Feed breakfast", 5, "high", "feeding", "daily"),
                CareTask("Feed dinner", 5, "high", "feeding", "daily"),
                CareTask("Clean litter box", 10, "medium", "grooming", "daily"),
            ]
        return [CareTask("Feed", 10, "high", "feeding", "daily")]


@dataclass
class Owner:
    """An owner who manages one or more pets."""
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self, pet_names: list[str] | None = None) -> list[CareTask]:
        """Collect all pending tasks across pets, optionally filtered by pet name."""
        all_tasks = []
        for pet in self.pets:
            if pet_names and pet.name not in pet_names:
                continue
            all_tasks.extend(pet.get_pending_tasks())
        return all_tasks

    def has_time_for(self, task: CareTask, minutes_used: int) -> bool:
        """Return True if the task fits within the owner's remaining available time."""
        return (minutes_used + task.duration_minutes) <= self.available_minutes


class Scheduler:
    """Retrieves, ranks, and schedules tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_due_tasks(self, pet_names: list[str] | None = None) -> list[CareTask]:
        """Return all pending tasks that are due today, optionally filtered by pet name."""
        return [t for t in self.owner.get_all_tasks(pet_names) if t.is_due_today()]

    def _rank_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Sort tasks by composite score (priority + category urgency + brevity), highest first."""
        return sorted(tasks, key=lambda t: (-t.task_score(), t.duration_minutes))

    def _explain(self, task: CareTask, reason: str) -> str:
        """Build a human-readable explanation string for why a task was scheduled or skipped."""
        return f"'{task.title}' ({task.priority} priority, {task.duration_minutes} min): {reason}"

    def build_plan(self, pet_names: list[str] | None = None) -> "DailyPlan":
        """Build a daily plan from due tasks, with conflict detection and time-budget enforcement."""
        due_tasks = self.get_due_tasks(pet_names)
        ranked = self._rank_tasks(due_tasks)

        scheduled = []
        skipped = []
        minutes_used = 0
        scheduled_categories: set[str] = set()
        exclusive_categories = {"exercise", "feeding"}

        for task in ranked:
            # Conflict detection: block duplicate exclusive-category tasks
            if task.category in exclusive_categories and task.category in scheduled_categories:
                skipped.append((task, self._explain(task, f"category '{task.category}' already scheduled")))
                continue

            if self.owner.has_time_for(task, minutes_used):
                scheduled.append((task, self._explain(task, "fits within available time")))
                minutes_used += task.duration_minutes
                scheduled_categories.add(task.category)
            else:
                skipped.append((task, self._explain(task, "not enough time remaining")))

        return DailyPlan(
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            total_duration_minutes=minutes_used,
        )


@dataclass
class DailyPlan:
    """The output of a scheduling run."""
    scheduled_tasks: list[tuple[CareTask, str]] = field(default_factory=list)
    skipped_tasks: list[tuple[CareTask, str]] = field(default_factory=list)
    total_duration_minutes: int = 0

    def display(self) -> str:
        """Format the full plan as a human-readable string for terminal or UI output."""
        lines = ["=== Daily Care Plan ===\n"]
        if self.scheduled_tasks:
            lines.append("Scheduled:")
            for task, reason in self.scheduled_tasks:
                lines.append(f"  - {task}")
        else:
            lines.append("No tasks scheduled.")

        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task, reason in self.skipped_tasks:
                lines.append(f"  - {task}")
                lines.append(f"    Reason: {reason.split(': ', 1)[-1]}")

        lines.append(f"\nTotal time: {self.total_duration_minutes} min")
        return "\n".join(lines)

    def summary(self) -> dict:
        """Return a dict of key counts and totals for the scheduled plan."""
        return {
            "scheduled_count": len(self.scheduled_tasks),
            "skipped_count": len(self.skipped_tasks),
            "total_duration_minutes": self.total_duration_minutes,
            "high_priority_scheduled": sum(
                1 for t, _ in self.scheduled_tasks if t.priority == "high"
            ),
        }
