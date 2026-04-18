from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from . import describer_registry as DescriberRegistry
from .base import BaseDescriber

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment


@DescriberRegistry.register("prisoner")
class PrisonerDescriber(BaseDescriber):
    switch_func = {
        "Both Suspects": "Suspect2",
        "Suspect1": "Suspect2",
        "Suspect2": "Suspect1",
    }
    receiver: str = "Both Suspects"

    def get_env_description(self, environment: BaseEnvironment) -> List[str]:
        if environment.cnt_turn == 0:
            environment.agents[0].set_receiver({"all"})
            environment.agents[1].set_receiver({"Police", "Suspect1"})
            environment.agents[2].set_receiver({"Police", "Suspect2"})
        description = []
        for i, agent in enumerate(environment.agents):
            if i == 0:
                if environment.cnt_turn % 2 == 1:
                    description.append("")
                    continue
                description.append(f"You are now talking to {self.receiver}")

                receiver = "all" if self.receiver == "Both Suspects" else self.receiver
                self.receiver = self.switch_func[self.receiver]
                agent.set_receiver({receiver})

            else:
                description.append("")

        return description

    def reset(self) -> None:
        pass
