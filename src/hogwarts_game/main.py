from hogwarts_game.config import Config
from hogwarts_game.engine.game import GameApp


def main() -> None:
    GameApp(Config.load()).run()
