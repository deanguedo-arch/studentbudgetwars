"""Center column — color-coded month log."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING,
    FONT_SUBHEADING, FONT_BODY, FONT_SMALL, FONT_MONO,
    PAD_S, PAD_M,
)

_POSITIVE_KEYWORDS = {"income", "promotion", "scholarship", "saved", "earned", "opened", "landed", "passed"}
_NEGATIVE_KEYWORDS = {"debt", "stress", "burnout", "lost", "failed", "collapsed", "dried", "broke", "ugly", "hit"}
_NEUTRAL_KEYWORDS = {"month", "year", "focus", "changed", "set"}


def _line_color(line: str) -> str:
    lower = line.lower()
    if any(kw in lower for kw in _POSITIVE_KEYWORDS):
        return COLOR_POSITIVE
    if any(kw in lower for kw in _NEGATIVE_KEYWORDS):
        return COLOR_NEGATIVE
    return TEXT_SECONDARY


class LogPanel(tk.Frame):
    def __init__(self, master: tk.Misc, title: str = "Run Feedback"):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False

        header = tk.Label(self, text=f"  {title}  ", bg=BG_CARD, fg=TEXT_HEADING,
                          font=FONT_SUBHEADING, anchor="w")
        header.pack(fill="x", padx=PAD_S, pady=(PAD_S, 2))

        self.text = tk.Text(
            self, height=1, wrap="word",
            bg=BG_ELEVATED, fg=TEXT_PRIMARY,
            relief="flat", bd=0,
            font=FONT_MONO,
            spacing1=1, spacing3=2,
            takefocus=0,
            insertbackground=BG_ELEVATED,
            selectbackground=BG_DARK,
        )
        text_wrap = tk.Frame(self, bg=BG_CARD)
        text_wrap.pack(fill="both", expand=True, padx=PAD_S, pady=(0, PAD_S))
        self._scrollbar = tk.Scrollbar(text_wrap, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self._scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
        self.text.configure(state="disabled")

        # Configure color tags
        self.text.tag_configure("positive", foreground=COLOR_POSITIVE)
        self.text.tag_configure("negative", foreground=COLOR_NEGATIVE)
        self.text.tag_configure("neutral", foreground=TEXT_SECONDARY)
        self.text.tag_configure("latest", foreground=TEXT_HEADING, font=("Consolas", 10, "bold"))

    def render(self, messages: list[str], limit: int = 10) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        visible = messages[-limit:]
        for i, msg in enumerate(visible):
            lower = msg.lower()
            if lower.startswith("big win:") or lower.startswith("big hit:") or lower.startswith("score change:") or lower.startswith("new threat:") or lower.startswith("next best move:"):
                tag = "latest"
            elif i == len(visible) - 1:
                tag = "latest"
            elif any(kw in lower for kw in _POSITIVE_KEYWORDS):
                tag = "positive"
            elif any(kw in lower for kw in _NEGATIVE_KEYWORDS):
                tag = "negative"
            else:
                tag = "neutral"
            self.text.insert("end", msg + "\n", tag)
        self.text.configure(state="disabled")
        self.text.see("end")
        self._update_scrollbar_visibility()

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
        font = ("Consolas", 12) if enabled else FONT_MONO
        self.text.configure(font=font)

    def _update_scrollbar_visibility(self) -> None:
        first, last = self.text.yview()
        if (last - first) < 0.999:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="right", fill="y")
        else:
            if self._scrollbar.winfo_ismapped():
                self._scrollbar.pack_forget()
