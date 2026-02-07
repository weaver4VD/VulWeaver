from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, List, Optional

from . import order_registry as OrderRegistry
from .base import BaseOrder
from agentverse.logging import logger

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment


@OrderRegistry.register("classroom")
class ClassroomOrder(BaseOrder):
    """The order for a classroom discussion
    The agents speak in the following order:
    1. The professor speaks first
    2. Then the professor can continue to speak, and the students can raise hands
    3. The professor can call on a student, then the student can speak or ask a question
    4. In the group discussion, the students in the group can speak in turn
    """

    def get_next_agent_idx(self, environment: BaseEnvironment) -> List[int]:
        if environment.rule_params.get("is_grouped_ended", False):
            return [0]
        if environment.rule_params.get("is_grouped", False):
            return self.get_next_agent_idx_grouped(environment)
        else:
            return self.get_next_agent_idx_ungrouped(environment)

    def get_next_agent_idx_ungrouped(self, environment: BaseEnvironment) -> List[int]:
        if len(environment.last_messages) == 0:
            return [0]
        elif len(environment.last_messages) == 1:
            message = environment.last_messages[0]
            sender = message.sender
            content = message.content
            if sender.startswith("Professor"):
                if content.startswith("[CallOn]"):
                    result = re.search(r"\[CallOn\] Yes, ([sS]tudent )?(\w+)", content)
                    if result is not None:
                        name_to_id = {
                            agent.name[len("Student ") :]: i
                            for i, agent in enumerate(environment.agents)
                        }
                        return [name_to_id[result.group(2)]]
                else:
                    return list(range(len(environment.agents)))
            elif sender.startswith("Student"):
                return [0]
        else:
            return [0]
        assert (
            False
        ), f"Should not reach here, last_messages: {environment.last_messages}"

    def get_next_agent_idx_grouped(self, environment: BaseEnvironment) -> List[int]:
        if "groups" not in environment.rule_params:
            logger.warn(
                "The environment is grouped, but the grouping information is not provided."
            )
        groups = environment.rule_params.get(
            "groups", [list(range(len(environment.agents)))]
        )
        group_speaker_mapping = environment.rule_params.get(
            "group_speaker_mapping", {i: 0 for i in range(len(groups))}
        )
        next_agent_idx = []
        for group_id in range(len(groups)):
            speaker_index = group_speaker_mapping[group_id]
            speaker = groups[group_id][speaker_index]
            next_agent_idx.append(speaker)
        for k, v in group_speaker_mapping.items():
            group_speaker_mapping[k] = (v + 1) % len(groups[k])
        environment.rule_params["group_speaker_mapping"] = group_speaker_mapping

        return next_agent_idx
