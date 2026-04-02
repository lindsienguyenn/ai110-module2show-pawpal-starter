from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)

    def get_default_tasks(self) -> list:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)

    def has_time_for(self, task) -> bool:
        pass


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    category: str
    completed: bool = False

    def priority_value(self) -> int:
        mapping = {"high": 3, "medium": 2, "low": 1}
        if self.priority not in mapping:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be 'low', 'medium', or 'high'.")
        return mapping[self.priority]

    def __repr__(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[CareTask]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def build_plan(self) -> "DailyPlan":
        pass

    def _rank_tasks(self) -> list[CareTask]:
        pass

    def _explain(self, task: CareTask) -> str:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[tuple["CareTask", str]] = field(default_factory=list)
    skipped_tasks: list[tuple["CareTask", str]] = field(default_factory=list)
    total_duration_minutes: int = 0

    def display(self) -> str:
        pass

    def summary(self) -> dict:
        pass
