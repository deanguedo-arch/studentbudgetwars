from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD,
    BG_DARK,
    BG_DARKEST,
    BG_ELEVATED,
    BORDER,
    TEXT_HEADING,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    COLOR_POSITIVE,
    COLOR_WARNING,
    FONT_HEADING,
    FONT_SUBHEADING,
    FONT_BODY,
    FONT_SMALL,
    FONT_MONO,
    PAD_S,
    PAD_M,
    PAD_L,
)


class LearnDrawer(tk.Toplevel):
    def __init__(self, parent: tk.Misc, on_close=None):
        super().__init__(parent)
        self._on_close = on_close
        self._topic_ids: list[str] = []
        self._topics_by_id: dict[str, object] = {}
        self._selected_topic_id: str | None = None

        self.title("Learn")
        self.configure(bg=BG_DARKEST)
        self.geometry("900x640")
        self.minsize(760, 520)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())

        shell = tk.Frame(self, bg=BG_DARKEST, padx=PAD_M, pady=PAD_M)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=BG_DARKEST)
        header.pack(fill="x", pady=(0, PAD_S))
        tk.Label(header, text="Learn", bg=BG_DARKEST, fg=TEXT_HEADING, font=FONT_HEADING).pack(side="left")
        tk.Label(
            header,
            text="How to change stats, what causes pressure, and what each system does.",
            bg=BG_DARKEST,
            fg=TEXT_SECONDARY,
            font=FONT_BODY,
        ).pack(side="left", padx=PAD_M)

        body = tk.Frame(shell, bg=BG_DARKEST)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1, minsize=230)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_S))
        right = tk.Frame(body, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(left, text="Topics", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING, anchor="w").pack(
            fill="x", padx=PAD_M, pady=(PAD_M, PAD_S)
        )
        self._topic_list = tk.Listbox(
            left,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            selectbackground=COLOR_POSITIVE,
            selectforeground=BG_DARKEST,
            font=FONT_BODY,
            relief="flat",
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            exportselection=False,
            activestyle="none",
        )
        self._topic_list.pack(fill="both", expand=True, padx=PAD_M, pady=(0, PAD_S))
        self._topic_list.bind("<<ListboxSelect>>", self._on_topic_select)

        self._close_button = tk.Button(
            left,
            text="Close",
            command=self.close,
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            activebackground=BG_ELEVATED,
            font=FONT_BODY,
            relief="flat",
            bd=0,
            padx=PAD_L,
            pady=PAD_S,
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self._close_button.pack(fill="x", padx=PAD_M, pady=(0, PAD_M))

        self._pressure_family = tk.Label(right, text="", bg=BG_CARD, fg=COLOR_WARNING, font=FONT_SUBHEADING, anchor="w")
        self._pressure_family.pack(fill="x", padx=PAD_M, pady=(PAD_M, 0))
        self._credit_line = tk.Label(right, text="", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_BODY, anchor="w")
        self._credit_line.pack(fill="x", padx=PAD_M, pady=(PAD_S, 0))
        self._stress_line = tk.Label(right, text="", bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w")
        self._stress_line.pack(fill="x", padx=PAD_M, pady=(0, PAD_S))

        self._pressure_sources_frame = tk.Frame(right, bg=BG_CARD)
        self._pressure_sources_frame.pack(fill="x", padx=PAD_M, pady=(0, PAD_S))

        self._detail = tk.Text(
            right,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            font=FONT_MONO,
            wrap="word",
            spacing1=2,
            spacing3=3,
            takefocus=0,
            insertbackground=BG_ELEVATED,
            selectbackground=BG_DARK,
        )
        self._detail.pack(fill="both", expand=True, padx=PAD_M, pady=(0, PAD_M))
        self._detail.configure(state="disabled")
        self._detail.tag_configure("title", foreground=TEXT_HEADING, font=FONT_HEADING)
        self._detail.tag_configure("section", foreground=COLOR_WARNING, font=FONT_SUBHEADING)
        self._detail.tag_configure("body", foreground=TEXT_PRIMARY, font=FONT_BODY)
        self._detail.tag_configure("bullet", foreground=TEXT_SECONDARY, font=FONT_BODY)
        self._detail.tag_configure("muted", foreground=TEXT_MUTED, font=FONT_SMALL)

    def close(self) -> None:
        if self._on_close is not None:
            self._on_close()
        self.destroy()

    def render(self, vm, *, selected_topic_id: str | None = None) -> None:
        topics = list(vm.topics)
        topic_ids = [topic.id for topic in topics]
        if topic_ids != self._topic_ids:
            self._topic_ids = topic_ids
            self._topics_by_id = {topic.id: topic for topic in topics}
            self._topic_list.delete(0, "end")
            for topic in topics:
                self._topic_list.insert("end", topic.title)
        else:
            self._topics_by_id = {topic.id: topic for topic in topics}

        self._pressure_family.configure(text=f"Pressure family: {vm.active_pressure_family}")
        self._credit_line.configure(text=vm.credit_line)
        self._stress_line.configure(text=vm.stress_line)
        self._render_pressure_sources(vm.pressure_sources)

        topic_id = selected_topic_id or self._selected_topic_id or (topics[0].id if topics else None)
        if topic_id in self._topics_by_id:
            self._selected_topic_id = topic_id
            index = self._topic_ids.index(topic_id)
            self._topic_list.selection_clear(0, "end")
            self._topic_list.selection_set(index)
            self._topic_list.see(index)
            self._render_topic(self._topics_by_id[topic_id])
        elif topics:
            self._selected_topic_id = topics[0].id
            self._topic_list.selection_clear(0, "end")
            self._topic_list.selection_set(0)
            self._topic_list.see(0)
            self._render_topic(topics[0])

    def _render_pressure_sources(self, sources: list[str]) -> None:
        for child in self._pressure_sources_frame.winfo_children():
            child.destroy()
        if not sources:
            tk.Label(
                self._pressure_sources_frame,
                text="No active pressure sources to flag.",
                bg=BG_CARD,
                fg=TEXT_MUTED,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x")
            return
        for line in sources[:4]:
            tk.Label(
                self._pressure_sources_frame,
                text=line,
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=560,
            ).pack(fill="x", pady=1)

    def _render_topic(self, topic) -> None:
        self._detail.configure(state="normal")
        self._detail.delete("1.0", "end")
        self._detail.insert("end", f"{topic.title}\n", "title")
        self._detail.insert("end", f"{topic.what_it_is}\n\n", "body")
        self._detail.insert("end", "How to raise\n", "section")
        for item in topic.how_to_raise or ["No explicit raise rule is listed yet."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        self._detail.insert("end", "\nHow to lower\n", "section")
        for item in topic.how_to_lower or ["No explicit lower rule is listed yet."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        self._detail.insert("end", "\nWhy it matters\n", "section")
        for item in topic.why_it_matters or ["This stat influences future choices and pressure."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        if topic.common_drivers:
            self._detail.insert("end", "\nCommon drivers\n", "section")
            self._detail.insert("end", f"{', '.join(topic.common_drivers)}\n", "muted")
        if topic.related_situation_families:
            self._detail.insert("end", "\nSituation families\n", "section")
            self._detail.insert("end", f"{', '.join(topic.related_situation_families)}\n", "muted")
        self._detail.configure(state="disabled")

    def _on_topic_select(self, _event=None) -> None:
        if not self._topic_list.curselection():
            return
        index = self._topic_list.curselection()[0]
        if 0 <= index < len(self._topic_ids):
            topic_id = self._topic_ids[index]
            self._selected_topic_id = topic_id
            topic = self._topics_by_id.get(topic_id)
            if topic is not None:
                self._render_topic(topic)


class LearnPanel(tk.Frame):
    def __init__(self, master: tk.Misc, title: str = "Learn", on_close=None):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        self._on_close = on_close
        self._topic_ids: list[str] = []
        self._topics_by_id: dict[str, object] = {}
        self._selected_topic_id: str | None = None
        self._large = False

        header = tk.Frame(self, bg=BG_CARD)
        header.pack(fill="x", padx=PAD_M, pady=(PAD_M, PAD_S))
        tk.Label(header, text=title, bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING, anchor="w").pack(
            side="left"
        )
        tk.Button(
            header,
            text="Hide",
            command=self.close,
            bg=BG_DARK,
            fg=TEXT_SECONDARY,
            activebackground=BG_ELEVATED,
            font=FONT_SMALL,
            relief="flat",
            bd=0,
            padx=PAD_S,
            pady=2,
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        ).pack(side="right")

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=PAD_M, pady=(0, PAD_M))
        body.columnconfigure(0, weight=1, minsize=210)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG_CARD)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_S))
        right = tk.Frame(body, bg=BG_CARD)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(left, text="Topics", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING, anchor="w").pack(
            fill="x", pady=(0, PAD_S)
        )
        self._topic_list = tk.Listbox(
            left,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            selectbackground=COLOR_POSITIVE,
            selectforeground=BG_DARKEST,
            font=FONT_BODY,
            relief="flat",
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            exportselection=False,
            activestyle="none",
        )
        self._topic_list.pack(fill="both", expand=True)
        self._topic_list.bind("<<ListboxSelect>>", self._on_topic_select)

        self._pressure_family = tk.Label(right, text="", bg=BG_CARD, fg=COLOR_WARNING, font=FONT_SUBHEADING, anchor="w")
        self._pressure_family.pack(fill="x")
        self._credit_line = tk.Label(right, text="", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_BODY, anchor="w")
        self._credit_line.pack(fill="x", pady=(PAD_S, 0))
        self._stress_line = tk.Label(right, text="", bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w")
        self._stress_line.pack(fill="x", pady=(0, PAD_S))

        self._pressure_sources_frame = tk.Frame(right, bg=BG_CARD)
        self._pressure_sources_frame.pack(fill="x", pady=(0, PAD_S))

        self._detail = tk.Text(
            right,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            font=FONT_MONO,
            wrap="word",
            spacing1=2,
            spacing3=3,
            takefocus=0,
            insertbackground=BG_ELEVATED,
            selectbackground=BG_DARK,
        )
        self._detail.pack(fill="both", expand=True)
        self._detail.configure(state="disabled")
        self._detail.tag_configure("title", foreground=TEXT_HEADING, font=FONT_HEADING)
        self._detail.tag_configure("section", foreground=COLOR_WARNING, font=FONT_SUBHEADING)
        self._detail.tag_configure("body", foreground=TEXT_PRIMARY, font=FONT_BODY)
        self._detail.tag_configure("bullet", foreground=TEXT_SECONDARY, font=FONT_BODY)
        self._detail.tag_configure("muted", foreground=TEXT_MUTED, font=FONT_SMALL)

    def close(self) -> None:
        if self._on_close is not None:
            self._on_close()

    def render_drawer(self, vm, *, selected_topic_id: str | None = None) -> None:
        self.render(vm, selected_topic_id=selected_topic_id)

    def render(self, vm, *, selected_topic_id: str | None = None) -> None:
        topics = list(vm.topics)
        topic_ids = [topic.id for topic in topics]
        if topic_ids != self._topic_ids:
            self._topic_ids = topic_ids
            self._topics_by_id = {topic.id: topic for topic in topics}
            self._topic_list.delete(0, "end")
            for topic in topics:
                self._topic_list.insert("end", topic.title)
        else:
            self._topics_by_id = {topic.id: topic for topic in topics}

        self._pressure_family.configure(text=f"Pressure family: {vm.active_pressure_family}")
        self._credit_line.configure(text=vm.credit_line)
        self._stress_line.configure(text=vm.stress_line)
        self._render_pressure_sources(vm.pressure_sources)

        topic_id = selected_topic_id or self._selected_topic_id or (topics[0].id if topics else None)
        if topic_id in self._topics_by_id:
            self._selected_topic_id = topic_id
            index = self._topic_ids.index(topic_id)
            self._topic_list.selection_clear(0, "end")
            self._topic_list.selection_set(index)
            self._topic_list.see(index)
            self._render_topic(self._topics_by_id[topic_id])
        elif topics:
            self._selected_topic_id = topics[0].id
            self._topic_list.selection_clear(0, "end")
            self._topic_list.selection_set(0)
            self._topic_list.see(0)
            self._render_topic(topics[0])

    def _render_pressure_sources(self, sources: list[str]) -> None:
        for child in self._pressure_sources_frame.winfo_children():
            child.destroy()
        if not sources:
            tk.Label(
                self._pressure_sources_frame,
                text="No active pressure sources to flag.",
                bg=BG_CARD,
                fg=TEXT_MUTED,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x")
            return
        for line in sources[:4]:
            tk.Label(
                self._pressure_sources_frame,
                text=line,
                bg=BG_CARD,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=560,
            ).pack(fill="x", pady=1)

    def _render_topic(self, topic) -> None:
        detail_font = ("Consolas", 11) if self._large else FONT_MONO
        self._detail.configure(font=detail_font)
        self._detail.configure(state="normal")
        self._detail.delete("1.0", "end")
        self._detail.insert("end", f"{topic.title}\n", "title")
        self._detail.insert("end", f"{topic.what_it_is}\n\n", "body")
        self._detail.insert("end", "How to raise\n", "section")
        for item in topic.how_to_raise or ["No explicit raise rule is listed yet."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        self._detail.insert("end", "\nHow to lower\n", "section")
        for item in topic.how_to_lower or ["No explicit lower rule is listed yet."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        self._detail.insert("end", "\nWhy it matters\n", "section")
        for item in topic.why_it_matters or ["This stat influences future choices and pressure."]:
            self._detail.insert("end", f"• {item}\n", "bullet")
        if topic.common_drivers:
            self._detail.insert("end", "\nCommon drivers\n", "section")
            self._detail.insert("end", f"{', '.join(topic.common_drivers)}\n", "muted")
        if topic.related_situation_families:
            self._detail.insert("end", "\nSituation families\n", "section")
            self._detail.insert("end", f"{', '.join(topic.related_situation_families)}\n", "muted")
        self._detail.configure(state="disabled")

    def _on_topic_select(self, _event=None) -> None:
        if not self._topic_list.curselection():
            return
        index = self._topic_list.curselection()[0]
        if 0 <= index < len(self._topic_ids):
            topic_id = self._topic_ids[index]
            self._selected_topic_id = topic_id
            topic = self._topics_by_id.get(topic_id)
            if topic is not None:
                self._render_topic(topic)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
        font = ("Consolas", 12) if enabled else FONT_MONO
        self._topic_list.configure(font=FONT_BODY if not enabled else ("Segoe UI", 12))
        self._credit_line.configure(font=("Segoe UI", 12, "bold") if enabled else FONT_BODY)
        self._stress_line.configure(font=("Segoe UI", 10) if enabled else FONT_SMALL)
        self._detail.configure(font=font)
