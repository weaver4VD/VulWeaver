from __future__ import annotations
import asyncio
from colorama import Fore

from typing import TYPE_CHECKING, List

from . import decision_maker_registry
from .base import BaseDecisionMaker
from agentverse.logging import typewriter_log

if TYPE_CHECKING:
    from agentverse.agents.base import BaseAgent
    from agentverse.message import Message


@decision_maker_registry.register("dynamic")
class DynamicDecisionMaker(BaseDecisionMaker):
    """
    Discuss in a horizontal manner.
    """

    name: str = "dynamic"
    async def astep(
        self,
        agents: List[BaseAgent],
        manager: List[BaseAgent],
        task_description: str,
        previous_plan: str = "No solution yet.",
        advice: str = "No advice yet.",
        previous_sentence: str = "No any sentence yet.",
        *args,
        **kwargs,
    ) -> List[str]:
        reviews = list()
        for i in range(len(agents)):
            review = await asyncio.gather(
                *[
                    agent.astep(previous_plan, advice, task_description)
                    for agent in agents[1:]
                ]
            )

            previous_sentence = await manager.astep(
                previous_plan, review, advice, task_description, previous_sentence
            )
            reviews.append(previous_sentence)

        """
        reviews = await asyncio.gather(
            *[
                agent.astep(previous_plan, advice, task_description)
                for agent in agents[1:]
            ]
        )
        """

        nonempty_reviews = []
        for review in reviews:
            if not review.is_agree and review.content != "":
                nonempty_reviews.append(review)
        agents[0].add_message_to_memory(nonempty_reviews)

        result = await agents[0].astep(previous_plan, advice, task_description)

        return [result]

    def reset(self):
        pass
