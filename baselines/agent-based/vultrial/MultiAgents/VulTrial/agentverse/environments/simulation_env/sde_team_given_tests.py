import asyncio
from typing import Any, Dict, List
import json

from agentverse.agents.simulation_agent.conversation import BaseAgent
from agentverse.environments.simulation_env.rules.base import SimulationRule as Rule
from agentverse.message import Message
from agentverse.logging import logger

from .. import env_registry as EnvironmentRegistry
from ..base import BaseEnvironment

from agentverse.initialization import load_tools


@EnvironmentRegistry.register("sde_team_given_tests")
class SdeTeamGivenTestsEnvironment(BaseEnvironment):
    """
    A basic environment implementing the logic of conversation to craft code.

    Args:
        agents: List of agents
        rule: Rule for the environment
        max_turns: Maximum number of turns
        cnt_turn: Current turn number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
    """

    agents: List[BaseAgent]
    rule: Rule
    max_turns: int = 10
    cnt_turn: int = 0
    last_messages: List[Message] = []
    rule_params: Dict = {}
    unit_tests: str = ""
   
   
   

    def __init__(self, rule, **kwargs):
        rule_config = rule
        order_config = rule_config.get("order", {"type": "sde_team_given_tests"})
        visibility_config = rule_config.get("visibility", {"type": "base"})
        selector_config = rule_config.get("selector", {"type": "sde_team_given_tests"})
        updater_config = rule_config.get("updater", {"type": "sde_team"})
        describer_config = rule_config.get("describer", {"type": "base"})
        rule = Rule(
            order_config,
            visibility_config,
            selector_config,
            updater_config,
            describer_config,
        )
        super().__init__(rule=rule, **kwargs)
        self.rule_params["first_round"] = True
        self.rule_params["end_flag"] = False

    async def step(self) -> List[Message]:
        """Run one step of the environment"""

        agent_ids = self.rule.get_next_agent_idx(self) 


        messages = await asyncio.gather(*[self.agents[i].astep("") for i in agent_ids])
        self.last_messages = messages

        selected_messages = self.rule.select_message(self, messages) 
        self.last_messages = selected_messages
        self.print_messages(selected_messages)

        self.rule.update_memory(self) 
        self.rule.update_visible_agents(self) 

        self.cnt_turn += 1

        return selected_messages

    def print_messages(self, messages: List[Message]) -> None:
        for message in messages:
            if message is not None:
                logger.info(f"{message.sender}: {message.content}")

    def reset(self) -> None:
        """Reset the environment"""
        self.cnt_turn = 0
        self.rule.reset()
        for agent in self.agents:
            agent.reset()

    def is_done(self) -> bool:
        """Check if the environment is done"""
        if self.cnt_turn >= self.max_turns or self.rule_params["end_flag"]: 
            return True
        return False
