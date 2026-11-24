"""Scenario state, held in code: stages advance in order and the facts they
reveal accumulate. Each stage's answer is graded by the oral grader against
that stage's rubric, with the facts revealed so far in the question."""

import math
from dataclasses import dataclass

from waypoint_api.exercises import Exercise, Scenario, Stage

SYNTHETIC = "All weather in this scenario is synthetic, for training only."


class ScenarioFinished(Exception):
    """A finished scenario cannot advance."""


@dataclass
class ScenarioState:
    """Where a student is in a scenario."""

    scenario: Scenario
    index: int = 0

    @property
    def finished(self) -> bool:
        """True once every stage has been answered."""
        return self.index == len(self.scenario.stages)

    @property
    def stage(self) -> Stage:
        """The current stage."""
        if self.finished:
            raise ScenarioFinished(self.scenario.id)
        return self.scenario.stages[self.index]

    def revealed(self) -> list[str]:
        """The facts of every stage up to and including the current one."""
        stages = self.scenario.stages[: self.index + 1]
        return [fact for stage in stages for fact in stage.facts]

    def advance(self) -> None:
        """Move to the next stage, or finish after the last."""
        if self.finished:
            raise ScenarioFinished(self.scenario.id)
        self.index += 1


def stage_exercise(state: ScenarioState) -> Exercise:
    """The current stage as an oral exercise for the grader: the scenario,
    the facts revealed so far and the stage's question."""
    scenario, stage = state.scenario, state.stage
    facts = "\n".join(f"- {fact}" for fact in state.revealed())
    return Exercise(
        id=f"{scenario.id}.{stage.id}",
        exam=scenario.exam,
        objective_id=scenario.objective_id,
        prompt=f"{scenario.prompt}\n\nWhat you know so far:\n{facts}\n\n"
        f"{stage.question}",
        sources=scenario.sources,
        rubric=stage.rubric,
    )


def overall_score(stage_scores: list[int]) -> int:
    """The mean of the stage scores, halves rounded up as in exercises.score."""
    return math.floor(sum(stage_scores) / len(stage_scores) + 0.5)
