from flask import Flask, render_template, url_for, request, session, redirect
import random

app = Flask(__name__)

class Card:
    def __init__(self, number, action=None):
        self.number = int(number)
        self.action = action

    def __repr__(self):
        return f'{self.number} {self.action}' if self.action else str(self.number)

    def to_dict(self):
        card_dict = {'number': self.number}
        if self.action:
            card_dict['action'] = self.action
        return card_dict


class Deck:
    def __init__(self):
        self.cards = []

    def generate_deck(self):
        # Add 4 cards of each number from 0 to 8
        for number in range(9):
            for _ in range(4):
                self.cards.append(Card(number))

        # Add 9 cards with the number 9
        for _ in range(9):
            self.cards.append(Card(9))

        # Add 9 special cards
        special_cards = [
            (5, 'W'), (5, 'W'), (5, 'W'),
            (6, 'P'), (6, 'P'), (6, 'P'),
            (7, 'Z'), (7, 'Z'), (7, 'Z')
        ]
        for number, action in special_cards:
            self.cards.append(Card(number, action))

        # Shuffle the deck
        random.shuffle(self.cards)


class Game:
    def __init__(self, num_players):
        self.num_players = num_players
        self.players = [[] for _ in range(num_players)]
        self.face_down_pile = []
        self.face_up_pile = []
        self.current_player = 0

    def switch_to_next_player(self):
        self.current_player = (self.current_player + 1) % self.num_players
    def deal_cards(self, deck):
        for _ in range(4):
            for player in self.players:
                player.append(deck.cards.pop(0))

    def reveal_deck_cards(self, deck):
        self.face_up_pile.append(deck.cards.pop(0))
        self.face_down_pile.append(deck.cards.pop(0))

    def take_face_up_card(self, exchange_index):
        new_card = self.face_up_pile.pop()

        # Player chooses which card to exchange
        if 0 <= exchange_index < len(self.players[self.current_player]):
            old_card = self.players[self.current_player].pop(exchange_index)
            self.players[self.current_player].insert(exchange_index, new_card)

            # Place the old card on top of the face-up pile
            self.face_up_pile.insert(0, old_card)

            self.switch_to_next_player()

            return old_card
        else:
            # Invalid exchange_index
            return None

    def fill_piles(self):
        while len(self.face_up_pile) < 2:
            self.face_up_pile.append(deck.cards.pop(0))

        while len(self.face_down_pile) < 2:
            self.face_down_pile.append(deck.cards.pop(0))

    def take_face_down_card(self, exchange_index):
        if not self.face_down_pile or not self.players[self.current_player]:
            return None  # No cards in the face-down pile or player's hand

        new_card = self.face_down_pile.pop()

        if 0 <= exchange_index < len(self.players[self.current_player]):
            old_card = self.players[self.current_player].pop(exchange_index)
            self.players[self.current_player].insert(exchange_index, new_card)

            self.face_up_pile.append(old_card)
            self.fill_piles()
            self.switch_to_next_player()
            return old_card
        else:
            # Invalid exchange_index
            return None

    def leave_face_down_card(self):
        if not self.face_down_pile:
            return None  # No cards in the face-down pile

        card = self.face_down_pile.pop()

        # Perform actions based on the game rules
        self.face_up_pile.append(card)

        self.fill_piles()
        self.switch_to_next_player()

        return card

@app.route('/end_screen', methods=['GET', 'POST'])
def end_screen():
    # Calculate the sum of points for each player
    player_sums = [sum(card.number for card in player_hand) for player_hand in game.players]

    # Find the winner (player with the lowest sum of points)
    winner_index = min(range(len(player_sums)), key=player_sums.__getitem__)

    return render_template('end_screen.html', players=game.players, sums=player_sums, winner=winner_index)

@app.route('/game', methods=['GET', 'POST'])
def game():
    revealed = False  # Initialize revealed status
    if request.method == 'POST':
        action = request.form['action']

        if action == 'take_face_up':
            exchange_index = int(request.form['exchange_index'])
            card = game.take_face_up_card(exchange_index)
        elif action == 'take_face_down':
            exchange_index = int(request.form['exchange_index'])
            card = game.take_face_down_card(exchange_index)
            revealed = True  # Set revealed status to True
        elif action == 'leave_face_down':
            card = game.leave_face_down_card()
            revealed = False  # Reset revealed status

        return render_template('game.html',
                               players=game.players,
                               current_player=game.current_player,
                               face_down_top=game.face_down_pile[-1] if game.face_down_pile else None,
                               face_up_top=game.face_up_pile[-1] if game.face_up_pile else None,
                               revealed=revealed)  # Pass revealed status to the template

    return render_template('game.html',
                           players=game.players,
                           current_player=game.current_player,
                           face_down_top=game.face_down_pile[-1] if game.face_down_pile else None,
                           face_up_top=game.face_up_pile[-1] if game.face_up_pile else None,
                           revealed=revealed)  # Pass revealed status to the template

if __name__ == '__main__':
    game = Game(num_players=2)

    deck = Deck()
    deck.generate_deck()

    game.deal_cards(deck)

    game.reveal_deck_cards(deck)

    app.run(host='0.0.0.0', port=12136, debug=True)
