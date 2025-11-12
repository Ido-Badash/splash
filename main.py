from game.core import BaseGame, logger
from game.states import Menu, Night1

def main():
    game = BaseGame()
    states = [
        Night1(), Menu()
    ]
    for s in states:
        s.game = game
        game.add_state(s)
    game.run()

if __name__ == "__main__":
    main()