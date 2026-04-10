"""Bottom action bar with accent-colored system buttons and prominent Resolve."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BG_HOVER, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_CAREER, ACCENT_EDUCATION, ACCENT_HOUSING, ACCENT_TRANSPORT,
    ACCENT_BUDGET, ACCENT_WEALTH, ACCENT_FOCUS, ACCENT_RESOLVE,
    FONT_BUTTON, FONT_BUTTON_LG, FONT_RESOLVE, FONT_RESOLVE_LG,
    PAD_S, PAD_M,
)

_SYSTEM_ACCENTS = {
    "career": ACCENT_CAREER,
    "education": ACCENT_EDUCATION,
    "housing": ACCENT_HOUSING,
    "transport": ACCENT_TRANSPORT,
    "budget": ACCENT_BUDGET,
    "wealth": ACCENT_WEALTH,
    "focus": ACCENT_FOCUS,
}


def _button_bg(label: str) -> str:
    """Get subtle background tint for a system button."""
    key = label.lower().replace(" ", "_")
    accent = _SYSTEM_ACCENTS.get(key)
    if accent:
        return BG_DARK
    return BG_ELEVATED


def _button_fg(label: str) -> str:
    key = label.lower().replace(" ", "_")
    return _SYSTEM_ACCENTS.get(key, TEXT_PRIMARY)


class ActionsPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._buttons: list[tk.Button] = []
        self._section_frames: list[tk.Frame] = []
        self._large_text_enabled = False

    def set_actions(self, actions: list[tuple[str, object]]) -> None:
        self.set_grouped_actions([("Actions", actions)])

    def set_grouped_actions(
        self,
        groups: list[tuple[str, list[tuple[str, object]]]],
        *,
        compact: bool = False,
    ) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        for frame in self._section_frames:
            frame.destroy()
        self._section_frames.clear()

        if compact:
            container = tk.Frame(self, bg=BG_CARD)
            container.pack(fill="x", padx=PAD_S, pady=(PAD_S // 2, PAD_S // 2))
            self._section_frames.append(container)
            for column, (section_title, actions) in enumerate(groups):
                section = tk.Frame(container, bg=BG_CARD)
                section.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else PAD_S, 0))
                container.grid_columnconfigure(column, weight=1, uniform="actions")

                tk.Label(
                    section,
                    text=section_title,
                    bg=BG_CARD,
                    fg=TEXT_HEADING,
                    font=FONT_BUTTON if self._large_text_enabled else FONT_BUTTON,
                    anchor="w",
                ).pack(fill="x", pady=(0, PAD_S // 2))

                buttons_frame = tk.Frame(section, bg=BG_CARD)
                buttons_frame.pack(fill="x")

                regular_actions = [a for a in actions if a[0].lower() != "resolve month"]
                resolve_action = next((a for a in actions if a[0].lower() == "resolve month"), None)

                for index, (label, callback) in enumerate(regular_actions):
                    accent = _button_fg(label)
                    font = FONT_BUTTON_LG if self._large_text_enabled else FONT_BUTTON
                    btn = tk.Button(
                        buttons_frame, text=label, command=callback,
                        bg=_button_bg(label), fg=accent,
                        activebackground=BG_HOVER, activeforeground=TEXT_HEADING,
                        relief="flat", bd=0, font=font,
                        padx=PAD_S, pady=max(1, PAD_S // 3),
                        cursor="hand2",
                        highlightbackground=accent, highlightthickness=2,
                        wraplength=118,
                    )
                    btn.grid(row=0, column=index, padx=2, pady=1, sticky="ew")
                    btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BG_HOVER))
                    btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=_button_bg(b.cget("text"))))
                    self._buttons.append(btn)

                if resolve_action:
                    label, callback = resolve_action
                    resolve_font = FONT_RESOLVE_LG if self._large_text_enabled else FONT_RESOLVE
                    resolve_btn = tk.Button(
                        buttons_frame, text=label, command=callback,
                        bg="#60451f", fg=ACCENT_RESOLVE,
                        activebackground="#75572a", activeforeground="#fff8d0",
                        relief="flat", bd=0, font=resolve_font,
                        pady=max(1, PAD_S // 3), padx=PAD_S,
                        cursor="hand2",
                        highlightbackground=ACCENT_RESOLVE, highlightthickness=2,
                    )
                    resolve_btn.grid(
                        row=0,
                        column=len(regular_actions),
                        padx=2,
                        pady=1,
                        sticky="ew",
                    )
                    resolve_btn.bind("<Enter>", lambda e: resolve_btn.configure(bg="#75572a"))
                    resolve_btn.bind("<Leave>", lambda e: resolve_btn.configure(bg="#60451f"))
                    self._buttons.append(resolve_btn)

                group_columns = len(regular_actions) + (1 if resolve_action else 0)
                for i in range(max(1, group_columns)):
                    buttons_frame.grid_columnconfigure(i, weight=1)
            return

        container = tk.Frame(self, bg=BG_CARD)
        container.pack(fill="x", padx=PAD_S, pady=(PAD_S, PAD_S))
        self._section_frames.append(container)

        for column, (section_title, actions) in enumerate(groups):
            section = tk.Frame(container, bg=BG_CARD)
            section.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else PAD_S, 0))
            container.grid_columnconfigure(column, weight=1, uniform="action_sections")

            tk.Label(
                section,
                text=section_title,
                bg=BG_CARD,
                fg=TEXT_HEADING,
                font=FONT_BUTTON_LG if self._large_text_enabled else FONT_BUTTON,
                anchor="w",
            ).pack(fill="x", pady=(0, PAD_S // 2))

            buttons_frame = tk.Frame(section, bg=BG_CARD)
            buttons_frame.pack(fill="x")

            regular_actions = [a for a in actions if a[0].lower() != "resolve month"]
            resolve_action = next((a for a in actions if a[0].lower() == "resolve month"), None)
            group_columns = max(1, len(regular_actions))

            for index, (label, callback) in enumerate(regular_actions):
                accent = _button_fg(label)
                font = FONT_BUTTON_LG if self._large_text_enabled else FONT_BUTTON
                btn = tk.Button(
                    buttons_frame, text=label, command=callback,
                    bg=_button_bg(label), fg=accent,
                    activebackground=BG_HOVER, activeforeground=TEXT_HEADING,
                    relief="flat", bd=0, font=font,
                    padx=PAD_M, pady=PAD_S,
                    cursor="hand2",
                    highlightbackground=accent, highlightthickness=2,
                    wraplength=160,
                )
                btn.grid(row=0, column=index, padx=3, pady=3, sticky="ew")
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BG_HOVER))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=_button_bg(b.cget("text"))))
                self._buttons.append(btn)

            if resolve_action:
                label, callback = resolve_action
                resolve_font = FONT_RESOLVE_LG if self._large_text_enabled else FONT_RESOLVE
                resolve_btn = tk.Button(
                    buttons_frame, text=label, command=callback,
                    bg="#60451f", fg=ACCENT_RESOLVE,
                    activebackground="#75572a", activeforeground="#fff8d0",
                    relief="flat", bd=0, font=resolve_font,
                    pady=PAD_S, cursor="hand2",
                    highlightbackground=ACCENT_RESOLVE, highlightthickness=2,
                )
                resolve_btn.grid(row=0, column=max(0, len(regular_actions)), padx=3, pady=3, sticky="ew")
                resolve_btn.bind("<Enter>", lambda e: resolve_btn.configure(bg="#75572a"))
                resolve_btn.bind("<Leave>", lambda e: resolve_btn.configure(bg="#60451f"))
                self._buttons.append(resolve_btn)
                group_columns += 1

            for i in range(group_columns):
                buttons_frame.grid_columnconfigure(i, weight=1)

    def set_large_text(self, enabled: bool) -> None:
        self._large_text_enabled = enabled
        for btn in self._buttons:
            if btn.cget("text").lower() == "resolve month":
                btn.configure(font=FONT_RESOLVE_LG if enabled else FONT_RESOLVE)
            else:
                btn.configure(font=FONT_BUTTON_LG if enabled else FONT_BUTTON)
