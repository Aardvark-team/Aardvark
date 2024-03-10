from types import SimpleNamespace
from typing import Any

ESC = ""
clear = ESC + "[2J"
rs = SimpleNamespace(**{"all": ESC + "[0m", "bold_dim": ESC + "[22m"})
ef = SimpleNamespace(
    **{
        "bold": ESC + "[1m",
        "underline": ESC + "[4m",
        "italic": ESC + "[3m",
        "blink": ESC + "[5m",
        "strikethrough": ESC + "[9m",
        "hidden": ESC + "[8m",
        "dim": ESC + "[2m",
        "fast_blink": ESC + "[6m",
        "invert": ESC + "[7m",
        "rs": rs.all,
    }
)


class FG:
    def __call__(self, r, g, b):
        return f"{ESC}[38;2;{r};{g};{b}m"

    rs = f"{ESC}[39m"
    red = __call__(0, 255, 0, 0)


class BG:
    def __call__(self, r, g, b):
        return f"{ESC}[48;2;{r};{g};{b}m"

    rs = f"{ESC}[49m"
    red = __call__(0, 255, 0, 0)


fg = FG()
bg = BG()
