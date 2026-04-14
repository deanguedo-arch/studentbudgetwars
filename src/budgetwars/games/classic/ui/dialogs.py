from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from .panes import configure_dark_combobox_style
from .setup_dialog import _lookup_option, build_setup_summary_lines, compute_setup_dialog_geometry
from .theme import (
    ACCENT_RESOLVE,
    BG_CARD,
    BG_DARK,
    BG_DARKEST,
    BG_ELEVATED,
    BG_HOVER,
    BG_MID,
    BORDER,
    FONT_BODY,
    FONT_BUTTON,
    FONT_SMALL,
    FONT_SUBHEADING,
    PAD_L,
    PAD_M,
    PAD_S,
    TEXT_HEADING,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from .view_models import _SetupGroup


class SelectionDialog(simpledialog.Dialog):
    """Dark-themed selection dialog for choosing game options."""

    def __init__(self, parent: tk.Misc, title: str, prompt: str, options: list[tuple[str, str, str]]):
        self.prompt = prompt
        self.options = options
        self.result: str | None = None
        self._desc_var = tk.StringVar(value="")
        super().__init__(parent, title)

    def body(self, master: tk.Misc):
        master.configure(bg=BG_DARKEST)
        self.configure(bg=BG_DARKEST)

        tk.Label(
            master,
            text=self.prompt,
            justify="left",
            wraplength=540,
            font=FONT_SUBHEADING,
            bg=BG_DARKEST,
            fg=TEXT_HEADING,
        ).pack(anchor="w", padx=PAD_M, pady=(PAD_M, PAD_S))
        self.listbox = tk.Listbox(
            master,
            width=56,
            height=min(9, max(4, len(self.options))),
            font=FONT_BODY,
            bg=BG_ELEVATED,
            fg=TEXT_HEADING,
            selectbackground=ACCENT_RESOLVE,
            selectforeground=TEXT_HEADING,
            relief="flat",
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            activestyle="none",
            exportselection=False,
        )
        self.listbox.pack(fill="both", expand=True, padx=PAD_M, pady=PAD_S)
        for label, _, _ in self.options:
            self.listbox.insert("end", label)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        tk.Label(
            master,
            textvariable=self._desc_var,
            justify="left",
            anchor="w",
            wraplength=540,
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            relief="flat",
            bd=0,
            padx=PAD_M,
            pady=PAD_S,
            font=FONT_SMALL,
        ).pack(fill="x", padx=PAD_M, pady=(0, PAD_M))

        if self.options:
            self.listbox.selection_set(0)
            self._desc_var.set(self.options[0][2])
        return self.listbox

    def _on_select(self, _event=None) -> None:
        if self.listbox.curselection():
            self._desc_var.set(self.options[self.listbox.curselection()[0]][2])

    def apply(self):
        if self.listbox.curselection():
            self.result = self.options[self.listbox.curselection()[0]][1]

    def buttonbox(self):
        box = tk.Frame(self, bg=BG_DARKEST)
        ok_btn = tk.Button(
            box,
            text="OK",
            width=10,
            command=self.ok,
            default="active",
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            activebackground=BG_HOVER,
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        ok_btn.pack(side="left", padx=5, pady=PAD_M)
        cancel_btn = tk.Button(
            box,
            text="Cancel",
            width=10,
            command=self.cancel,
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            activebackground=BG_ELEVATED,
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        cancel_btn.pack(side="left", padx=5, pady=PAD_M)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()


class ClassicSetupDialog(simpledialog.Dialog):
    def __init__(
        self,
        parent: tk.Misc,
        bundle,
        *,
        initial_name: str = "Player",
        initial_preset_id: str | None = None,
        initial_city_id: str | None = None,
        initial_academic_level_id: str | None = None,
        initial_family_support_level_id: str | None = None,
        initial_savings_band_id: str | None = None,
        initial_opening_path_id: str | None = None,
        initial_difficulty_id: str | None = None,
    ):
        self.bundle = bundle
        self.result: dict[str, str] | None = None
        self.player_name_var = tk.StringVar(value=initial_name or "Player")
        self.summary_var = tk.StringVar(value="")
        self._group_selection_vars: dict[str, tk.StringVar] = {}
        self._group_desc_vars: dict[str, tk.StringVar] = {}
        self._group_buttons: dict[str, tk.Button] = {}
        self._value_maps: dict[str, dict[str, tuple[str, str, str]]] = {}
        self._groups = [
            _SetupGroup(
                "preset_id",
                "Preset",
                "Choose the background you are starting from:",
                [(item.name, item.id, item.description) for item in bundle.presets],
                initial_preset_id,
            ),
            _SetupGroup(
                "city_id",
                "City",
                "Choose the city you are trying to make work:",
                [(item.name, item.id, item.opportunity_text) for item in bundle.cities],
                initial_city_id,
            ),
            _SetupGroup(
                "academic_level_id",
                "Academics",
                "How strong is your academic footing?",
                [(item.name, item.id, item.description) for item in bundle.config.academic_levels],
                initial_academic_level_id,
            ),
            _SetupGroup(
                "family_support_level_id",
                "Family Support",
                "How much backup do you realistically have?",
                [(item.name, item.id, item.description) for item in bundle.config.family_support_levels],
                initial_family_support_level_id,
            ),
            _SetupGroup(
                "savings_band_id",
                "Starting Cushion",
                "How much cushion are you really starting with?",
                [(item.name, item.id, item.description) for item in bundle.config.savings_bands],
                initial_savings_band_id,
            ),
            _SetupGroup(
                "opening_path_id",
                "Opening Path",
                "Pick the lane you are stepping into first:",
                [(item.name, item.id, item.description) for item in bundle.config.opening_paths],
                initial_opening_path_id,
            ),
            _SetupGroup(
                "difficulty_id",
                "Difficulty",
                "Pick how hard the decade should hit back:",
                [(item.name, item.id, item.description) for item in bundle.difficulties],
                initial_difficulty_id,
            ),
        ]
        self._groups_by_key = {group.key: group for group in self._groups}
        super().__init__(parent, "Start New Run")

    def body(self, master: tk.Misc):
        master.configure(bg=BG_DARKEST)
        self.configure(bg=BG_DARKEST)
        self._combobox_style = configure_dark_combobox_style(self)
        self.transient(self.master)
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=5)
        master.columnconfigure(1, weight=4)

        left = tk.Frame(master, bg=BG_DARKEST)
        left.grid(row=0, column=0, sticky="nsew", padx=(PAD_M, PAD_M), pady=PAD_M)
        left.columnconfigure(0, weight=1)

        name_frame = tk.LabelFrame(
            left,
            text="Player Name",
            padx=PAD_M,
            pady=PAD_M,
            bg=BG_CARD,
            fg=TEXT_HEADING,
            font=FONT_SUBHEADING,
            bd=1,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        name_frame.grid(row=0, column=0, sticky="ew", pady=(0, PAD_M))
        self.name_entry = tk.Entry(
            name_frame,
            textvariable=self.player_name_var,
            font=FONT_BODY,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.name_entry.pack(fill="x")

        options_outer = tk.LabelFrame(
            left,
            text="Start Setup",
            padx=PAD_M,
            pady=PAD_M,
            bg=BG_CARD,
            fg=TEXT_HEADING,
            font=FONT_SUBHEADING,
            bd=1,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        options_outer.grid(row=1, column=0, sticky="nsew")
        options_outer.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        canvas = tk.Canvas(options_outer, bg=BG_CARD, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(options_outer, orient="vertical", command=canvas.yview)
        options_frame = tk.Frame(canvas, bg=BG_CARD)
        options_frame.columnconfigure(0, weight=1)

        options_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        options_window = canvas.create_window((0, 0), window=options_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(options_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row, group in enumerate(self._groups):
            option_map = {label: option for option in group.options for label in [option[0]]}
            self._value_maps[group.key] = option_map
            default_option = _lookup_option(group.options, group.initial_id)
            var = tk.StringVar(value=default_option[0])
            desc_var = tk.StringVar(value=default_option[2])
            self._group_selection_vars[group.key] = var
            self._group_desc_vars[group.key] = desc_var

            frame = tk.LabelFrame(
                options_frame,
                text=group.title,
                padx=PAD_M,
                pady=PAD_S,
                bg=BG_ELEVATED,
                fg=TEXT_HEADING,
                font=FONT_SMALL,
                bd=0,
                relief="flat",
            )
            frame.grid(row=row, column=0, sticky="ew", pady=3)
            frame.columnconfigure(0, weight=1)

            select_btn = tk.Button(
                frame,
                textvariable=var,
                command=lambda key=group.key: self.select_setup_group(key),
                bg=BG_MID,
                fg=TEXT_PRIMARY,
                activebackground=BG_HOVER,
                activeforeground=TEXT_HEADING,
                font=FONT_BODY,
                relief="flat",
                cursor="hand2",
                highlightbackground=BORDER,
                highlightthickness=1,
                anchor="w",
                padx=PAD_M,
                pady=PAD_S,
            )
            select_btn.grid(row=0, column=0, sticky="ew")
            self._group_buttons[group.key] = select_btn

            tk.Label(
                frame,
                text=group.prompt,
                justify="left",
                wraplength=400,
                fg=TEXT_SECONDARY,
                bg=BG_ELEVATED,
                font=("Segoe UI", 9, "bold"),
            ).grid(row=1, column=0, sticky="w", pady=(PAD_S, 0))
            tk.Label(
                frame,
                textvariable=desc_var,
                justify="left",
                wraplength=400,
                fg=TEXT_MUTED,
                bg=BG_ELEVATED,
                font=FONT_SMALL,
            ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        right = tk.LabelFrame(
            master,
            text="Opening Identity",
            padx=PAD_L,
            pady=PAD_L,
            bg=BG_CARD,
            fg=TEXT_HEADING,
            font=FONT_SUBHEADING,
            bd=1,
            relief="solid",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(0, PAD_M), pady=PAD_M)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.summary_text = tk.Text(
            right,
            width=1,
            height=1,
            wrap="word",
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            font=FONT_BODY,
            spacing1=2,
            spacing3=4,
            insertbackground=BG_ELEVATED,
        )
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_text.configure(state="disabled")

        self.update_idletasks()
        parent = self.master
        parent.update_idletasks()
        x, y, width, height = compute_setup_dialog_geometry(
            parent_x=parent.winfo_rootx(),
            parent_y=parent.winfo_rooty(),
            parent_width=max(1, parent.winfo_width()),
            parent_height=max(1, parent.winfo_height()),
            screen_width=self.winfo_screenwidth(),
            screen_height=self.winfo_screenheight(),
        )
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(860, width), min(600, height))

        self._refresh_summary()
        return self.name_entry

    def _current_option(self, key: str) -> tuple[str, str, str]:
        selected_label = self._group_selection_vars[key].get()
        return self._value_maps[key][selected_label]

    def _selected_ids(self) -> dict[str, str]:
        return {key: self._current_option(key)[1] for key in self._group_selection_vars}

    def select_setup_group(self, key: str) -> None:
        group = self._groups_by_key[key]
        choice = SelectionDialog(self, group.title, group.prompt, group.options).result
        if choice is None:
            return
        selected = next(option for option in group.options if option[1] == choice)
        self._group_selection_vars[key].set(selected[0])
        self._group_desc_vars[key].set(selected[2])
        self._group_buttons[key].configure(text=selected[0])
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        selections = self._selected_ids()
        summary_lines = build_setup_summary_lines(self.bundle, selections, self.player_name_var.get().strip())
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", "\n".join(summary_lines))
        self.summary_text.configure(state="disabled")

    def validate(self) -> bool:
        if not self.player_name_var.get().strip():
            messagebox.showerror("Player Name", "Please enter a player name.")
            return False
        return True

    def apply(self) -> None:
        self.result = {
            "player_name": self.player_name_var.get().strip() or "Player",
            **self._selected_ids(),
        }

    def buttonbox(self):
        box = tk.Frame(self, bg=BG_DARKEST)
        start = tk.Button(
            box,
            text="Start Run",
            width=14,
            command=self.ok,
            default="active",
            bg="#4a4520",
            fg=ACCENT_RESOLVE,
            activebackground="#5a5528",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            highlightbackground=ACCENT_RESOLVE,
            highlightthickness=2,
        )
        start.pack(side="left", padx=5, pady=PAD_M)
        cancel = tk.Button(
            box,
            text="Cancel",
            width=10,
            command=self.cancel,
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            activebackground=BG_ELEVATED,
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        cancel.pack(side="left", padx=5, pady=PAD_M)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()


def prompt_new_game_setup(
    parent: tk.Misc,
    bundle,
    *,
    initial_name: str = "Player",
    initial_preset_id: str | None = None,
    initial_city_id: str | None = None,
    initial_academic_level_id: str | None = None,
    initial_family_support_level_id: str | None = None,
    initial_savings_band_id: str | None = None,
    initial_opening_path_id: str | None = None,
    initial_difficulty_id: str | None = None,
) -> dict[str, str] | None:
    dialog = ClassicSetupDialog(
        parent,
        bundle,
        initial_name=initial_name,
        initial_preset_id=initial_preset_id,
        initial_city_id=initial_city_id,
        initial_academic_level_id=initial_academic_level_id,
        initial_family_support_level_id=initial_family_support_level_id,
        initial_savings_band_id=initial_savings_band_id,
        initial_opening_path_id=initial_opening_path_id,
        initial_difficulty_id=initial_difficulty_id,
    )
    return dialog.result
