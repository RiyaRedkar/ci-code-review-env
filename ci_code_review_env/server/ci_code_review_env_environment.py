from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import CiCodeReviewAction, CiCodeReviewObservation
except ImportError:
    from models import CiCodeReviewAction, CiCodeReviewObservation


class CiCodeReviewEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)

        
        self.tasks = {
            "easy": {
                "title": "Fix simple bug",
                "diff": "def add(a,b): return a-b",
                "tests": "Expected 5 got -1",
                "bug": "a-b",
                "decision": "request_changes",
            },
            "medium": {
                "title": "Logical error",
                "diff": "if x > 10: return True else False",
                "tests": "Edge case failing",
                "bug": "missing return",
                "decision": "request_changes",
            },
            "hard": {
                "title": "Hidden issue",
                "diff": "list.sort(); return list[0]",
                "tests": "Performance issue",
                "bug": "in-place",
                "decision": "request_changes",
            },
        }

        self.task_names = list(self.tasks.keys())
        self.task_index = 0
        self.current_task_name = "easy"
        self.current_task = self.tasks[self.current_task_name]

    
    def get_tasks(self):
        return self.task_names

    def reset(self) -> CiCodeReviewObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # rotate tasks automatically (validator will hit multiple)
        self.current_task_name = self.task_names[self.task_index]
        self.task_index = (self.task_index + 1) % len(self.task_names)
        self.current_task = self.tasks[self.current_task_name]

        return CiCodeReviewObservation(
            echoed_message=str({
                "task_name": self.current_task_name,
                "pr_title": self.current_task["title"],
                "code_diff": self.current_task["diff"],
                "test_results": self.current_task["tests"],
            }),
            message_length=0,
            done=False,
            reward=0.01,  # must NOT be 0
        )

    def step(self, action: CiCodeReviewAction) -> CiCodeReviewObservation:
        self._state.step_count += 1

        message = action.message.lower()
        task = self.current_task

        score = 0.2  # base (avoid 0)

    
        if self.current_task_name == "easy":
            if task["bug"] in message:
                score = 0.6

        elif self.current_task_name == "medium":
            if task["bug"] in message and task["decision"] in message:
                score = 0.7

        elif self.current_task_name == "hard":
            if (
                task["bug"] in message
                and task["decision"] in message
                and len(message) > 10
            ):
                score = 0.8

    
        score = max(0.01, min(score, 0.99))

        return CiCodeReviewObservation(
            echoed_message=f"task={self.current_task_name}",
            message_length=len(message),
            done=True,
            reward=score,
            metadata={"task": self.current_task_name},
        )

    @property
    def state(self) -> State:
        return self._state