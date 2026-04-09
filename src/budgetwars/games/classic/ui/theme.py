"""Classic UI design system — colors, fonts, and reusable widget factories."""
from __future__ import annotations

import tkinter as tk

# ── Background palette ──────────────────────────────────────────────
BG_DARKEST  = "#0b1016"
BG_DARK     = "#111923"
BG_MID      = "#182330"
BG_CARD     = "#1d2a38"
BG_ELEVATED = "#243446"
BG_HOVER    = "#2d4258"
BORDER      = "#4a6076"

# ── Text ─────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#f0eadb"
TEXT_SECONDARY = "#c8bca6"
TEXT_MUTED     = "#8f8a7a"
TEXT_HEADING   = "#fff7e7"

# ── System accent colors ────────────────────────────────────────────
ACCENT_CAREER    = "#d98f43"
ACCENT_EDUCATION = "#88b7d8"
ACCENT_HOUSING   = "#5ea87a"
ACCENT_TRANSPORT = "#6aa3b5"
ACCENT_BUDGET    = "#4fb39d"
ACCENT_WEALTH    = "#d9b55a"
ACCENT_FOCUS     = "#d97952"
ACCENT_RESOLVE   = "#f2ca7a"

# ── Score tier colors ────────────────────────────────────────────────
TIER_BRONZE = "#c48a4d"
TIER_SILVER = "#c1c7cf"
TIER_GOLD   = "#e2bf62"
TIER_ELITE  = "#86c3cf"

def tier_color(tier: str) -> str:
    return {
        "Bronze": TIER_BRONZE,
        "Silver": TIER_SILVER,
        "Gold": TIER_GOLD,
        "Elite": TIER_ELITE,
    }.get(tier, TEXT_SECONDARY)

# ── Stat colors ──────────────────────────────────────────────────────
COLOR_POSITIVE  = "#72c78c"
COLOR_NEGATIVE  = "#df7664"
COLOR_WARNING   = "#d9a85f"
COLOR_NEUTRAL   = "#7d96a8"
COLOR_STRESS    = "#df7664"
COLOR_ENERGY    = "#72c78c"
COLOR_LIFE      = "#8ab7cf"
COLOR_FAMILY    = "#b8996f"
COLOR_SOCIAL    = "#e0be76"
COLOR_MONEY_POS = "#72c78c"
COLOR_MONEY_NEG = "#df7664"

# ── Fonts ────────────────────────────────────────────────────────────
FONT_HEADING      = ("Georgia", 13, "bold")
FONT_HEADING_LG   = ("Georgia", 16, "bold")
FONT_SUBHEADING   = ("Georgia", 10, "bold")
FONT_BODY         = ("Trebuchet MS", 10)
FONT_BODY_LG      = ("Trebuchet MS", 12)
FONT_MONO         = ("Consolas", 10)
FONT_MONO_LG      = ("Consolas", 12)
FONT_SMALL        = ("Trebuchet MS", 9)
FONT_TINY         = ("Trebuchet MS", 8)
FONT_SCORE        = ("Georgia", 22, "bold")
FONT_SCORE_TIER   = ("Georgia", 12, "bold")
FONT_BUTTON       = ("Trebuchet MS", 10, "bold")
FONT_BUTTON_LG    = ("Trebuchet MS", 12, "bold")
FONT_RESOLVE      = ("Georgia", 14, "bold")
FONT_RESOLVE_LG   = ("Georgia", 16, "bold")

# ── Layout constants ─────────────────────────────────────────────────
PAD_S  = 4
PAD_M  = 8
PAD_L  = 12
PAD_XL = 16
CARD_BORDER_W = 3
CORNER_RADIUS = 0  # Tk doesn't support, but kept for reference


# ── Widget factories ─────────────────────────────────────────────────

def section_frame(parent: tk.Misc, title: str, accent: str = BORDER) -> tk.LabelFrame:
    """Styled dark section with colored title."""
    frame = tk.LabelFrame(
        parent,
        text=f"  {title}  ",
        bg=BG_CARD,
        fg=accent,
        font=FONT_SUBHEADING,
        bd=1,
        relief="solid",
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=PAD_M,
        pady=PAD_S,
    )
    return frame


def card_frame(parent: tk.Misc, accent: str = BORDER) -> tk.Frame:
    """A card-style frame with a colored left border accent."""
    outer = tk.Frame(parent, bg=accent, bd=0)
    inner = tk.Frame(outer, bg=BG_ELEVATED, bd=0)
    inner.pack(side="right", fill="both", expand=True, padx=(CARD_BORDER_W, 0))
    # Store inner reference for adding children
    outer._inner = inner  # type: ignore[attr-defined]
    return outer


def heading_label(parent: tk.Misc, text: str, **kwargs) -> tk.Label:
    defaults = dict(bg=BG_CARD, fg=TEXT_HEADING, font=FONT_HEADING, anchor="w")
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def body_label(parent: tk.Misc, text: str = "", **kwargs) -> tk.Label:
    defaults = dict(bg=BG_CARD, fg=TEXT_PRIMARY, font=FONT_BODY, anchor="w", justify="left")
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def muted_label(parent: tk.Misc, text: str = "", **kwargs) -> tk.Label:
    defaults = dict(bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left")
    defaults.update(kwargs)
    return tk.Label(parent, text=text, **defaults)


def stat_bar(
    parent: tk.Misc,
    value: int,
    max_value: int,
    color: str,
    width: int = 100,
    height: int = 10,
    bg: str = BG_DARK,
) -> tk.Canvas:
    """Simple colored progress bar."""
    canvas = tk.Canvas(parent, width=width, height=height, bg=bg, bd=0, highlightthickness=0)
    fill_w = max(0, min(width, int(width * (value / max(1, max_value)))))
    canvas.create_rectangle(0, 0, fill_w, height, fill=color, outline="")
    canvas.create_rectangle(fill_w, 0, width, height, fill=BG_DARK, outline="")
    return canvas


def money_str(value: int) -> str:
    return f"${value:,}"


def delta_str(value: int) -> str:
    if value > 0:
        return f"+${value:,}"
    elif value < 0:
        return f"-${abs(value):,}"
    return "$0"


def money_color(value: int) -> str:
    if value > 0:
        return COLOR_MONEY_POS
    elif value < 0:
        return COLOR_MONEY_NEG
    return TEXT_SECONDARY
