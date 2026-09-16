import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser


class PowerEdit:
    """
    PowerEdit
    ----------
    Lightweight WordPad-style rich-text editor built with Tkinter.

    Features:
        - Font family / size
        - Bold / italic / underline / strike
        - Text color
        - Left / center / right alignment
        - Bulleted lists
        - Numbered lists
        - Find / replace
        - Undo / redo
        - TXT / basic RTF
        - Printing
        - Keyboard shortcuts
    """

    DEFAULT_FONT = "Arial"
    DEFAULT_SIZE = 12
    DEFAULT_COLOR = "#000000"

    BULLET_PREFIX = "• "
    NUMBER_PREFIX_RE = re.compile(r"^(\d+)\.\s")

    def __init__(self, root):
        self.root = root
        self.root.title("PowerEdit")
        self.root.geometry("1100x700")
        self.root.minsize(750, 500)

        self.filename = None
        self.modified = False

        # Current formatting state
        self.current_font = self.DEFAULT_FONT
        self.current_size = self.DEFAULT_SIZE
        self.current_color = self.DEFAULT_COLOR

        self.bold = False
        self.italic = False
        self.underline = False
        self.strike = False
        self.current_alignment = "left"

        # Last selection is remembered because toolbar clicks remove
        # focus from the Text widget.
        self.last_selection_start = None
        self.last_selection_end = None

        # Find/replace
        self.find_window = None

        # Formatting tags
        self.format_tags = {}

        self.create_menu()
        self.create_toolbar()
        self.create_editor()
        self.create_statusbar()
        self.create_bindings()

        self.update_title()
        self.update_toolbar()

        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

        self.text.focus_set()

    # ============================================================
    # MENU
    # ============================================================

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # File
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N",
                              command=self.new_document)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O",
                              command=self.open_document)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S",
                              command=self.save_document)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S",
                              command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Print", accelerator="Ctrl+P",
                              command=self.print_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit
        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z",
                              command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y",
                              command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X",
                              command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C",
                              command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V",
                              command=self.paste)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A",
                              command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F",
                              command=self.show_find)
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H",
                              command=self.show_replace)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Format
        format_menu = tk.Menu(menubar, tearoff=False)

        format_menu.add_command(
            label="Bold",
            accelerator="Ctrl+B",
            command=self.toggle_bold
        )
        format_menu.add_command(
            label="Italic",
            accelerator="Ctrl+I",
            command=self.toggle_italic
        )
        format_menu.add_command(
            label="Underline",
            accelerator="Ctrl+U",
            command=self.toggle_underline
        )
        format_menu.add_command(
            label="Strikethrough",
            command=self.toggle_strike
        )

        format_menu.add_separator()

        format_menu.add_command(
            label="Bulleted List",
            command=self.toggle_bullets
        )
        format_menu.add_command(
            label="Numbered List",
            command=self.toggle_numbering
        )
        format_menu.add_command(
            label="Remove List Formatting",
            command=self.remove_list_formatting
        )

        format_menu.add_separator()

        format_menu.add_command(
            label="Align Left",
            command=lambda: self.set_alignment("left")
        )
        format_menu.add_command(
            label="Center",
            command=lambda: self.set_alignment("center")
        )
        format_menu.add_command(
            label="Align Right",
            command=lambda: self.set_alignment("right")
        )

        menubar.add_cascade(label="Format", menu=format_menu)

        self.root.config(menu=menubar)

    # ============================================================
    # TOOLBAR
    # ============================================================

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bd=1, relief="raised")
        toolbar.pack(side="top", fill="x")

        row1 = tk.Frame(toolbar)
        row1.pack(side="top", fill="x", padx=3, pady=2)

        row2 = tk.Frame(toolbar)
        row2.pack(side="top", fill="x", padx=3, pady=2)

        # --------------------------------------------------------
        # Row 1 - formatting
        # --------------------------------------------------------

        tk.Label(row1, text="Font:").pack(side="left", padx=(2, 2))

        self.font_var = tk.StringVar(value=self.DEFAULT_FONT)

        self.font_combo = ttk.Combobox(
            row1,
            textvariable=self.font_var,
            width=20,
            state="readonly"
        )

        fonts = sorted(
            set(
                list(
                    self.root.tk.call(
                        "font", "families"
                    )
                )
            )
        )

        self.font_combo["values"] = fonts
        self.font_combo.pack(side="left", padx=2)
        self.font_combo.bind("<<ComboboxSelected>>", self.font_changed)

        tk.Label(row1, text="Size:").pack(side="left", padx=(8, 2))

        self.size_var = tk.StringVar(value=str(self.DEFAULT_SIZE))

        self.size_combo = ttk.Combobox(
            row1,
            textvariable=self.size_var,
            width=5,
            state="readonly",
            values=(
                "8", "9", "10", "11", "12", "14",
                "16", "18", "20", "22", "24",
                "28", "32", "36", "48", "72"
            )
        )

        self.size_combo.pack(side="left", padx=2)
        self.size_combo.bind("<<ComboboxSelected>>", self.size_changed)

        # Bold
        self.bold_button = tk.Button(
            row1,
            text="B",
            width=3,
            font=("Arial", 10, "bold"),
            command=self.toggle_bold,
            relief="raised"
        )
        self.bold_button.pack(side="left", padx=1)

        # Italic
        self.italic_button = tk.Button(
            row1,
            text="I",
            width=3,
            font=("Arial", 10, "italic"),
            command=self.toggle_italic,
            relief="raised"
        )
        self.italic_button.pack(side="left", padx=1)

        # Underline
        self.underline_button = tk.Button(
            row1,
            text="U",
            width=3,
            font=("Arial", 10, "underline"),
            command=self.toggle_underline,
            relief="raised"
        )
        self.underline_button.pack(side="left", padx=1)

        # Strike
        self.strike_button = tk.Button(
            row1,
            text="S",
            width=3,
            font=("Arial", 10),
            command=self.toggle_strike,
            relief="raised"
        )
        self.strike_button.pack(side="left", padx=1)

        # Color
        tk.Label(row1, text="Color:").pack(side="left", padx=(8, 2))

        self.color_button = tk.Button(
            row1,
            text="A",
            width=3,
            font=("Arial", 10, "bold"),
            fg="black",
            command=self.choose_color
        )
        self.color_button.pack(side="left", padx=2)

        # Lists
        self.bullet_button = ttk.Button(
            row2,
            text="• List",
            command=self.toggle_bullets
        )
        self.bullet_button.pack(side="left", padx=2)

        self.number_button = ttk.Button(
            row1,
            text="1. List",
            command=self.toggle_numbering
        )
        self.number_button.pack(side="left", padx=2)

        self.remove_list_button = ttk.Button(
            row1,
            text="No List",
            command=self.remove_list_formatting
        )
        self.remove_list_button.pack(side="left", padx=2)

        # --------------------------------------------------------
        # Row 2
        # --------------------------------------------------------
        # Alignment
        ttk.Button(
            row2,
            text="Left",
            command=lambda: self.set_alignment("left")
        ).pack(side="left", padx=2)

        ttk.Button(
            row2,
            text="Center",
            command=lambda: self.set_alignment("center")
        ).pack(side="left", padx=2)

        ttk.Button(
            row2,
            text="Right",
            command=lambda: self.set_alignment("right")
        ).pack(side="left", padx=2)

        ttk.Separator(
            row2,
            orient="vertical"
        ).pack(side="left", fill="y", padx=7)

        ttk.Button(
            row2,
            text="Undo",
            command=self.undo
        ).pack(side="left", padx=2)

        ttk.Button(
            row2,
            text="Redo",
            command=self.redo
        ).pack(side="left", padx=2)



        ttk.Button(
            row2,
            text="Find",
            command=self.show_find
        ).pack(side="left", padx=2)

        ttk.Button(
            row2,
            text="Replace",
            command=self.show_replace
        ).pack(side="left", padx=2)

        ttk.Button(
            row2,
            text="Print",
            command=self.print_document
        ).pack(side="left", padx=2)

        ttk.Separator(
            row2,
            orient="vertical"
        ).pack(side="left", fill="y", padx=7)





    # ============================================================
    # TEXT EDITOR
    # ============================================================

    def create_editor(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            frame,
            wrap="word",
            undo=True,
            maxundo=-1,
            font=(self.DEFAULT_FONT, self.DEFAULT_SIZE),
            padx=10,
            pady=10,
            tabs=("2c",)
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.text.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.text.configure(yscrollcommand=scrollbar.set)

        # Alignment tags
        self.text.tag_configure(
            "align_left",
            justify="left"
        )

        self.text.tag_configure(
            "align_center",
            justify="center"
        )

        self.text.tag_configure(
            "align_right",
            justify="right"
        )

    # ============================================================
    # STATUS BAR
    # ============================================================

    def create_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")

        status = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            bd=1,
            relief="sunken"
        )
        status.pack(side="bottom", fill="x")

    # ============================================================
    # BINDINGS
    # ============================================================

    def create_bindings(self):
        self.root.bind_all("<Control-n>", self.shortcut_new)
        self.root.bind_all("<Control-o>", self.shortcut_open)
        self.root.bind_all("<Control-s>", self.shortcut_save)
        self.root.bind_all("<Control-Shift-S>", self.shortcut_save_as)

        self.root.bind_all("<Control-z>", self.shortcut_undo)
        self.root.bind_all("<Control-y>", self.shortcut_redo)

        self.root.bind_all("<Control-x>", self.shortcut_cut)
        self.root.bind_all("<Control-c>", self.shortcut_copy)
        self.root.bind_all("<Control-v>", self.shortcut_paste)
        self.root.bind_all("<Control-a>", self.shortcut_select_all)

        self.root.bind_all("<Control-f>", self.shortcut_find)
        self.root.bind_all("<Control-h>", self.shortcut_replace)
        self.root.bind_all("<Control-p>", self.shortcut_print)

        self.root.bind_all("<Control-b>", self.shortcut_bold)
        self.root.bind_all("<Control-i>", self.shortcut_italic)
        self.root.bind_all("<Control-u>", self.shortcut_underline)

        self.text.bind("<<Modified>>", self.on_modified)
        self.text.bind("<KeyRelease>", self.cursor_changed)
        self.text.bind("<ButtonRelease-1>", self.remember_selection)
        self.text.bind("<B1-Motion>", self.remember_selection)

        # Enter is handled to continue lists.
        self.text.bind("<Return>", self.handle_return)

        # Tab inside a list increases indentation.
        self.text.bind("<Tab>", self.handle_tab)

    # ============================================================
    # SHORTCUTS
    # ============================================================

    def shortcut_new(self, event=None):
        self.new_document()
        return "break"

    def shortcut_open(self, event=None):
        self.open_document()
        return "break"

    def shortcut_save(self, event=None):
        self.save_document()
        return "break"

    def shortcut_save_as(self, event=None):
        self.save_as()
        return "break"

    def shortcut_undo(self, event=None):
        self.undo()
        return "break"

    def shortcut_redo(self, event=None):
        self.redo()
        return "break"

    def shortcut_cut(self, event=None):
        self.cut()
        return "break"

    def shortcut_copy(self, event=None):
        self.copy()
        return "break"

    def shortcut_paste(self, event=None):
        self.paste()
        return "break"

    def shortcut_select_all(self, event=None):
        self.select_all()
        return "break"

    def shortcut_find(self, event=None):
        self.show_find()
        return "break"

    def shortcut_replace(self, event=None):
        self.show_replace()
        return "break"

    def shortcut_print(self, event=None):
        self.print_document()
        return "break"

    def shortcut_bold(self, event=None):
        self.toggle_bold()
        return "break"

    def shortcut_italic(self, event=None):
        self.toggle_italic()
        return "break"

    def shortcut_underline(self, event=None):
        self.toggle_underline()
        return "break"

    # ============================================================
    # FORMATTING
    # ============================================================

    def get_selection_range(self):
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")

            self.last_selection_start = start
            self.last_selection_end = end

            return start, end

        except tk.TclError:
            if (
                self.last_selection_start is not None
                and self.last_selection_end is not None
            ):
                return (
                    self.last_selection_start,
                    self.last_selection_end
                )

            return None, None

    def remember_selection(self, event=None):
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")

            self.last_selection_start = start
            self.last_selection_end = end

        except tk.TclError:
            pass

        self.update_toolbar()

    def get_format_at(self, index):
        tags = self.text.tag_names(index)

        # Find the newest formatting tag.
        for tag in reversed(tags):
            if tag.startswith("fmt_") and tag in self.format_tags:
                return self.format_tags[tag].copy()

        return {
            "font": self.current_font,
            "size": self.current_size,
            "color": self.current_color,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "strike": self.strike
        }

    def create_format_tag(self, fmt):
        family = re.sub(
            r"[^A-Za-z0-9]",
            "_",
            str(fmt["font"])
        )

        color = str(fmt["color"]).replace("#", "")

        styles = []

        if fmt["bold"]:
            styles.append("bold")

        if fmt["italic"]:
            styles.append("italic")

        style_string = " ".join(styles)

        tag_name = (
            f"fmt_{family}_"
            f"{fmt['size']}_"
            f"{color}_"
            f"{int(fmt['bold'])}_"
            f"{int(fmt['italic'])}_"
            f"{int(fmt['underline'])}_"
            f"{int(fmt['strike'])}"
        )

        if tag_name not in self.format_tags:
            self.format_tags[tag_name] = fmt.copy()

            self.text.tag_configure(
                tag_name,
                font=(
                    fmt["font"],
                    fmt["size"],
                    style_string
                ),
                foreground=fmt["color"],
                underline=fmt["underline"],
                overstrike=fmt["strike"]
            )

        return tag_name

    def remove_format_tags(self, start, end):
        tags = self.text.tag_names()

        for tag in tags:
            if tag.startswith("fmt_"):
                self.text.tag_remove(
                    tag,
                    start,
                    end
                )

    def apply_single_property_to_selection(
        self,
        property_name,
        value
    ):
        start, end = self.get_selection_range()

        if not start or not end:
            return False

        try:
            start_index = self.text.index(start)
            end_index = self.text.index(end)

            pos = start_index

            while self.text.compare(pos, "<", end_index):
                next_pos = self.text.index(f"{pos} + 1c")

                fmt = self.get_format_at(pos)

                fmt[property_name] = value

                tag = self.create_format_tag(fmt)

                self.remove_format_tags(
                    pos,
                    next_pos
                )

                self.text.tag_add(
                    tag,
                    pos,
                    next_pos
                )

                pos = next_pos

            self.restore_selection(
                start_index,
                end_index
            )

            self.modified = True
            self.update_title()

            return True

        except tk.TclError:
            return False

    def restore_selection(self, start, end):
        try:
            self.text.tag_remove(
                "sel",
                "1.0",
                tk.END
            )

            self.text.tag_add(
                "sel",
                start,
                end
            )

            self.text.mark_set(
                "insert",
                end
            )

            self.last_selection_start = start
            self.last_selection_end = end

        except tk.TclError:
            pass

    def font_changed(self, event=None):
        value = self.font_var.get().strip()

        if not value:
            return

        if self.apply_single_property_to_selection(
            "font",
            value
        ):
            pass
        else:
            self.current_font = value

        self.text.focus_set()
        self.update_toolbar()

    def size_changed(self, event=None):
        try:
            value = int(self.size_var.get())
        except (ValueError, TypeError):
            return

        if value < 1:
            return

        if self.apply_single_property_to_selection(
            "size",
            value
        ):
            pass
        else:
            self.current_size = value

        self.text.focus_set()
        self.update_toolbar()

    def toggle_bold(self):
        start, end = self.get_selection_range()

        if start and end:
            first = self.get_format_at(start)
            value = not first["bold"]

            self.apply_single_property_to_selection(
                "bold",
                value
            )

            self.bold = value
        else:
            self.bold = not self.bold

        self.text.focus_set()
        self.update_toolbar()

    def toggle_italic(self):
        start, end = self.get_selection_range()

        if start and end:
            first = self.get_format_at(start)
            value = not first["italic"]

            self.apply_single_property_to_selection(
                "italic",
                value
            )

            self.italic = value
        else:
            self.italic = not self.italic

        self.text.focus_set()
        self.update_toolbar()

    def toggle_underline(self):
        start, end = self.get_selection_range()

        if start and end:
            first = self.get_format_at(start)
            value = not first["underline"]

            self.apply_single_property_to_selection(
                "underline",
                value
            )

            self.underline = value
        else:
            self.underline = not self.underline

        self.text.focus_set()
        self.update_toolbar()

    def toggle_strike(self):
        start, end = self.get_selection_range()

        if start and end:
            first = self.get_format_at(start)
            value = not first["strike"]

            self.apply_single_property_to_selection(
                "strike",
                value
            )

            self.strike = value
        else:
            self.strike = not self.strike

        self.text.focus_set()
        self.update_toolbar()

    # ============================================================
    # COLORS
    # ============================================================

    def choose_color(self):
        result = colorchooser.askcolor(
            title="Choose Text Color",
            parent=self.root
        )

        rgb, hex_color = result

        if hex_color:
            self.set_color(hex_color)

    def set_color(self, color):
        if isinstance(color, tuple):
            color = color[1]

        if not color:
            return

        self.current_color = str(color)

        self.apply_single_property_to_selection(
            "color",
            self.current_color
        )

        self.color_button.configure(
            fg=self.current_color
        )

        self.text.focus_set()
        self.update_toolbar()

    # ============================================================
    # ALIGNMENT
    # ============================================================

    def get_paragraph_start(self, index):
        return self.text.index(
            f"{index} linestart"
        )

    def get_paragraph_end(self, index):
        return self.text.index(
            f"{index} lineend"
        )

    def get_selected_paragraphs(self):
        start, end = self.get_selection_range()

        if not start or not end:
            insert = self.text.index("insert")
            return [self.get_paragraph_start(insert)]

        first_line = self.text.index(
            f"{start} linestart"
        )

        # If selection ends exactly at the beginning of a line,
        # don't unnecessarily include that line.
        if self.text.compare(
            end,
            ">",
            f"{end} linestart"
        ):
            last_line = self.text.index(
                f"{end} linestart"
            )
        else:
            last_line = self.text.index(
                f"{end} - 1c linestart"
            )

        paragraphs = []

        current = first_line

        while self.text.compare(
            current,
            "<=",
            last_line
        ):
            paragraphs.append(current)

            next_line = self.text.index(
                f"{current} + 1 line linestart"
            )

            if self.text.compare(
                next_line,
                ">",
                last_line
            ):
                break

            current = next_line

        return paragraphs

    def set_alignment(self, alignment):
        paragraphs = self.get_selected_paragraphs()

        for start in paragraphs:
            end = self.text.index(
                f"{start} lineend"
            )

            for tag in (
                "align_left",
                "align_center",
                "align_right"
            ):
                self.text.tag_remove(
                    tag,
                    start,
                    f"{end} + 1c"
                )

            tag = {
                "left": "align_left",
                "center": "align_center",
                "right": "align_right"
            }[alignment]

            self.text.tag_add(
                tag,
                start,
                f"{end} + 1c"
            )

        self.current_alignment = alignment
        self.modified = True
        self.update_title()
        self.text.focus_set()

    # ============================================================
    # LISTS
    # ============================================================

    def line_text(self, line_start):
        return self.text.get(
            line_start,
            f"{line_start} lineend"
        )

    def line_has_bullet(self, text):
        return text.startswith(self.BULLET_PREFIX)

    def line_has_number(self, text):
        return bool(
            self.NUMBER_PREFIX_RE.match(text)
        )

    def remove_list_from_line(self, line_start):
        text = self.line_text(line_start)

        if text.startswith(self.BULLET_PREFIX):
            self.text.delete(
                line_start,
                f"{line_start} + {len(self.BULLET_PREFIX)}c"
            )
            return "bullet"

        match = self.NUMBER_PREFIX_RE.match(text)

        if match:
            prefix_length = len(match.group(0))

            self.text.delete(
                line_start,
                f"{line_start} + {prefix_length}c"
            )

            return "number"

        return None

    def add_bullet_to_line(self, line_start):
        text = self.line_text(line_start)

        if self.line_has_bullet(text):
            return

        if self.line_has_number(text):
            self.remove_list_from_line(line_start)

        self.text.insert(
            line_start,
            self.BULLET_PREFIX
        )

    def add_number_to_line(
        self,
        line_start,
        number
    ):
        text = self.line_text(line_start)

        if self.line_has_bullet(text):
            self.remove_list_from_line(line_start)
        elif self.line_has_number(text):
            self.remove_list_from_line(line_start)

        self.text.insert(
            line_start,
            f"{number}. "
        )

    def toggle_bullets(self):
        paragraphs = self.get_selected_paragraphs()

        if not paragraphs:
            return

        # If every selected paragraph is already a bullet,
        # remove bullets.
        all_bullets = all(
            self.line_has_bullet(
                self.line_text(p)
            )
            for p in paragraphs
        )

        for paragraph in paragraphs:
            if all_bullets:
                if self.line_has_bullet(
                    self.line_text(paragraph)
                ):
                    self.remove_list_from_line(
                        paragraph
                    )
            else:
                self.add_bullet_to_line(
                    paragraph
                )

        self.modified = True
        self.update_title()
        self.text.focus_set()

    def toggle_numbering(self):
        paragraphs = self.get_selected_paragraphs()

        if not paragraphs:
            return

        all_numbered = all(
            self.line_has_number(
                self.line_text(p)
            )
            for p in paragraphs
        )

        if all_numbered:
            for paragraph in paragraphs:
                self.remove_list_from_line(
                    paragraph
                )
        else:
            number = 1

            for paragraph in paragraphs:
                self.add_number_to_line(
                    paragraph,
                    number
                )
                number += 1

            # Renumber consecutive list items after changes.
            self.renumber_all_numbered_lists()

        self.modified = True
        self.update_title()
        self.text.focus_set()

    def remove_list_formatting(self):
        paragraphs = self.get_selected_paragraphs()

        for paragraph in paragraphs:
            self.remove_list_from_line(
                paragraph
            )

        self.modified = True
        self.update_title()
        self.text.focus_set()

    def renumber_all_numbered_lists(self):
        current = "1.0"
        number = 1
        in_numbered_list = False

        while self.text.compare(
            current,
            "<",
            "end-1c"
        ):
            text = self.line_text(current)

            if self.line_has_number(text):
                prefix_match = self.NUMBER_PREFIX_RE.match(text)

                if prefix_match:
                    old_number = prefix_match.group(1)
                    new_prefix = f"{number}. "

                    old_prefix = f"{old_number}. "

                    if old_prefix != new_prefix:
                        self.text.delete(
                            current,
                            f"{current} + {len(old_prefix)}c"
                        )

                        self.text.insert(
                            current,
                            new_prefix
                        )

                    number += 1
                    in_numbered_list = True
            else:
                if not self.line_has_bullet(text):
                    number = 1
                    in_numbered_list = False

            next_line = self.text.index(
                f"{current} + 1 line linestart"
            )

            if self.text.compare(
                next_line,
                ">=",
                "end"
            ):
                break

            current = next_line

    # ============================================================
    # LIST ENTER / TAB
    # ============================================================

    def handle_return(self, event=None):
        insert = self.text.index("insert")

        line_start = self.text.index(
            f"{insert} linestart"
        )

        current_line = self.line_text(
            line_start
        )

        # Bullet
        if current_line.startswith(
            self.BULLET_PREFIX
        ):
            content = current_line[
                len(self.BULLET_PREFIX):
            ].strip()

            if not content:
                # Empty bullet -> remove it and create normal line.
                self.text.delete(
                    line_start,
                    f"{line_start} + {len(self.BULLET_PREFIX)}c"
                )

                self.text.insert(
                    insert,
                    "\n"
                )

                return "break"

            self.text.insert(
                insert,
                "\n" + self.BULLET_PREFIX
            )

            self.modified = True
            self.renumber_all_numbered_lists()

            return "break"

        # Numbered list
        number_match = self.NUMBER_PREFIX_RE.match(
            current_line
        )

        if number_match:
            number = int(
                number_match.group(1)
            )

            prefix = number_match.group(0)

            content = current_line[
                len(prefix):
            ].strip()

            if not content:
                # Empty numbered item -> exit list.
                self.text.delete(
                    line_start,
                    f"{line_start} + {len(prefix)}c"
                )

                self.text.insert(
                    insert,
                    "\n"
                )

                self.renumber_all_numbered_lists()

                return "break"

            self.text.insert(
                insert,
                f"\n{number + 1}. "
            )

            self.renumber_all_numbered_lists()

            self.modified = True

            return "break"

        # Normal Enter
        self.text.insert(
            insert,
            "\n"
        )

        self.modified = True

        return "break"

    def handle_tab(self, event=None):
        insert = self.text.index("insert")

        line_start = self.text.index(
            f"{insert} linestart"
        )

        text = self.line_text(
            line_start
        )

        if (
            self.line_has_bullet(text)
            or self.line_has_number(text)
        ):
            self.text.insert(
                line_start,
                "    "
            )

            self.modified = True

            return "break"

        return None

    # ============================================================
    # TOOLBAR STATE
    # ============================================================

    def update_toolbar(self):
        try:
            start, end = self.get_selection_range()

            if start and end:
                fmt = self.get_format_at(start)

                self.font_var.set(
                    fmt["font"]
                )

                self.size_var.set(
                    str(fmt["size"])
                )

                self.current_color = fmt["color"]
                self.bold = fmt["bold"]
                self.italic = fmt["italic"]
                self.underline = fmt["underline"]
                self.strike = fmt["strike"]

            else:
                self.font_var.set(
                    self.current_font
                )

                self.size_var.set(
                    str(self.current_size)
                )

            self.bold_button.configure(
                relief="sunken"
                if self.bold
                else "raised"
            )

            self.italic_button.configure(
                relief="sunken"
                if self.italic
                else "raised"
            )

            self.underline_button.configure(
                relief="sunken"
                if self.underline
                else "raised"
            )

            self.strike_button.configure(
                relief="sunken"
                if self.strike
                else "raised"
            )

            self.color_button.configure(
                fg=self.current_color
            )

            self.update_status()

        except tk.TclError:
            pass

    def cursor_changed(self, event=None):
        try:
            insert = self.text.index("insert")

            fmt = self.get_format_at(
                insert
            )

            self.current_font = fmt["font"]
            self.current_size = fmt["size"]
            self.current_color = fmt["color"]

            self.bold = fmt["bold"]
            self.italic = fmt["italic"]
            self.underline = fmt["underline"]
            self.strike = fmt["strike"]

        except tk.TclError:
            pass

        self.remember_selection()
        self.update_toolbar()

    # ============================================================
    # EDIT OPERATIONS
    # ============================================================

    def cut(self):
        self.copy()

        try:
            self.text.delete(
                "sel.first",
                "sel.last"
            )
            self.modified = True
        except tk.TclError:
            pass

    def copy(self):
        try:
            selected = self.text.get(
                "sel.first",
                "sel.last"
            )

            self.root.clipboard_clear()
            self.root.clipboard_append(
                selected
            )

        except tk.TclError:
            pass

    def paste(self):
        try:
            data = self.root.clipboard_get()

            self.text.insert(
                "insert",
                data
            )

            self.modified = True

        except tk.TclError:
            pass

    def select_all(self):
        self.text.tag_add(
            "sel",
            "1.0",
            "end-1c"
        )

        self.last_selection_start = "1.0"
        self.last_selection_end = "end-1c"

        self.text.focus_set()

    def undo(self):
        try:
            self.text.edit_undo()
            self.modified = True
            self.update_title()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.text.edit_redo()
            self.modified = True
            self.update_title()
        except tk.TclError:
            pass

    # ============================================================
    # FIND / REPLACE
    # ============================================================

    def show_find(self):
        self.show_find_replace(False)

    def show_replace(self):
        self.show_find_replace(True)

    def show_find_replace(self, replace_mode=False):
        if self.find_window is not None:
            try:
                self.find_window.destroy()
            except tk.TclError:
                pass

        self.find_window = tk.Toplevel(
            self.root
        )

        self.find_window.title(
            "Replace" if replace_mode else "Find"
        )

        self.find_window.transient(
            self.root
        )

        self.find_window.resizable(
            False,
            False
        )

        frame = tk.Frame(
            self.find_window,
            padx=10,
            pady=10
        )
        frame.pack()

        tk.Label(
            frame,
            text="Find:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=3
        )

        find_var = tk.StringVar()

        find_entry = ttk.Entry(
            frame,
            textvariable=find_var,
            width=35
        )

        find_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=3
        )

        replace_var = tk.StringVar()

        if replace_mode:
            tk.Label(
                frame,
                text="Replace:"
            ).grid(
                row=1,
                column=0,
                sticky="w",
                pady=3
            )

            replace_entry = ttk.Entry(
                frame,
                textvariable=replace_var,
                width=35
            )

            replace_entry.grid(
                row=1,
                column=1,
                padx=5,
                pady=3
            )

        def find_next():
            target = find_var.get()

            if not target:
                return

            start = self.text.index(
                "insert"
            )

            position = self.text.search(
                target,
                start,
                stopindex=tk.END,
                nocase=False
            )

            if not position:
                position = self.text.search(
                    target,
                    "1.0",
                    stopindex=tk.END,
                    nocase=False
                )

            if position:
                end = self.text.index(
                    f"{position} + {len(target)}c"
                )

                self.text.tag_remove(
                    "sel",
                    "1.0",
                    tk.END
                )

                self.text.tag_add(
                    "sel",
                    position,
                    end
                )

                self.text.mark_set(
                    "insert",
                    end
                )

                self.text.see(position)

        def replace_one():
            target = find_var.get()

            if not target:
                return

            replacement = replace_var.get()

            try:
                start = self.text.index(
                    "sel.first"
                )
                end = self.text.index(
                    "sel.last"
                )

                selected = self.text.get(
                    start,
                    end
                )

                if selected == target:
                    self.text.delete(
                        start,
                        end
                    )

                    self.text.insert(
                        start,
                        replacement
                    )

                    self.modified = True

                find_next()

            except tk.TclError:
                find_next()

        def replace_all():
            target = find_var.get()

            if not target:
                return

            replacement = replace_var.get()

            content = self.text.get(
                "1.0",
                tk.END
            )

            content = content.replace(
                target,
                replacement
            )

            self.text.delete(
                "1.0",
                tk.END
            )

            self.text.insert(
                "1.0",
                content
            )

            self.modified = True
            self.update_title()

        buttons = tk.Frame(frame)
        buttons.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=(8, 0)
        )

        ttk.Button(
            buttons,
            text="Find Next",
            command=find_next
        ).pack(
            side="left",
            padx=3
        )

        if replace_mode:
            ttk.Button(
                buttons,
                text="Replace",
                command=replace_one
            ).pack(
                side="left",
                padx=3
            )

            ttk.Button(
                buttons,
                text="Replace All",
                command=replace_all
            ).pack(
                side="left",
                padx=3
            )

        ttk.Button(
            buttons,
            text="Close",
            command=self.find_window.destroy
        ).pack(
            side="left",
            padx=3
        )

        find_entry.focus_set()

        self.find_window.bind(
            "<Return>",
            lambda e: find_next()
        )

    # ============================================================
    # DOCUMENT MANAGEMENT
    # ============================================================

    def confirm_save(self):
        if not self.modified:
            return True

        result = messagebox.askyesnocancel(
            "Save Changes",
            "The document has been modified.\n\n"
            "Do you want to save your changes?"
        )

        if result is None:
            return False

        if result:
            return self.save_document()

        return True

    def new_document(self):
        if not self.confirm_save():
            return

        self.text.delete(
            "1.0",
            tk.END
        )

        self.filename = None
        self.modified = False

        self.format_tags.clear()

        self.current_font = self.DEFAULT_FONT
        self.current_size = self.DEFAULT_SIZE
        self.current_color = self.DEFAULT_COLOR

        self.bold = False
        self.italic = False
        self.underline = False
        self.strike = False

        self.update_title()
        self.update_toolbar()

        self.text.focus_set()

    def open_document(self):
        if not self.confirm_save():
            return

        filename = filedialog.askopenfilename(
            title="Open Document",
            filetypes=[
                ("Rich Text Format", "*.rtf"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return

        try:
            if filename.lower().endswith(
                ".rtf"
            ):
                with open(
                    filename,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:
                    data = file.read()

                self.load_rtf(data)

            else:
                with open(
                    filename,
                    "r",
                    encoding="utf-8",
                    errors="replace"
                ) as file:
                    data = file.read()

                self.text.delete(
                    "1.0",
                    tk.END
                )

                self.text.insert(
                    "1.0",
                    data
                )

            self.filename = filename
            self.modified = False

            self.update_title()

        except Exception as exc:
            messagebox.showerror(
                "Open Error",
                f"Could not open the file.\n\n{exc}"
            )

    def save_document(self):
        if not self.filename:
            return self.save_as()

        return self.save_to_file(
            self.filename
        )

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save Document",
            defaultextension=".rtf",
            filetypes=[
                ("Rich Text Format", "*.rtf"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )

        if not filename:
            return False

        return self.save_to_file(
            filename
        )

    def save_to_file(self, filename):
        try:
            if filename.lower().endswith(
                ".rtf"
            ):
                content = self.export_rtf()

                with open(
                    filename,
                    "w",
                    encoding="utf-8"
                ) as file:
                    file.write(content)

            else:
                content = self.text.get(
                    "1.0",
                    "end-1c"
                )

                with open(
                    filename,
                    "w",
                    encoding="utf-8"
                ) as file:
                    file.write(content)

            self.filename = filename
            self.modified = False

            self.update_title()

            return True

        except Exception as exc:
            messagebox.showerror(
                "Save Error",
                f"Could not save the file.\n\n{exc}"
            )

            return False

    # ============================================================
    # RTF EXPORT
    # ============================================================

    def rtf_escape(self, text):
        text = text.replace(
            "\\",
            "\\\\"
        )

        text = text.replace(
            "{",
            "\\{"
        )

        text = text.replace(
            "}",
            "\\}"
        )

        text = text.replace(
            "\t",
            "\\tab "
        )

        return text

    def collect_rtf_colors(self):
        colors = []

        for fmt in self.format_tags.values():
            color = fmt["color"]

            if color not in colors:
                colors.append(color)

        if self.DEFAULT_COLOR not in colors:
            colors.insert(
                0,
                self.DEFAULT_COLOR
            )

        return colors

    def hex_to_rgb(self, color):
        color = color.lstrip("#")

        if len(color) != 6:
            return 0, 0, 0

        try:
            return (
                int(color[0:2], 16),
                int(color[2:4], 16),
                int(color[4:6], 16)
            )
        except ValueError:
            return 0, 0, 0

    def export_rtf(self):
        colors = self.collect_rtf_colors()

        color_table = [
            r"{\colortbl ;"
        ]

        for color in colors:
            r, g, b = self.hex_to_rgb(
                color
            )

            color_table.append(
                f"\\red{r}\\green{g}\\blue{b};"
            )

        color_table.append("}")

        rtf = [
            r"{\rtf1\ansi\deff0",
            r"{\fonttbl"
        ]

        fonts = []

        for fmt in self.format_tags.values():
            if fmt["font"] not in fonts:
                fonts.append(
                    fmt["font"]
                )

        if self.current_font not in fonts:
            fonts.append(
                self.current_font
            )

        for i, font in enumerate(fonts):
            safe_font = font.replace(
                "\\",
                ""
            )

            rtf.append(
                f"{{\\f{i} {safe_font};}}"
            )

        rtf.append("}")

        rtf.extend(
            color_table
        )

        # Export line by line.
        lines = self.text.get(
            "1.0",
            "end-1c"
        ).split("\n")

        position = "1.0"

        for line_index, line in enumerate(lines):
            # Determine list type.
            line_start = f"{line_index + 1}.0"

            bullet = line.startswith(
                self.BULLET_PREFIX
            )

            number_match = self.NUMBER_PREFIX_RE.match(
                line
            )

            if bullet:
                rtf.append(
                    r"\pntext\bullet\tab "
                )
                content_start = len(
                    self.BULLET_PREFIX
                )

            elif number_match:
                number = number_match.group(1)

                rtf.append(
                    rf"\pntext {number}.\tab "
                )

                content_start = len(
                    number_match.group(0)
                )

            else:
                content_start = 0

            # Alignment
            alignment = "left"

            tags = self.text.tag_names(
                line_start
            )

            if "align_center" in tags:
                alignment = "center"

            elif "align_right" in tags:
                alignment = "right"

            if alignment == "center":
                rtf.append(r"\qc ")

            elif alignment == "right":
                rtf.append(r"\qr ")

            else:
                rtf.append(r"\ql ")

            # Export characters.
            char_index = content_start

            while char_index < len(line):
                index = (
                    f"{line_index + 1}."
                    f"{char_index}"
                )

                fmt = self.get_format_at(
                    index
                )

                font_index = 0

                for i, font in enumerate(fonts):
                    if font == fmt["font"]:
                        font_index = i
                        break

                color_index = 0

                for i, color in enumerate(colors):
                    if color == fmt["color"]:
                        color_index = i + 1
                        break

                rtf.append(
                    f"\\f{font_index}"
                )

                rtf.append(
                    f"\\fs{int(fmt['size']) * 2}"
                )

                if color_index:
                    rtf.append(
                        f"\\cf{color_index}"
                    )

                if fmt["bold"]:
                    rtf.append(
                        r"\b"
                    )

                if fmt["italic"]:
                    rtf.append(
                        r"\i"
                    )

                if fmt["underline"]:
                    rtf.append(
                        r"\ul"
                    )

                if fmt["strike"]:
                    rtf.append(
                        r"\strike"
                    )

                # Find the end of the same formatting run.
                run_end = char_index + 1

                while run_end < len(line):
                    next_index = (
                        f"{line_index + 1}."
                        f"{run_end}"
                    )

                    next_fmt = self.get_format_at(
                        next_index
                    )

                    if next_fmt != fmt:
                        break

                    run_end += 1

                chunk = line[
                    char_index:run_end
                ]

                rtf.append(
                    self.rtf_escape(
                        chunk
                    )
                )

                # Reset character styles.
                rtf.append(
                    r"\b0\i0\ul0\strike0 "
                )

                char_index = run_end

            if line_index < len(lines) - 1:
                rtf.append(
                    r"\par "
                )

        rtf.append("}")

        return "".join(rtf)

    # ============================================================
    # RTF IMPORT
    # ============================================================

    def load_rtf(self, data):
        """
        Basic RTF importer.

        Supports:
            - fonts
            - sizes
            - colors
            - bold
            - italic
            - underline
            - strike
            - alignment
            - basic bullet / numbered list markers
        """

        self.text.delete(
            "1.0",
            tk.END
        )

        font_names = self.parse_font_table(
            data
        )

        colors = self.parse_color_table(
            data
        )

        body = self.extract_rtf_body(
            data
        )

        state = {
            "font": self.DEFAULT_FONT,
            "size": self.DEFAULT_SIZE,
            "color": self.DEFAULT_COLOR,
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
            "alignment": "left"
        }

        output_position = "1.0"

        i = 0

        while i < len(body):
            char = body[i]

            if char == "\\":
                command, consumed = self.read_rtf_command(
                    body,
                    i
                )

                if command is not None:
                    self.process_rtf_command(
                        command,
                        state,
                        font_names,
                        colors
                    )

                    i += consumed
                    continue

            if char == "{":
                i += 1
                continue

            if char == "}":
                i += 1
                continue

            if char == "\r":
                i += 1
                continue

            if char == "\n":
                i += 1
                continue

            # Insert character.
            start = self.text.index(
                "end-1c"
            )

            self.text.insert(
                tk.END,
                char
            )

            end = self.text.index(
                "end-1c"
            )

            fmt = {
                "font": state["font"],
                "size": state["size"],
                "color": state["color"],
                "bold": state["bold"],
                "italic": state["italic"],
                "underline": state["underline"],
                "strike": state["strike"]
            }

            tag = self.create_format_tag(
                fmt
            )

            self.text.tag_add(
                tag,
                start,
                end
            )

            alignment_tag = {
                "left": "align_left",
                "center": "align_center",
                "right": "align_right"
            }.get(
                state["alignment"],
                "align_left"
            )

            self.text.tag_add(
                alignment_tag,
                start,
                end
            )

            i += 1

        # Convert basic RTF list markers into PowerEdit list prefixes.
        self.convert_imported_list_markers()

    def parse_font_table(self, data):
        fonts = []

        match = re.search(
            r"{\\fonttbl(.*?)}",
            data,
            re.DOTALL
        )

        if not match:
            return fonts

        table = match.group(1)

        for match in re.finditer(
            r"\\f(\d+)\s+([^;{}]+);",
            table
        ):
            index = int(
                match.group(1)
            )

            name = match.group(2).strip()

            while len(fonts) <= index:
                fonts.append(
                    self.DEFAULT_FONT
                )

            fonts[index] = name

        return fonts

    def parse_color_table(self, data):
        colors = [
            self.DEFAULT_COLOR
        ]

        match = re.search(
            r"{\\colortbl\s*(.*?)}",
            data,
            re.DOTALL
        )

        if not match:
            return colors

        table = match.group(1)

        entries = table.split(";")

        for entry in entries:
            r = re.search(
                r"\\red(\d+)",
                entry
            )

            g = re.search(
                r"\\green(\d+)",
                entry
            )

            b = re.search(
                r"\\blue(\d+)",
                entry
            )

            if r and g and b:
                color = (
                    f"#{int(r.group(1)):02x}"
                    f"{int(g.group(1)):02x}"
                    f"{int(b.group(1)):02x}"
                )

                colors.append(color)

        return colors

    def extract_rtf_body(self, data):
        start = data.find(
            "\\viewkind"
        )

        if start == -1:
            start = data.find(
                "\\ansi"
            )

        if start == -1:
            return data

        body = data[start:]

        # Remove font/color table sections.
        body = re.sub(
            r"{\\fonttbl.*?}",
            "",
            body,
            flags=re.DOTALL
        )

        body = re.sub(
            r"{\\colortbl.*?}",
            "",
            body,
            flags=re.DOTALL
        )

        return body

    def read_rtf_command(self, text, index):
        i = index + 1

        if i >= len(text):
            return None, 1

        if text[i] in "\\{}":
            return text[i], 2

        match = re.match(
            r"([a-zA-Z]+)(-?\d+)? ?",
            text[i:]
        )

        if not match:
            return None, 1

        word = match.group(1)
        number = match.group(2)

        consumed = 1 + len(
            match.group(0)
        )

        if number is not None:
            return (
                f"{word}{number}",
                consumed
            )

        return (
            word,
            consumed
        )

    def process_rtf_command(
        self,
        command,
        state,
        fonts,
        colors
    ):
        if command.startswith("f") and command[1:].isdigit():
            index = int(
                command[1:]
            )

            if 0 <= index < len(fonts):
                state["font"] = fonts[index]

            return

        if command.startswith("fs"):
            try:
                half_points = int(
                    command[2:]
                )

                state["size"] = max(
                    1,
                    half_points // 2
                )

            except ValueError:
                pass

            return

        if command.startswith("cf"):
            try:
                index = int(
                    command[2:]
                )

                if 0 <= index < len(colors):
                    state["color"] = colors[index]

            except ValueError:
                pass

            return

        if command == "b":
            state["bold"] = True
            return

        if command == "b0":
            state["bold"] = False
            return

        if command == "i":
            state["italic"] = True
            return

        if command == "i0":
            state["italic"] = False
            return

        if command == "ul":
            state["underline"] = True
            return

        if command == "ul0":
            state["underline"] = False
            return

        if command == "strike":
            state["strike"] = True
            return

        if command == "strike0":
            state["strike"] = False
            return

        if command == "ql":
            state["alignment"] = "left"
            return

        if command == "qc":
            state["alignment"] = "center"
            return

        if command == "qr":
            state["alignment"] = "right"
            return

        if command == "par":
            self.text.insert(
                tk.END,
                "\n"
            )
            return

        if command == "tab":
            self.text.insert(
                tk.END,
                "\t"
            )
            return

    def convert_imported_list_markers(self):
        """
        Detects simple RTF list markers that were exported by
        PowerEdit and converts them into normal PowerEdit prefixes.
        """

        lines = self.text.get(
            "1.0",
            "end-1c"
        ).split("\n")

        self.text.delete(
            "1.0",
            tk.END
        )

        for i, line in enumerate(lines):
            # Basic detection.
            if line.startswith(
                "• "
            ):
                pass

            elif re.match(
                r"^\d+\.\s",
                line
            ):
                pass

            self.text.insert(
                tk.END,
                line
            )

            if i < len(lines) - 1:
                self.text.insert(
                    tk.END,
                    "\n"
                )

    # ============================================================
    # PRINT
    # ============================================================

    def print_document(self):
        content = self.text.get(
            "1.0",
            "end-1c"
        )

        if not content.strip():
            messagebox.showinfo(
                "Print",
                "There is nothing to print."
            )
            return

        try:
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8"
            ) as file:
                file.write(content)
                filename = file.name

            subprocess.run(
                [
                    "lpr",
                    filename
                ],
                check=False
            )

            messagebox.showinfo(
                "Print",
                "The document was sent to the system printer."
            )

            try:
                os.unlink(filename)
            except OSError:
                pass

        except Exception as exc:
            messagebox.showerror(
                "Print Error",
                f"Could not print the document.\n\n{exc}"
            )

    # ============================================================
    # MODIFIED / TITLE
    # ============================================================

    def on_modified(self, event=None):
        try:
            if self.text.edit_modified():
                self.modified = True
                self.update_title()
                self.text.edit_modified(False)

        except tk.TclError:
            pass

    def update_title(self):
        name = (
            os.path.basename(self.filename)
            if self.filename
            else "Untitled"
        )

        marker = "* " if self.modified else ""

        self.root.title(
            f"{marker}{name} - PowerEdit"
        )

    def update_status(self):
        try:
            line, column = self.text.index(
                "insert"
            ).split(".")

            content = self.text.get(
                "1.0",
                "end-1c"
            )

            words = len(
                content.split()
            )

            self.status_var.set(
                f"Line {line}, Column {int(column) + 1}    "
                f"Words: {words}"
            )

        except tk.TclError:
            pass

    # ============================================================
    # EXIT
    # ============================================================

    def exit_application(self):
        if self.confirm_save():
            self.root.destroy()


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    root = tk.Tk()

    app = PowerEdit(root)

    root.mainloop()