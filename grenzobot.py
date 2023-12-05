import json
import os
import random
import copy


class Card:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Game:
    def __init__(self, deck):
        self.cards = deck
        for card in self.cards:
            card.zone = 'Library'
        self.shuffle()
        self.turn = 0
        self.commander_in_play = False
        self.mana_pool = 0
        self.pulls = 0
        self.hits = 0
        

    def shuffle(self):
        random.shuffle(self.cards)

    def untap(self):
        for card in [x for x in self.cards if x.zone == 'Battlefield']:
            card.tapped = False

    def draw_card(self):
        library = [x for x in self.cards if x.zone == 'Library']
        if library:
            library[0].zone = 'Hand'
        else:
            print('Library is empty, you lose the game!')

    def play_land(self):
        lands_in_hand = [x for x in self.cards if x.zone == 'Hand' and 'Land' in x.type_line]
        if lands_in_hand:
            lands_in_hand[0].zone = 'Battlefield'
            lands_in_hand[0].tapped = False

    def tap_out(self):
        for land in [x for x in self.cards if x.zone == 'Battlefield' and 'Land' in x.type_line]:
            if not land.tapped:
                land.tapped = True
                self.mana_pool += 1

    def pull(self):
        self.pulls += 1
        bottom_card = [x for x in self.cards if x.zone == 'Library'][-1]
        if bottom_card.name == 'Workhorse':
            self.hits += 1
            self.mana_pool += 4
            bottom_card.zone = 'Graveyard'
        elif bottom_card.name in ["Emrakul's Hatcher", 'Priest of Gix', 'Priest of Urabrask']:
            bottom_card.zone = 'Battlefield'
            self.hits += 1
            self.mana_pool += 3
        elif bottom_card.name in ['Kalain, Reclusive Painter', 'Wily Goblin']:
            bottom_card.zone = 'Battlefield'
            self.hits += 1
            self.mana_pool += 1
        elif 'Creature' in bottom_card.type_line:
            bottom_card.zone = 'Battlefield'
            self.hits += 1
        else:
            bottom_card.zone = 'Graveyard'

    def land_count(self, zone):
        return len([x for x in self.cards if x.zone == zone and 'Land' in x.type_line])

    def state(self):
        print(f'Turn {self.turn}:')
        for zone in ['Hand', 'Battlefield', 'Graveyard']:
            print(f'{zone}: {len([x for x in self.cards if x.zone == zone])} cards'
                  f'{[x.name for x in self.cards if x.zone == zone]}')


def process_decklist(database, decklist):

    # Read json data from file
    path = os.path.join(os.path.dirname(__file__), database)
    with open(path, 'r', encoding="utf-8") as f:
        data = json.load(f)

    # Load json data to class objects
    all_cards = [Card(**obj) for obj in data]

    # Add cards to deck
    deck = []
    path = os.path.join(os.path.dirname(__file__), decklist)
    with open(path, encoding="utf-8") as f:
        for ln in f:
            line = ln.strip().split(' ', 1)
            qty = int(line[0])
            card_name = line[1]
            card_obj = next((card for card in all_cards if card.name == card_name), None)
            for _ in range(qty):
                deck.append(copy.copy(card_obj))
    return deck



def simulate_game(deck, cast_genzo_on, num_turns):

    def land_thing():
        # create game object
        game = Game(deck)
        # draw opening hand
        for _ in range(7):
            game.draw_card()
        # check numbers of lands in hand
        if game.land_count('Hand') >= 3:
            return game
        else:
            return land_thing()
        
    # start a new game
    game = land_thing()
    pull_cost = 2

    # loop for each turn
    for _ in range(num_turns):

        game.turn += 1
        game.untap()
        game.draw_card()
        game.play_land()
        game.tap_out()

        for card in [x for x in game.cards if x.zone == 'Hand']:

            # cast heartstone
            if card.name == 'Heartstone' and game.mana_pool >= int(card.cmc):
                card.zone = 'Battlefield'
                game.mana_pool -= int(card.cmc)
                pull_cost = 1

        if game.commander_in_play:
            # do pulls
            while game.mana_pool >= pull_cost:
                game.mana_pool -= pull_cost
                game.pull()
        elif game.mana_pool >= cast_genzo_on:
            # cast grenzo
            game.mana_pool -= cast_genzo_on
            game.commander_in_play = True

    return game.pulls, game.hits


if __name__=='__main__':

    deck = process_decklist('scryfall_data.json', 'decklist.txt')

    cast_on = 3
    turns = 8
    simulations = 5000
    sum_pulls = 0
    sum_hits = 0

    print(f'Simualate {simulations} games, cast Grenzo on {cast_on}, play to turn {turns}.')

    for _ in range(simulations):
        pulls, hits = simulate_game(deck, cast_on, turns)
        sum_pulls += pulls
        sum_hits += hits

    print(f'Average hits per game: {sum_hits/simulations}')
    # print(f'Hit percentage: {sum_hits/sum_pulls*100}')


    for num_pulls in range(5,11):
        sum_hits = 0
        cycles = 10000
        for _ in range(cycles):
            game = Game(deck)
            for _ in range(num_pulls):
                game.pull()
            for _ in range(game.mana_pool//2):
                game.pull()
            sum_hits += game.hits
        print(f'Average hits with {num_pulls} pulls: {sum_hits/cycles}')