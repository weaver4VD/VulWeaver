import asyncio
import logging
from typing import Any, Dict, List
from agentverse.agents.simulation_agent.conversation import BaseAgent
from agentverse.environments.simulation_env.rules.base import SimulationRule as Rule
from agentverse.message import Message

from .. import env_registry as EnvironmentRegistry
from .basic import BasicEnvironment


@EnvironmentRegistry.register("prisoner_dilemma")
class PrisonerDilemmaEnvironment(BasicEnvironment):
    """
    An environment for prisoner dilemma.
    """

    async def step(self) -> List[Message]:
        """Run one step of the environment"""
        agent_ids = self.rule.get_next_agent_idx(self)
        env_descriptions = self.rule.get_env_description(self)
        messages = await asyncio.gather(
            *[self.agents[i].astep(self, env_descriptions[i]) for i in agent_ids]
        )
        selected_messages = self.rule.select_message(self, messages)
        self.last_messages = selected_messages
        self.print_messages(selected_messages)
        self.rule.update_memory(self)
        self.rule.update_visible_agents(self)

        self.cnt_turn += 1

        return selected_messages
