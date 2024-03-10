from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import random
from classes import Observation, Action, Agent, AvailableActions, Game, Rules


@dataclass
class Commodity:
    name: str
    value: float


@dataclass
class Observation:
    text: str


@dataclass
class PitGame(Game):
    rules: Rules = Rules(
        title="Pit",
        summary="""Pit is a commodity trading game where players engage in trading to accumulate points and emerge as the winner.
        The game involves commodity cards representing various goods, with each card holding a specific point value.
        Players shout out their trade offers, attempting to negotiate deals with others to acquire valuable commodities.
        Additionally, Bull and Bear cards periodically influence the market conditions, either boosting or decreasing commodity values.
        The game continues with trading phases, market fluctuations, and scoring until a player or team reaches the agreed-upon point total,
        declaring them the victor in the spirited world of commodity trading.""",
        additional_details=None,
    )
    id: str = "pit"
    agent_virtual_players: Dict[int, List[int]] = field(default_factory=dict)
    virtual_player_hands: Dict[int, Dict[str, int]] = field(default_factory=dict)
    virtual_player_scores: Dict[int, float] = field(default_factory=dict)
    agents: List[Agent] = field(default_factory=list)

    def __post_init__(self):
        self.commodities = [
            Commodity("Barley", 85.0),
            Commodity("Corn", 75.0),
            Commodity("Soyabeans", 55.0),
            Commodity("Wheat", 100.0),
            Commodity("Bull", 0.0),
            Commodity("Bear", 0.0),
        ]
        self.scores = []
        self.round_number = 0

    def setup_virtual_players(self):
        virtual_player_id = 0
        for agent in self.agents:
            self.agent_virtual_players[agent.agent_id] = [
                virtual_player_id,
                virtual_player_id + 1,
            ]
            for vp_id in self.agent_virtual_players[agent.agent_id]:
                self.virtual_player_scores[vp_id] = 0.0
                self.virtual_player_hands[vp_id] = {
                    commodity.name: 0 for commodity in self.commodities
                }
            virtual_player_id += 2

    def shuffle_cards(self):
        virtual_player_id = 0
        for agent in self.agents:
            self.agent_virtual_players[agent.agent_id] = [
                virtual_player_id,
                virtual_player_id + 1,
            ]
            for vp_id in self.agent_virtual_players[agent.agent_id]:
                self.virtual_player_scores[vp_id] = 0.0
                self.virtual_player_hands[vp_id] = {
                    commodity.name: 0 for commodity in self.commodities
                }
            virtual_player_id += 2

        for vp_id in self.virtual_player_hands.keys():
            for _ in range(9):
                selected_commodity = random.choice(self.commodities).name
                self.virtual_player_hands[vp_id][selected_commodity] += 1

    def init_game(
        self,
        agent_1_cls: Agent,
        agent_2_cls: Agent,
    ):
        agent_1 = agent_1_cls(
            team_id=0,
            agent_id=1,
            agent_type_id=agent_1_cls.agent_type_id,
            **self.agent_1_kwargs,
        )
        agent_2 = agent_2_cls(
            team_id=1,
            agent_id=2,
            agent_type_id=agent_2_cls.agent_type_id,
            **self.agent_2_kwargs,
        )
        self.agents = [agent_1, agent_2]
        self.scores = [0.0] * len(self.agents)
        self.setup_virtual_players()

    def check_corners_update_score(self):
        for vp_id, hand in self.virtual_player_hands.items():
            bull_card = hand.get("Bull", 0)
            bear_card = hand.get("Bear", 0)
            for commodity, count in hand.items():
                is_corner = count == 9 or (count == 8 and bull_card)
                if is_corner:
                    commodity_obj = next(
                        (c for c in self.commodities if c.name == commodity), None
                    )
                    if commodity_obj:
                        score = commodity_obj.value
                        if bull_card and count == 8:
                            print(
                                f"Virtual Player {vp_id} has a Bull Corner on {commodity}."
                            )
                        if bull_card and count == 9:
                            score *= 2  # Double Bull Corner
                            print(
                                f"Virtual Player {vp_id} has a Double Bull Corner on {commodity}."
                            )
                        if bear_card:
                            score -= 20 * bear_card  # Penalty for holding Bear card

                        self.virtual_player_scores[vp_id] += score
                        print(
                            f"Virtual Player {vp_id} has cornered the market on {commodity}. Score updated."
                        )

                        for agent_id, vp_ids in self.agent_virtual_players.items():
                            if vp_id in vp_ids:
                                self.scores[
                                    self.agents.index(
                                        next(
                                            agent
                                            for agent in self.agents
                                            if agent.agent_id == agent_id
                                        )
                                    )
                                ] = sum(self.virtual_player_scores[vp] for vp in vp_ids)
                                break
                        self.shuffle_cards()

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        agent_hand = self.virtual_player_hands[
            self.agent_virtual_players[agent.agent_id][0]
        ]
        hand_description = ", ".join(
            [
                f"{count} x {commodity}"
                for commodity, count in agent_hand.items()
                if count > 0
            ]
        )

        observation_text = (
            f"Agent {agent.agent_id}, it's your turn. Your hand: {hand_description}. "
            f"You can trade up to 4 cards of the same commodity at once."
        )

        available_actions = AvailableActions(
            instructions="Choose a commodity and quantity to trade",
            predefined={
                f"{commodity.name}_{quantity}": f"Trade {quantity} {commodity.name}"
                for commodity in self.commodities
                for quantity in range(1, 5)
            },
            openended={},
        )

        return Observation(text=observation_text), available_actions

    def update(
        self,
        action: Action,
        available_actions: AvailableActions,
        agent: Agent,
        other_agent: Agent,
    ):
        print(action.action_id)
        chosen_commodity, trade_quantity = action.action_id.split("_")
        trade_quantity = int(trade_quantity)
        print(chosen_commodity, trade_quantity)

        if (
            chosen_commodity in available_actions.predefined
            and 1 <= trade_quantity <= 4
        ):
            for vp_id in self.agent_virtual_players[agent.agent_id]:
                if self.virtual_player_hands[vp_id][chosen_commodity] >= trade_quantity:
                    self.virtual_player_hands[vp_id][chosen_commodity] -= trade_quantity
                    for other_vp_id in self.agent_virtual_players[other_agent.agent_id]:
                        self.virtual_player_hands[other_vp_id][
                            chosen_commodity
                        ] += trade_quantity
                        break
                    if self.show_state:
                        print(
                            f"Virtual Player {vp_id} traded {trade_quantity} {chosen_commodity} with Virtual Player {other_vp_id}"
                        )
                    self.check_corners_update_score()
                    break
        else:
            if self.show_state:
                print("Invalid action. Choosing a random action instead.")
            chosen_commodity, trade_quantity = random.choice(
                list(available_actions.predefined.keys())
            ).split("_")
            trade_quantity = int(trade_quantity)
            for vp_id in self.agent_virtual_players[agent.agent_id]:
                if self.virtual_player_hands[vp_id][chosen_commodity] >= trade_quantity:
                    self.virtual_player_hands[vp_id][chosen_commodity] -= trade_quantity
                    traded = False

                    for other_vp_id in self.agent_virtual_players[other_agent.agent_id]:
                        if (
                            sum(self.virtual_player_hands[other_vp_id].values())
                            + trade_quantity
                            <= 9
                        ):
                            self.virtual_player_hands[other_vp_id][
                                chosen_commodity
                            ] += trade_quantity
                            traded = True
                            if self.show_state:
                                print(
                                    f"Virtual Player {vp_id} randomly traded {trade_quantity} {chosen_commodity} cards with Virtual Player {other_vp_id}"
                                )
                            break

                    if traded:
                        self.check_corners_update_score()
                        break
                else:
                    if self.show_state:
                        print(
                            f"Virtual Player {vp_id} doesn't have {trade_quantity} {chosen_commodity} cards to trade."
                        )

    def play(self) -> Tuple[float, float]:
        self.shuffle_cards()

        while not self.game_is_over:
            self.round_number += 1
            current_agent = self.agents[(self.round_number - 1) % len(self.agents)]
            other_agent = self.agents[1 - ((self.round_number - 1) % len(self.agents))]

            observation, available_actions = self.get_observation(current_agent)

            action = current_agent.take_action(
                self.rules,
                observation,
                available_actions,
                show_state=True,
            )
            self.update(action, available_actions, current_agent, other_agent)
            print(self.scores)

            print(f"End of round {self.round_number}. Scores: {self.scores}")

            if True in [score >= 500 for score in self.scores]:
                self.game_is_over = True

        print(
            f"Agent {self.agents[self.scores.index(max(self.scores))].agent_id} won with a score of {max(self.scores)}."
        )
        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]
        return tuple(normalized_scores)
