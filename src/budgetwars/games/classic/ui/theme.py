"""Classic UI design system — colors, fonts, and reusable widget factories."""
from __future__ import annotations

import tkinter as tk

# ── Background palette ──────────────────────────────────────────────
BG_DARKEST  = "#0e0e1a"
BG_DARK     = "#161625"
BG_MID      = "#1e1e32"
BG_CARD     = "#252540"
BG_ELEVATED = "#2d2d4a"
BG_HOVER    = "#363658"
BORDER      = "#3a3a5c"

# ── Text ─────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#e8e8f0"
TEXT_SECONDARY = "#a0a0b8"
TEXT_MUTED     = "#6e6e88"
TEXT_HEADING   = "#f0f0ff"

# ── System accent colors ────────────────────────────────────────────
ACCENT_CAREER    = "#f0a030"   # amber
ACCENT_EDUCATION = "#4ea8de"   # blue
ACCENT_HOUSING   = "#48b880"   # green
ACCENT_TRANSPORT = "#a86de4"   # purple
ACCENT_BUDGET    = "#38c8b0"   # teal
ACCENT_WEALTH    = "#e8c840"   # gold
ACCENT_FOCUS     = "#e87040"   # orange
ACCENT_RESOLVE   = "#ffd966"   # gold button

# ── Score tier colors ────────────────────────────────────────────────
TIER_BRONZE = "#cd7f32"
TIER_SILVER = "#a8b0b8"
TIER_GOLD   = "#f0c850"
TIER_ELITE  = "#60d0ff"

def tier_color(tier: str) -> str:
    return {
        "Bronze": TIER_BRONZE,
        "Silver": TIER_SILVER,
        "Gold": TIER_GOLD,
        "Elite": TIER_ELITE,
    }.get(tier, TEXT_SECONDARY)

# ── Stat colors ──────────────────────────────────────────────────────
COLOR_POSITIVE  = "#48d878"
COLOR_NEGATIVE  = "#e85050"
COLOR_WARNING   = "#f0a840"
COLOR_NEUTRAL   = "#6888a8"
COLOR_STRESS    = "#e85050"
COLOR_ENERGY    = "#48d878"
COLOR_LIFE      = "#60b0f0"
COLOR_FAMILY    = "#c888e0"
COLOR_SOCIAL    = "#f0c060"
COLOR_MONEY_POS = "#48d878"
COLOR_MONEY_NEG = "#e85050"

# ── Fonts ────────────────────────────────────────────────────────────
FONT_HEADING      = ("Segoe UI", 12, "bold")
FONT_HEADING_LG   = ("Segoe UI", 14, "bold")
FONT_SUBHEADING   = ("Segoe UI", 10, "bold")
FONT_BODY         = ("Segoe UI", 10)
FONT_BODY_LG      = ("Segoe UI", 12)
FONT_MONO         = ("Consolas", 10)
FONT_MONO_LG      = ("Consolas", 12)
FONT_SMALL        = ("Segoe UI", 9)
FONT_TINY         = ("Segoe UI", 8)
FONT_SCORE        = ("Segoe UI", 18, "bold")
FONT_SCORE_TIER   = ("Segoe UI", 11, "bold")
FONT_BUTTON       = ("Segoe UI", 10, "bold")
FONT_BUTTON_LG    = ("Segoe UI", 12, "bold")
FONT_RESOLVE      = ("Segoe UI", 13, "bold")
FONT_RESOLVE_LG   = ("Segoe UI", 15, "bold")

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
