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
    red = f"{ESC}[31m"
    blue = f"{ESC}[34m"
    green = f"{ESC}[32m"
    yellow = f"{ESC}[33m"
    magenta = f"{ESC}[35m"
    cyan = f"{ESC}[36m"
    white = f"{ESC}[37m"
    black = f"{ESC}[30m"


class BG:
    def __call__(self, r, g, b):
        return f"{ESC}[48;2;{r};{g};{b}m"

    rs = f"{ESC}[49m"
    red = f"{ESC}[41m"
    blue = f"{ESC}[44m"
    green = f"{ESC}[42m"
    yellow = f"{ESC}[43m"
    magenta = f"{ESC}[45m"
    cyan = f"{ESC}[46m"
    white = f"{ESC}[47m"
    black = f"{ESC}[40m"


fg = FG()
bg = BG()
