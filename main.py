from game import BaseGame, logger, build_states

def main():
    game = BaseGame()
    states = build_states()
    for s in states:
        game.add_state(s)
    game.run()

if __name__ == "__main__":
    main()