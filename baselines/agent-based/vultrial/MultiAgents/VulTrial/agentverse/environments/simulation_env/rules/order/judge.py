from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, List, Optional

from . import order_registry as OrderRegistry
from .base import BaseOrder
from agentverse.logging import logger

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment


@OrderRegistry.register("judge")
class JudgeOrder(BaseOrder):
    """
    The order for a security researcher team.
    The agents speak in the following order:
      1. The security researcher speaks first
      2. Then the code author defends
      3. Then the judge summarizes
      4. After the above three finish, the jury makes the final decision
    """

    def get_next_agent_idx(self, environment: BaseEnvironment) -> List[int]:
        """
        There are 3 cycles * 3 roles = 9 messages. On the 10th message,
        the Jury speaks. No further turns after that.
        """
        print("**********************")

        turn_number = environment.cnt_turn         

        print(turn_number)

        if len(environment.last_messages) == 0:
            return [0]
        elif len(environment.last_messages) == 1:
            message = environment.last_messages[0]
            sender = message.sender
            if sender.startswith("security_researcher"):
                return [1]
            elif sender.startswith("code_author"):
                return [2]
            else:
                if turn_number < (environment.max_turns - 1):
                    return [0]
                else:
                    return [3]
        return [0]