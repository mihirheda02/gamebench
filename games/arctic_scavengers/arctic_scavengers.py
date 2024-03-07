from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
from cards.game_cards import *
import random
 
@dataclass
class ArcticScavengers(Game):
    class Player:
        def __init__(self, agent):
            self.agent = agent
            self.cards = {"deck":[], "draw":[]}
            self.actions = {ActionSymbol.DIG: 0, ActionSymbol.DRAW: 0, ActionSymbol.HUNT: 0, "HIRE": 0, "TRASH":0, "SNIPER":0, "SABOTEUR":0} 
            self.food = 0
        
        def create_deck(self, deck):
            pass

        def draw_hand(self):
            # Both players draw 5 cards from top of their deck. If deck is empty, shuffle discard pile and draw from there.
            pass

        def reset_actions(self):
            self.food = 0
            for action in self.actions:
                self.actions[action] = 0
    class Deck:
        def __init__(self):
            self.contested_resources = []
            self.junkyard = []
            self.mercenaries = [[]] # 8 mercenary piles

    rules : Rules = Rules(
        title="Arctic Scavengers",
        summary="""
        Players work to build their tribes as large as possible by hiring mercenaries, scavenging junk piles and winning skirmishes against other players' tribes.
        Each tribe member card in a tribe represents the number of people shown on the card.
        The player with the largest tribe at the end of the game is the winner.
        """,
        # Give instructions on game setup here, the different deck piles, and how each round will work, and how you win.
        # 14 turns in total, as there are 14 contested resource cards in the pile.
        additional_details = None
    )
    id : str = "arctic_scavengers"

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_2_kwargs)]
        self.players = [self.Player(self.agents[0]), self.Player(self.agents[1])]
        self.deck = self.Deck()
        # TODO: Initialise 10 cards for each player (4 refugee, 3 scavenger, 1 brawler, 1 spear, 1 shovel)
        for player in self.players:
            player.create_deck(self.deck)
        self.game_winner = None
    
    def observation_resource_gather(self, player : Player) -> Tuple[Observation, AvailableActions]:
        player.reset_actions()
        context = "This is your draw hand, and the information on your cards."
        for card in player.cards["draw"]:
            context += "\n" + str(card)
        context += f"\nYou have {player.food} FOOD currency."
        context += "\nThe contested resources pile has " + str(len(self.deck.contested_resources)) + " cards and the junkyard pile has " + str(len(self.deck.junkyard)) + " cards."
        for pile in self.deck.mercenaries:
            if pile:
                context += "\nThe " + pile[0].title + " pile has " + str(len(pile)) + " cards."
                context += "\n" + str(pile[0])
        context += "\nThe HUNT action allows you to generate food during a single round, that can be used as currency for hiring a single mercenary card."
        context += "\nAny card you play of type MODIFIER must be combined with a STANDARD card. The MODIFIER card will add to the score of the STANDARD card."
        observation = Observation(text=context) 
        s = "Choose cards to use and discard in an action, otherwise say STOP and your current hand will remain for the skirmish. Remember that each of the actions DIG, DRAW, HIRE, HUNT, TRASH can only be used once.", 
        s += "\nThe DIG action allows you to draw one or more cards from the top of the junkyard pile, determined by the sum of DIG values you play. You may choose a maximum of one card to place in your reserve deck, and return any other cards to the bottom of the junkyard pile.",
        s += "\nThe DRAW action allows you to draw one or more cards from your reserve deck, adding them to your playing hand. The number is determined by the sum of the DRAW values you play.",
        s += "\nThe HIRE action allows you to hire one mercenary and add it to your reserve deck. The MEDICINE and FOOD currency you play must equal the cost of the mercenary card.",
        s += "\nThe HUNT action allows you to generate FOOD currency that is equal to the sum of the HUNT values you play. This currency can be used to hire mercenaries.",
        s += "\nThe TRASH action allows you to choose one or more cards from your playing hand to add to the junkyard pile, which is shuffled after each new card added."
        s += "\nFor the actions DIG, DRAW, HUNT or TRASH, return as an openended response a tuple of the action name and a list of the card titles you are using for this action."
        s += "\nFor example, (\"DIG\", [\"Brawler\", \"Shovel\"])."
        s += "\nFor the action HIRE, return as an openended response a tuple of the action, a list of the MEDICINE card titles you are using for this action, and the title of the mercenary you want to hire. You must have gathered enough FOOD currency gained by HUNTing for this action."
        s += "\nFor example, (\"HIRE\", [\"Pills\"], \"Saboteur\")."
        s += "\nFor STOP, return (\"STOP\", [])"
        available_actions = AvailableActions(
             instructions = s,            
             openended = {
                    "DIG": "Draw one or more cards from the top of the junkyard pile, determined by the sum of DIG values you play. You may choose a maximum of one card to place in your reserve deck, and return any other cards to the bottom of the junkyard pile.",
                    "DRAW": "Draw one or more cards from your reserve deck, adding them to your playing hand. The number is determined by the sum of the DRAW values you play.",
                    "HIRE": "Hire one mercenary and add it to your reserve deck. The MEDICINE and FOOD currency you play must equal the cost of the mercenary card.",
                    "HUNT": "Generate FOOD currency that is equal to the sum of the HUNT values you play. This currency can be used to hire mercenaries.",
                    "TRASH": "Choose one or more cards from your playing hand to add to the junkyard pile, which is shuffled after each new card added.",
                    "STOP": "Stop gathering resources and move to the skirmish phase."
                    #Add the ability to snipe during the opponent's turn
             },
             predefined = {}
        )
        return observation, available_actions

    def observation_skirmish(self, player : Player) -> Tuple[Observation, AvailableActions]:
        context = "This is the hand you have brought to the skirmish. Your opponent can see your hand."
        for card in player.cards["draw"]:
            context += "\n" + str(card) 
        context += "\n This is the hand your opponent has brought to the skirmish. You can see their hand."
        for card in self.players[1 - player].cards["draw"]:
            context += "\n" + str(card)
        observation = Observation(text=context)
        s += "Choose whether to perform a SNIPE or SABOTEUR action towards your opponent, if you have the cards in your hand. Otherwise, say STOP and your skirmish actions will end."
        s +- "\nThe winner of the round is determined by the highest fight value, and if there is a tie then the biggest tribe. Otherwise the contested resource is shuffled in the junkyard pile."
        s += "\nThe SNIPER action allows you to snipe one tribe member, forcing it to be discarded."
        s += "\nThe SABOTEUR action allows you to disarm one tool card, forcing it to be discarded."
        s += "\nFor the actions SNIPER or SABOTEUR, return as an openended response a tuple of the action name and the card title of your opponent that you are performing this action on."
        s += "\nFor the action STOP, return (\"STOP\", "")"
        available_actions = AvailableActions(
             instructions = s,            
             openended = {
                    "SNIPER": "Snipe one tribe member, forcing it to be discarded.",
                    "SABOTEUR": "Disarm one tool card, forcing it to be discarded.",
                    "STOP": "Stop taking further actions in the skirmish."
             },
             predefined = {}
        )
        return observation, available_actions
    
    def observation_respond_to_action(self, player : Player, action : Action) -> Tuple[Observation, AvailableActions]:
        context = "Your opponent has announced that they are taking the following action."
        context += "\n" + str(action.action_id) + " " + str(action.openended_response)
        observation = Observation(text=context)
        s = "You have the option to perform a SNIPER or SABOTEUR action then discard any cards that you play."
        s += "\nThe SNIPER action allows you to snipe one tribe member, forcing it to be discarded by the opponent."
        s += "\nThe SABOTEUR action allows you to disarm one tool card, forcing it to be discarded by the opponent."
        s += "If you are unable or don't want to take these actions, take the action STOP and return (\"STOP\", "")."
        s += "Otherwise, for the actions SNIPER or SABOTEUR, return as an openended response a tuple of the action name and the card title of your opponent that you are performing this action on."
        s += "\nFor example, (\"SNIPER\", [\"Brawler\"])."
        available_actions = AvailableActions(
             instructions = s,            
             openended = {
                    "SNIPER": "Snipe one tribe member, forcing it to be discarded.",
                    "SABOTEUR": "Disarm one tool card, forcing it to be discarded.",
                    "STOP": "Stop taking further actions in the skirmish."
             },
             predefined = {}
        )
        return observation, available_actions

    def update_resource_gather(self, action : Action,  available_actions : AvailableActions, player : Player, action2 : Action, player2 : Player):
        # If you snipe/sabotage during the skirmish phase, the sniper/saboteur card remains in your hand.
        # If action is invalid then a random one is taken.  I.e. take first card from hand and do something with it. Or trash a card.
        pass  

    def update_skirmish(self, action : Action, available_actions : AvailableActions, player : Player, player2 : Player):
        pass

    def play_resource_gather(self, player : Player, other : int):
        # Make sure in while loop that actions are not repeated and each one is valid.
        observation, available_actions = self.observation_resource_gather(player.agent)
        action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        while action[0] != "STOP":
            observation2, available_actions2 = self.observation_respond_to_action(self.players[other], action)
            action2 = self.players[other].agent.take_action(self.rules, observation2, available_actions2, show_state=self.show_state)
            self.update_resource_gather(action, available_actions, player, action2, self.players[other])
            observation, available_actions = self.observation_resource_gather(player.agent)
            action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            # while loop to check if action is valid and not repeated

    def play_skirmish(self, player : Player, other : int):
        observation, available_actions = self.observation_skirmish(player.agent)
        action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        while action != "STOP":
            self.update(action, available_actions, player, self.players[other])
            observation, available_actions = self.observation_skirmish(player.agent)
            action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

    def play(self) -> Tuple[float, float]:
        count = 0
        while self.deck.contested_resources:
            initiator = count % 2
            #### DRAWING PHASE #### 
            for player in self.players:
                player.draw_hand()

            #### RESOURCE GATHERING PHASE ####
            player = self.players[initiator]
            self.play_resource_gather(player, 1-initiator)
            player = self.players[1 - initiator]
            self.play_resource_gather(player, initiator)
            
            #### SKIRMISH PHASE ####
            player = self.players[initiator]
            self.play_skirmish(player)
            player = self.players[1 - initiator]
            self.play_skirmish(player)
            fight_scores = [self.players[0].calculate_fight_score(), self.players[1].calculate_fight_score()]
            if fight_scores[0] > fight_scores[1]:
                self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
            elif fight_scores[0] < fight_scores[1]:
                self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
            else:
                people_scores = [self.players[0].calculate_people(), self.players[1].calculate_people()]
                if people_scores[0] > people_scores[1]:
                    self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
                elif people_scores[0] < people_scores[1]:
                    self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
                else:
                    self.deck.junkyard.append(self.deck.contested_resources.pop(0))
            
            count += 1
        return (1, 0) if self.players[0].calculate_people() > self.players[1].calculate_people() else (0, 1)