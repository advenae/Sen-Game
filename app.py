from flask import Flask, session, render_template, url_for, request, redirect
import random

app = Flask(__name__)


class Deck:
    def __init__(self):
        self.cards = []

    def generate_deck(self):
        for _ in range(9):
            self.cards.append(Card(9))

        for number in range(9):
            for _ in range(4):
                self.cards.append(Card(number))

        for _ in range(6):
            self.cards.append(Card(6, 'P'))

        random.shuffle(self.cards)


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


class Game:
    def __init__(self):
        self.num_players = 2
        self.players = [[] for _ in range(self.num_players)]
        self.turn_counter = 0
        self.current_player = 0
        self.face_down_pile = []
        self.face_up_pile = []

    def switch_to_next_player(self):
        self.current_player = (self.current_player + 1) % self.num_players
        self.turn_counter += 1

    def deal_cards(self, deck):
        for _ in range(4):
            for player in self.players:
                player.append(deck.cards.pop(0))

    def reveal_deck_cards(self, deck):
        self.face_up_pile.append(deck.cards.pop(0))
        self.face_down_pile.append(deck.cards.pop(0))

    def fill_piles(self):
        while len(self.face_down_pile) < 2 and deck.cards:
            self.face_down_pile.append(deck.cards.pop(0))

    def take_face_down_card(self, exchange_index):
        if not self.face_down_pile or not self.players[self.current_player]:
            return None

        new_card = self.face_down_pile.pop()

        if 0 <= exchange_index < len(self.players[self.current_player]):
            old_card = self.players[self.current_player].pop(exchange_index)
            self.players[self.current_player].insert(exchange_index, new_card)
            self.face_up_pile.append(old_card)
            self.fill_piles()
            self.switch_to_next_player()

            if not self.face_down_pile:
                finish_game()

            return old_card
        else:
            return None

    def leave_face_down_card(self):
        if not self.face_down_pile:
            return None

        card = self.face_down_pile.pop()
        self.face_up_pile.append(card)
        self.fill_piles()
        self.switch_to_next_player()

        return card

    def take_face_up_card(self, exchange_index):
        new_card = self.face_up_pile.pop()

        if 0 <= exchange_index < len(self.players[self.current_player]):
            old_card = self.players[self.current_player].pop(exchange_index)
            self.players[self.current_player].insert(exchange_index, new_card)
            self.face_up_pile.append(old_card)
            self.switch_to_next_player()

            return old_card
        else:
            return None


@app.route('/new_game', methods=['POST'])
def new_game():
    global game, deck
    game = Game()
    deck = Deck()
    deck.generate_deck()
    game.deal_cards(deck)
    game.reveal_deck_cards(deck)

    return redirect(url_for('game'))


@app.route('/end_screen', methods=['GET', 'POST'])
def end_screen():
    player_sums = [sum(card.number for card in player_hand) for player_hand in game.players]
    max_nine_count = max(sum(1 for card in player_hand if card.number == 9) for player_hand in game.players)
    winner_index = min(range(len(player_sums)), key=player_sums.__getitem__)
    player_nine_counts = [sum(1 for card in player_hand if card.number == 9) for player_hand in game.players]

    if max_nine_count > 0 and sum(1 for count in player_nine_counts if count == max_nine_count) == 1:
        for i in range(len(game.players)):
            if player_nine_counts[i] == max_nine_count:
                nine_sum = 9 * max_nine_count
                player_sums[i] -= nine_sum

    return render_template('end_screen.html', players=game.players, sums=player_sums, winner=winner_index)


@app.route('/game', methods=['GET', 'POST'])
def game():
    revealed = False
    if request.method == 'POST':
        action = request.form['action']

        if action == 'take_face_up':
            exchange_index = int(request.form['exchange_index'])
            card = game.take_face_up_card(exchange_index)
        elif action == 'take_face_down':
            exchange_index = int(request.form['exchange_index'])
            card = game.take_face_down_card(exchange_index)
            revealed = True
        elif action == 'leave_face_down':
            card = game.leave_face_down_card()
            revealed = False

        if not game.face_down_pile:
            return game.end_game()

        return render_template('game.html',
                               players=game.players,
                               current_player=game.current_player,
                               face_down_top=game.face_down_pile[-1] if game.face_down_pile else None,
                               face_up_top=game.face_up_pile[-1] if game.face_up_pile else None,
                               revealed=revealed,
                               turn_counter=game.turn_counter)

    return render_template('game.html',
                           players=game.players,
                           current_player=game.current_player,
                           face_down_top=game.face_down_pile[-1] if game.face_down_pile else None,
                           face_up_top=game.face_up_pile[-1] if game.face_up_pile else None,
                           revealed=revealed,
                           turn_counter=game.turn_counter)


def finish_game():
    return redirect(url_for('end_screen'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/rules', methods=['GET', 'POST'])
def rules():
    return render_template('rules.html')


if __name__ == '__main__':
    game = Game()
    deck = Deck()
    deck.generate_deck()
    game.deal_cards(deck)
    game.reveal_deck_cards(deck)

    app.run(host='0.0.0.0', port=12136, debug=True)
