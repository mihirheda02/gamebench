from dataclasses import dataclass, field
from typing import List, Tuple
import random
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


@dataclass
class Commodity:
    name: str
    base_value: float
    price_fluctuation: Tuple[float, float]


@dataclass
class MarketTrend:
    commodity: str
    trend: str  # e.g., 'up', 'down', 'stable'


@dataclass
class Observation:
    text: str
    market_trends: List[MarketTrend] = field(default_factory=list)


@dataclass
class CommodityTradingStats:
    commodity_name: str
    trades_count: int = 0
    volume_traded: int = 0


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

    def __post_init__(self):
        self.commodities = [
            Commodity("Wheat", 10.0, (0.9, 1.1)),
            Commodity("Corn", 15.0, (0.8, 1.2)),
            Commodity("Barley", 12.0, (0.85, 1.15)),
            Commodity("Oats", 8.0, (0.95, 1.05)),
        ]
        self.stock_pile = {
            commodity.name: random.randint(1, 10) for commodity in self.commodities
        }
        self.scores = []
        self.round_number = 0
        self.messages = []
        self.market_trends = []
        self.trading_stats = {
            commodity.name: CommodityTradingStats(commodity.name)
            for commodity in self.commodities
        }
        self.previous_round_stats = None

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

    def update_trading_stats(self, commodity_name, volume):
        self.trading_stats[commodity_name].trades_count += 1
        self.trading_stats[commodity_name].volume_traded += volume

    def calculate_market_trends_adjust_values(self):
        if self.previous_round_stats:
            for commodity_name, stats in self.trading_stats.items():
                previous_stats = self.previous_round_stats.get(commodity_name)
                commodity_obj = next(
                    filter(lambda x: x.name == commodity_name, self.commodities), None
                )

                trade_count_change = stats.trades_count - previous_stats.trades_count
                volume_traded_change = (
                    stats.volume_traded - previous_stats.volume_traded
                )

                # Determine the trend based on the changes in trade count and volume traded
                if trade_count_change > 0 and volume_traded_change > 0:
                    trend = "up"
                    adjustment_factor = 1.05 + min(
                        volume_traded_change / 100, 0.1
                    )  # max adjustment capped at 10%
                    commodity_obj.base_value *= adjustment_factor
                elif trade_count_change < 0 and volume_traded_change < 0:
                    trend = "down"
                    adjustment_factor = 0.95 - min(
                        abs(volume_traded_change) / 100, 0.1
                    )  # max adjustment capped at 10%
                    commodity_obj.base_value *= adjustment_factor
                else:
                    trend = "stable"

                self.market_trends.append(MarketTrend(commodity_name, trend))

        self.previous_round_stats = self.trading_stats.copy()
        self.trading_stats = {
            name: CommodityTradingStats(name) for name in self.trading_stats.keys()
        }

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation_text = (
            f"{agent.agent_id}, it's your turn. Stock Pile: {self.stock_pile}"
        )
        available_actions = AvailableActions(
            instructions="Choose a commodity to trade",
            predefined={
                commodity.name: f"Trade {commodity.name}"
                for commodity in self.commodities
            },
            openended={},
        )
        return (
            Observation(text=observation_text, market_trends=self.market_trends),
            available_actions,
        )

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        chosen_commodity = action.action_id
        if chosen_commodity in available_actions.predefined:
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if commodity:
                if self.stock_pile[chosen_commodity] > 0:
                    self.stock_pile[chosen_commodity] -= 1
                    fluctuated_value = commodity.base_value * random.uniform(
                        *commodity.price_fluctuation
                    )
                    if random.random() < 0.1:
                        if random.choice(["Bull", "Bear"]) == "Bull":
                            fluctuated_value *= 1.2
                            if self.show_state:
                                print(
                                    f"Bull effect! {chosen_commodity} value increased by 20%."
                                )
                        else:
                            fluctuated_value *= 0.8
                            if self.show_state:
                                print(
                                    f"Bear effect! {chosen_commodity} value decreased by 20%."
                                )
                    self.scores[self.agents.index(agent)] += fluctuated_value
                    if self.show_state:
                        print(
                            f"{agent.agent_id} traded {chosen_commodity} at {fluctuated_value}"
                        )
                else:
                    if self.show_state:
                        print(f"No more {chosen_commodity} in stock pile.")
        else:
            if self.show_state:
                print("Invalid action. Choosing a random action instead.")
            chosen_commodity = random.choice(list(available_actions.predefined.keys()))
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if commodity:
                if self.stock_pile[chosen_commodity] > 0:
                    self.stock_pile[chosen_commodity] -= 1
                    fluctuated_value = commodity.base_value * random.uniform(
                        *commodity.price_fluctuation
                    )
                    if random.random() < 0.1:
                        if random.choice(["Bull", "Bear"]) == "Bull":
                            fluctuated_value *= 1.2
                            if self.show_state:
                                print(
                                    f"Bull effect! {chosen_commodity} value increased by 20%."
                                )
                        else:
                            fluctuated_value *= 0.8
                            if self.show_state:
                                print(
                                    f"Bear effect! {chosen_commodity} value decreased by 20%."
                                )
                    self.scores[self.agents.index(agent)] += fluctuated_value
                    if self.show_state:
                        print(
                            f"{agent.agent_id} traded {chosen_commodity} at {fluctuated_value}"
                        )
                else:
                    if self.show_state:
                        print(f"No more {chosen_commodity} in stock pile.")

    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            self.round_number += 1
            for agent in self.agents:
                observation, available_actions = self.get_observation(agent)

                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.update(action, available_actions, agent)
                self.calculate_market_trends_adjust_values()
                if all(value == 0 for value in self.stock_pile.values()):
                    self.game_is_over = True

        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]
        return tuple(normalized_scores)
