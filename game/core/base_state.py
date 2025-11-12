from typing import TYPE_CHECKING, Optional
import luneth_engine as le

if TYPE_CHECKING:
    from .base_game import BaseGame

class BaseState(le.State):
    game: "BaseGame"  # type hint for IDE's

    def __init__(self, name: str, game: Optional["BaseGame"] = None):
        super().__init__(name)
        self.game = game
