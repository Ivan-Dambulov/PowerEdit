import os
import re
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, font


class PowerEdit:
    def __init__(self, root):
        self.root = root
        self.root.title("PowerEdit")
        self.root.geometry("1100x720")
        self.root.minsize(800, 500)

        # ---------------------------------------------------------
        # Document state
        # ---------------------------------------------------------

        self.current_file = None
        self.modified = False

        self.current_font = "Arial"
        self.current_size = 12
        self.current_color = "#000000"

        self.bold = False
        self.italic = False
        self.underline = False
        self.strike = False

        self.current_alignment = "left"

        # Remember selection because clicking toolbar removes focus
        self.last_selection_start = None
        self.last_selection_end = None

        # Formatting tags -> formatting dictionary
        self.format_tags = {}

        # Find/replace state
        self.find_window = None

        # ---------------------------------------------------------
        # Variables
        # ---------------------------------------------------------

        self.font_var = tk.StringVar(value=self.current_font)
        self.size_var = tk.StringVar(value=str(self.current_size))

        self.status_var = tk.StringVar(value="Ready")

        # ---------------------------------------------------------
        # Build UI
        # ---------------------------------------------------------

        self.create_menu()
        self.create_toolbar()
        self.create_editor()
        self.create_statusbar()

        self.bind_shortcuts()

        # Initial format tag
        self.create_format_tag(self.get_current_format())

        self.update_toolbar()
        self.update_title()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # =============================================================
    # MENU
    # =============================================================

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # File
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(
            label="New",
            accelerator="Ctrl+N",
            command=self.new_document
        )
        file_menu.add_command(
            label="Open...",
            accelerator="Ctrl+O",
            command=self.open_document
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Save",
            accelerator="Ctrl+S",
            command=self.save_document
        )
        file_menu.add_command(
            label="Save As...",
            accelerator="Ctrl+Shift+S",
            command=self.save_as
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Print",
            accelerator="Ctrl+P",
            command=self.print_document
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.on_close
        )

        menubar.add_cascade(label="File", menu=file_menu)

        # Edit
        edit_menu = tk.Menu(menubar, tearoff=False)

        edit_menu.add_command(
            label="Undo",
            accelerator="Ctrl+Z",
            command=self.undo
        )
        edit_menu.add_command(
            label="Redo",
            accelerator="Ctrl+Y",
            command=self.redo
        )
        edit_menu.add_separator()

        edit_menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=self.cut
        )
        edit_menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=self.copy
        )
        edit_menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=self.paste
        )
        edit_menu.add_command(
            label="Select All",
            accelerator="Ctrl+A",
            command=self.select_all
        )
        edit_menu.add_separator()

        edit_menu.add_command(
            label="Find",
            accelerator="Ctrl+F",
            command=self.show_find
        )
        edit_menu.add_command(
            label="Replace",
            accelerator="Ctrl+H",
            command=self.show_replace
        )

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

        format_menu.add_separator()

        format_menu.add_command(
            label="Text Color...",
            command=self.choose_custom_color
        )

        menubar.add_cascade(label="Format", menu=format_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(
            label="About PowerEdit",
            command=self.show_about
        )

        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # =============================================================
    # TOOLBAR
    # =============================================================

    def create_toolbar(self):
        outer = ttk.Frame(self.root)
        outer.pack(fill="x", padx=4, pady=4)

        # ---------------------------------------------------------
        # Row 1
        # ---------------------------------------------------------

        row1 = ttk.Frame(outer)
        row1.pack(fill="x")

        # Font
        ttk.Label(row1, text="Font:").pack(side="left", padx=(2, 3))

        fonts = sorted(set(font.families()))

        self.font_combo = ttk.Combobox(
            row1,
            textvariable=self.font_var,
            values=fonts,
            width=24,
            state="normal"
        )
        self.font_combo.pack(side="left", padx=(0, 6))

        self.font_combo.bind(
            "<<ComboboxSelected>>",
            self.font_changed
        )
        self.font_combo.bind(
            "<Return>",
            self.font_changed
        )

        # Size
        ttk.Label(row1, text="Size:").pack(side="left", padx=(0, 3))

        sizes = [
            "8", "9", "10", "11", "12", "14", "16", "18",
            "20", "22", "24", "26", "28", "32", "36",
            "40", "48", "56", "64", "72"
        ]

        self.size_combo = ttk.Combobox(
            row1,
            textvariable=self.size_var,
            values=sizes,
            width=5,
            state="normal"
        )
        self.size_combo.pack(side="left", padx=(0, 8))

        self.size_combo.bind(
            "<<ComboboxSelected>>",
            self.size_changed
        )
        self.size_combo.bind(
            "<Return>",
            self.size_changed
        )

        # Formatting buttons
        self.bold_button = tk.Button(
            row1,
            text="B",
            width=3,
            font=("Arial", 10, "bold"),
            command=self.toggle_bold,
            relief="raised"
        )
        self.bold_button.pack(side="left", padx=1)

        self.italic_button = tk.Button(
            row1,
            text="I",
            width=3,
            font=("Arial", 10, "italic"),
            command=self.toggle_italic,
            relief="raised"
        )
        self.italic_button.pack(side="left", padx=1)

        self.underline_button = tk.Button(
            row1,
            text="U",
            width=3,
            font=("Arial", 10, "underline"),
            command=self.toggle_underline,
            relief="raised"
        )
        self.underline_button.pack(side="left", padx=1)

        self.strike_button = tk.Button(
            row1,
            text="S",
            width=3,
            font=("Arial", 10),
            command=self.toggle_strike,
            relief="raised"
        )
        self.strike_button.pack(side="left", padx=1)

        ttk.Separator(
            row1,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=6
        )

        # Color
        ttk.Label(row1, text="Color:").pack(side="left")

        self.color_button = tk.Button(
            row1,
            text="A",
            width=3,
            bg="#000000",
            fg="white",
            command=self.show_color_palette
        )
        self.color_button.pack(side="left", padx=3)

        ttk.Separator(
            row1,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=6
        )

        # Alignment
        ttk.Label(row1, text="Align:").pack(side="left", padx=(0, 3))

        ttk.Button(
            row1,
            text="Left",
            command=lambda: self.set_alignment("left")
        ).pack(side="left", padx=1)

        ttk.Button(
            row1,
            text="Center",
            command=lambda: self.set_alignment("center")
        ).pack(side="left", padx=1)

        ttk.Button(
            row1,
            text="Right",
            command=lambda: self.set_alignment("right")
        ).pack(side="left", padx=1)

        # ---------------------------------------------------------
        # Row 2
        # ---------------------------------------------------------

        row2 = ttk.Frame(outer)
        row2.pack(fill="x", pady=(4, 0))

        ttk.Button(
            row2,
            text="Undo",
            command=self.undo
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Redo",
            command=self.redo
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Cut",
            command=self.cut
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Copy",
            command=self.copy
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Paste",
            command=self.paste
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Select All",
            command=self.select_all
        ).pack(side="left", padx=1)

        ttk.Separator(
            row2,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=6
        )

        ttk.Button(
            row2,
            text="Find",
            command=self.show_find
        ).pack(side="left", padx=1)

        ttk.Button(
            row2,
            text="Replace",
            command=self.show_replace
        ).pack(side="left", padx=1)

        ttk.Separator(
            row2,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=6
        )

        ttk.Button(
            row2,
            text="Print",
            command=self.print_document
        ).pack(side="left", padx=1)

    # =============================================================
    # EDITOR
    # =============================================================

    def create_editor(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.text = tk.Text(
            frame,
            wrap="word",
            undo=True,
            maxundo=-1,
            font=(self.current_font, self.current_size),
            padx=8,
            pady=8
        )

        scrollbar_y = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.text.yview
        )

        scrollbar_x = ttk.Scrollbar(
            frame,
            orient="horizontal",
            command=self.text.xview
        )

        self.text.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scrollbar_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Selection tracking
        self.text.bind(
            "<ButtonRelease-1>",
            self.remember_selection
        )

        self.text.bind(
            "<B1-Motion>",
            self.remember_selection
        )

        self.text.bind(
            "<<Selection>>",
            self.remember_selection
        )

        self.text.bind(
            "<KeyRelease>",
            self.editor_key_release
        )

        self.text.bind(
            "<KeyPress>",
            self.handle_keypress
        )

        self.text.bind(
            "<Button-1>",
            self.cursor_changed
        )

        self.text.bind(
            "<Motion>",
            self.cursor_changed
        )

        # Right click
        self.text.bind(
            "<Button-3>",
            self.show_context_menu
        )

    # =============================================================
    # STATUS BAR
    # =============================================================

    def create_statusbar(self):
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=5, pady=(0, 4))

        ttk.Label(
            bar,
            textvariable=self.status_var,
            anchor="w"
        ).pack(side="left")

    # =============================================================
    # FORMATTING
    # =============================================================

    def get_current_format(self):
        return {
            "font": self.current_font,
            "size": self.current_size,
            "color": self.current_color,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "strike": self.strike,
        }

    def normalize_color(self, color):
        if isinstance(color, tuple):
            if len(color) >= 2:
                color = color[1]

        if not color:
            return "#000000"

        return str(color)

    def create_format_tag(self, fmt):
        """
        Create a tag representing a COMPLETE character format.

        A key design point:
        when changing only size, we copy the existing format and
        modify only size. This prevents the font from changing.
        """

        fmt = fmt.copy()

        fmt["font"] = str(fmt.get("font", "Arial"))
        fmt["size"] = int(fmt.get("size", 12))
        fmt["color"] = self.normalize_color(
            fmt.get("color", "#000000")
        )

        fmt["bold"] = bool(fmt.get("bold", False))
        fmt["italic"] = bool(fmt.get("italic", False))
        fmt["underline"] = bool(fmt.get("underline", False))
        fmt["strike"] = bool(fmt.get("strike", False))

        family = re.sub(
            r"[^A-Za-z0-9]",
            "_",
            fmt["font"]
        )

        color = fmt["color"].replace("#", "")

        tag = (
            f"fmt_"
            f"{family}_"
            f"{fmt['size']}_"
            f"{color}_"
            f"{int(fmt['bold'])}_"
            f"{int(fmt['italic'])}_"
            f"{int(fmt['underline'])}_"
            f"{int(fmt['strike'])}"
        )

        styles = []

        if fmt["bold"]:
            styles.append("bold")

        if fmt["italic"]:
            styles.append("italic")

        style = " ".join(styles)

        self.text.tag_configure(
            tag,
            font=(
                fmt["font"],
                fmt["size"],
                style
            ),
            foreground=fmt["color"],
            underline=fmt["underline"],
            overstrike=fmt["strike"]
        )

        self.format_tags[tag] = fmt.copy()

        return tag

    def get_format_at(self, index):
        """
        Return the complete formatting of the character at index.
        """

        tags = self.text.tag_names(index)

        # Most recently applied formatting tag is preferred.
        for tag in reversed(tags):
            if tag.startswith("fmt_"):
                fmt = self.format_tags.get(tag)

                if fmt:
                    return fmt.copy()

        return self.get_current_format()

    def remove_format_tags(self, start, end):
        """
        Remove only our character-format tags.
        Alignment tags are left untouched.
        """

        tags = self.text.tag_names()

        for tag in tags:
            if tag.startswith("fmt_"):
                self.text.tag_remove(
                    tag,
                    start,
                    end
                )

    def get_selection_range(self):
        """
        Get the active selection.

        If clicking the toolbar removed the actual Tk selection,
        use the remembered selection.
        """

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
                try:
                    # Validate indexes
                    self.text.index(
                        self.last_selection_start
                    )
                    self.text.index(
                        self.last_selection_end
                    )

                    return (
                        self.last_selection_start,
                        self.last_selection_end
                    )

                except tk.TclError:
                    pass

        return None, None

    def remember_selection(self, event=None):
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")

            self.last_selection_start = start
            self.last_selection_end = end

            self.status_var.set(
                f"Selected: {self.text.count(start, end, 'chars')[0]} characters"
            )

        except tk.TclError:
            pass

    def apply_single_property_to_selection(
        self,
        property_name,
        value
    ):
        """
        Change ONLY one formatting property.

        This is the key method that prevents:
            changing size -> changing font
            changing color -> changing size
            changing bold -> changing everything
        """

        start, end = self.get_selection_range()

        if not start or not end:
            return False

        # Save selection
        self.last_selection_start = start
        self.last_selection_end = end

        pos = start

        while self.text.compare(pos, "<", end):

            next_pos = self.text.index(
                f"{pos} + 1 char"
            )

            fmt = self.get_format_at(pos)

            # Change ONLY the requested property.
            fmt[property_name] = value

            # Remove old complete format from this character.
            for tag in self.text.tag_names(pos):
                if tag.startswith("fmt_"):
                    self.text.tag_remove(
                        tag,
                        pos,
                        next_pos
                    )

            # Add the modified complete format.
            tag = self.create_format_tag(fmt)

            self.text.tag_add(
                tag,
                pos,
                next_pos
            )

            pos = next_pos

        self.modified = True
        self.update_title()

        self.restore_selection(start, end)

        return True

    def apply_current_format_to_selection(self):
        """
        Used when applying the complete current format.
        """

        start, end = self.get_selection_range()

        if not start or not end:
            return

        self.remove_format_tags(start, end)

        tag = self.create_format_tag(
            self.get_current_format()
        )

        self.text.tag_add(
            tag,
            start,
            end
        )

        self.modified = True
        self.update_title()

        self.restore_selection(start, end)

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

            self.text.see(start)

        except tk.TclError:
            pass

        self.last_selection_start = start
        self.last_selection_end = end

    # -------------------------------------------------------------
    # Font
    # -------------------------------------------------------------

    def font_changed(self, event=None):
        value = self.font_var.get().strip()

        if not value:
            return

        start, end = self.get_selection_range()

        if start and end:
            # ONLY font changes.
            self.apply_single_property_to_selection(
                "font",
                value
            )
        else:
            self.current_font = value

        self.text.focus_set()
        self.update_toolbar()

    # -------------------------------------------------------------
    # Size
    # -------------------------------------------------------------

    def size_changed(self, event=None):
        try:
            value = int(
                self.size_var.get().strip()
            )
        except (ValueError, TypeError):
            return

        if value < 1:
            return

        start, end = self.get_selection_range()

        if start and end:
            # ONLY size changes.
            self.apply_single_property_to_selection(
                "size",
                value
            )
        else:
            self.current_size = value

        self.text.focus_set()
        self.update_toolbar()

    # -------------------------------------------------------------
    # Color
    # -------------------------------------------------------------

    def set_color(self, color, window=None):
        color = self.normalize_color(color)

        start, end = self.get_selection_range()

        if start and end:
            # ONLY color changes.
            self.apply_single_property_to_selection(
                "color",
                color
            )
        else:
            self.current_color = color

        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass

        self.text.focus_set()
        self.update_toolbar()

    def choose_custom_color(self):
        result = colorchooser.askcolor(
            title="Choose Text Color",
            parent=self.root
        )

        if result:
            rgb, hex_color = result

            if hex_color:
                self.set_color(hex_color)

    # -------------------------------------------------------------
    # Bold
    # -------------------------------------------------------------

    def toggle_bold(self):
        start, end = self.get_selection_range()

        if start and end:
            fmt = self.get_format_at(start)

            self.apply_single_property_to_selection(
                "bold",
                not fmt["bold"]
            )
        else:
            self.bold = not self.bold

        self.text.focus_set()
        self.update_toolbar()

    # -------------------------------------------------------------
    # Italic
    # -------------------------------------------------------------

    def toggle_italic(self):
        start, end = self.get_selection_range()

        if start and end:
            fmt = self.get_format_at(start)

            self.apply_single_property_to_selection(
                "italic",
                not fmt["italic"]
            )
        else:
            self.italic = not self.italic

        self.text.focus_set()
        self.update_toolbar()

    # -------------------------------------------------------------
    # Underline
    # -------------------------------------------------------------

    def toggle_underline(self):
        start, end = self.get_selection_range()

        if start and end:
            fmt = self.get_format_at(start)

            self.apply_single_property_to_selection(
                "underline",
                not fmt["underline"]
            )
        else:
            self.underline = not self.underline

        self.text.focus_set()
        self.update_toolbar()

    # -------------------------------------------------------------
    # Strike
    # -------------------------------------------------------------

    def toggle_strike(self):
        start, end = self.get_selection_range()

        if start and end:
            fmt = self.get_format_at(start)

            self.apply_single_property_to_selection(
                "strike",
                not fmt["strike"]
            )
        else:
            self.strike = not self.strike

        self.text.focus_set()
        self.update_toolbar()

    # =============================================================
    # COLOR PALETTE
    # =============================================================

    def show_color_palette(self):
        window = tk.Toplevel(self.root)
        window.title("Text Color")
        window.resizable(False, False)
        window.transient(self.root)

        colors = [
            "#000000",
            "#800000",
            "#008000",
            "#808000",
            "#000080",
            "#800080",
            "#008080",
            "#808080",

            "#C00000",
            "#FF0000",
            "#00C000",
            "#00FF00",
            "#C0C000",
            "#FFFF00",
            "#0000C0",
            "#0000FF",

            "#C000C0",
            "#FF00FF",
            "#00C0C0",
            "#00FFFF",
            "#404040",
            "#808080",
            "#C0C0C0",
            "#FFFFFF",

            "#800000",
            "#FF8000",
            "#804000",
            "#804080",
            "#408080",
            "#004080",
            "#0080FF",
            "#4000FF",
        ]

        frame = ttk.Frame(window, padding=8)
        frame.pack()

        for i, color in enumerate(colors):
            button = tk.Button(
                frame,
                bg=color,
                width=3,
                height=1,
                relief="solid",
                borderwidth=1,
                command=lambda c=color: self.set_color(
                    c,
                    window
                )
            )

            button.grid(
                row=i // 8,
                column=i % 8,
                padx=2,
                pady=2
            )

        ttk.Button(
            frame,
            text="More Colors...",
            command=lambda: self.choose_color_from_palette_window(
                window
            )
        ).grid(
            row=4,
            column=0,
            columnspan=8,
            sticky="ew",
            pady=(7, 0)
        )

        window.grab_set()

    def choose_color_from_palette_window(self, window):
        result = colorchooser.askcolor(
            title="Choose Text Color",
            parent=window
        )

        if result:
            rgb, hex_color = result

            if hex_color:
                self.set_color(
                    hex_color,
                    window
                )

    # =============================================================
    # ALIGNMENT
    # =============================================================

    def set_alignment(self, alignment):
        self.current_alignment = alignment

        start, end = self.get_selection_range()

        if not start or not end:
            # Future paragraph
            self.apply_alignment_to_current_line()
            return

        # Apply to every paragraph touched by selection.
        line_start = self.text.index(
            f"{start} linestart"
        )

        line_end = self.text.index(
            f"{end} lineend"
        )

        if alignment == "left":
            tag = "align_left"
        elif alignment == "center":
            tag = "align_center"
        else:
            tag = "align_right"

        # Remove alignment tags
        for name in (
            "align_left",
            "align_center",
            "align_right"
        ):
            self.text.tag_remove(
                name,
                line_start,
                line_end
            )

        self.text.tag_configure(
            tag,
            justify=alignment
        )

        self.text.tag_add(
            tag,
            line_start,
            line_end
        )

        self.modified = True
        self.update_title()

        self.restore_selection(
            start,
            end
        )

        self.text.focus_set()

    def apply_alignment_to_current_line(self):
        index = self.text.index("insert")

        start = self.text.index(
            f"{index} linestart"
        )

        end = self.text.index(
            f"{index} lineend"
        )

        for name in (
            "align_left",
            "align_center",
            "align_right"
        ):
            self.text.tag_remove(
                name,
                start,
                end
            )

        tag = f"align_{self.current_alignment}"

        self.text.tag_configure(
            tag,
            justify=self.current_alignment
        )

        self.text.tag_add(
            tag,
            start,
            end
        )

        self.modified = True
        self.update_title()

    # =============================================================
    # TOOLBAR UPDATE
    # =============================================================

    def update_toolbar(self):
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

            self.color_button.configure(
                bg=fmt["color"]
            )

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

            self.color_button.configure(
                bg=self.current_color
            )

        # Update button relief
        self.bold_button.configure(
            relief="sunken" if self.bold else "raised"
        )

        self.italic_button.configure(
            relief="sunken" if self.italic else "raised"
        )

        self.underline_button.configure(
            relief="sunken" if self.underline else "raised"
        )

        self.strike_button.configure(
            relief="sunken" if self.strike else "raised"
        )

    # =============================================================
    # KEYBOARD / TYPING
    # =============================================================

    def handle_keypress(self, event):
        """
        Make newly typed text use the current formatting.
        """

        # Ctrl / Alt combinations are handled elsewhere.
        if event.state & 0x4:
            return

        # Alt
        if event.state & 0x8:
            return

        # Printable characters
        if event.char and event.char.isprintable():

            tag = self.create_format_tag(
                self.get_current_format()
            )

            try:
                self.text.edit_separator()

                self.text.insert(
                    "insert",
                    event.char,
                    tag
                )

                self.modified = True
                self.update_title()

                return "break"

            except tk.TclError:
                return

        # Tab
        if event.keysym == "Tab":
            tag = self.create_format_tag(
                self.get_current_format()
            )

            self.text.insert(
                "insert",
                "\t",
                tag
            )

            self.modified = True
            self.update_title()

            return "break"

        # Enter
        if event.keysym == "Return":

            tag = self.create_format_tag(
                self.get_current_format()
            )

            self.text.insert(
                "insert",
                "\n",
                tag
            )

            self.modified = True
            self.update_title()

            self.apply_alignment_to_current_line()

            return "break"

    def editor_key_release(self, event=None):
        self.update_toolbar()

        try:
            line, column = self.text.index(
                "insert"
            ).split(".")

            self.status_var.set(
                f"Line {line}, Column {int(column) + 1}"
            )

        except Exception:
            pass

    def cursor_changed(self, event=None):
        self.remember_selection()

    # =============================================================
    # SHORTCUTS
    # =============================================================

    def bind_shortcuts(self):
        self.root.bind_all(
            "<Control-n>",
            lambda e: self.new_document()
        )

        self.root.bind_all(
            "<Control-o>",
            lambda e: self.open_document()
        )

        self.root.bind_all(
            "<Control-s>",
            lambda e: self.save_document()
        )

        self.root.bind_all(
            "<Control-Shift-S>",
            lambda e: self.save_as()
        )

        self.root.bind_all(
            "<Control-p>",
            lambda e: self.print_document()
        )

        self.root.bind_all(
            "<Control-z>",
            lambda e: self.undo()
        )

        self.root.bind_all(
            "<Control-y>",
            lambda e: self.redo()
        )

        self.root.bind_all(
            "<Control-x>",
            lambda e: self.cut()
        )

        self.root.bind_all(
            "<Control-c>",
            lambda e: self.copy()
        )

        self.root.bind_all(
            "<Control-v>",
            lambda e: self.paste()
        )

        self.root.bind_all(
            "<Control-a>",
            lambda e: self.select_all()
        )

        self.root.bind_all(
            "<Control-f>",
            lambda e: self.show_find()
        )

        self.root.bind_all(
            "<Control-h>",
            lambda e: self.show_replace()
        )

        self.root.bind_all(
            "<Control-b>",
            lambda e: self.toggle_bold()
        )

        self.root.bind_all(
            "<Control-i>",
            lambda e: self.toggle_italic()
        )

        self.root.bind_all(
            "<Control-u>",
            lambda e: self.toggle_underline()
        )

    # =============================================================
    # EDIT COMMANDS
    # =============================================================

    def undo(self):
        try:
            self.text.edit_undo()
            self.modified = True
            self.update_title()
            self.update_toolbar()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.text.edit_redo()
            self.modified = True
            self.update_title()
            self.update_toolbar()
        except tk.TclError:
            pass

    def cut(self):
        self.copy()

        try:
            start, end = self.get_selection_range()

            if start and end:
                self.text.delete(
                    start,
                    end
                )

                self.last_selection_start = None
                self.last_selection_end = None

                self.modified = True
                self.update_title()

        except tk.TclError:
            pass

    def copy(self):
        try:
            start, end = self.get_selection_range()

            if start and end:
                data = self.text.get(
                    start,
                    end
                )

                self.root.clipboard_clear()
                self.root.clipboard_append(data)

        except tk.TclError:
            pass

    def paste(self):
        try:
            data = self.root.clipboard_get()
        except tk.TclError:
            return

        try:
            start, end = self.get_selection_range()

            if start and end:
                self.text.delete(
                    start,
                    end
                )

                self.text.mark_set(
                    "insert",
                    start
                )

        except tk.TclError:
            pass

        tag = self.create_format_tag(
            self.get_current_format()
        )

        self.text.insert(
            "insert",
            data,
            tag
        )

        self.modified = True
        self.update_title()
        self.update_toolbar()

    def select_all(self):
        try:
            self.text.tag_add(
                "sel",
                "1.0",
                "end-1c"
            )

            self.text.mark_set(
                "insert",
                "1.0"
            )

            self.last_selection_start = "1.0"
            self.last_selection_end = "end-1c"

            self.text.focus_set()

        except tk.TclError:
            pass

    # =============================================================
    # NEW DOCUMENT
    # =============================================================

    def new_document(self):
        if not self.confirm_discard():
            return

        self.text.delete(
            "1.0",
            tk.END
        )

        self.current_file = None
        self.modified = False

        self.current_font = "Arial"
        self.current_size = 12
        self.current_color = "#000000"

        self.bold = False
        self.italic = False
        self.underline = False
        self.strike = False

        self.last_selection_start = None
        self.last_selection_end = None

        self.text.edit_reset()

        self.update_toolbar()
        self.update_title()

    # =============================================================
    # OPEN
    # =============================================================

    def open_document(self):
        if not self.confirm_discard():
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
            if filename.lower().endswith(".rtf"):
                self.load_rtf(filename)
            else:
                self.load_txt(filename)

            self.current_file = filename
            self.modified = False

            self.update_title()

        except Exception as exc:
            messagebox.showerror(
                "Open Error",
                f"Could not open the file:\n\n{exc}"
            )

    def load_txt(self, filename):
        with open(
            filename,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as f:
            data = f.read()

        self.text.delete(
            "1.0",
            tk.END
        )

        tag = self.create_format_tag(
            self.get_current_format()
        )

        self.text.insert(
            "1.0",
            data,
            tag
        )

        self.text.edit_reset()

    # =============================================================
    # SAVE
    # =============================================================

    def save_document(self):
        if not self.current_file:
            return self.save_as()

        try:
            if self.current_file.lower().endswith(".rtf"):
                self.save_rtf(
                    self.current_file
                )
            else:
                self.save_txt(
                    self.current_file
                )

            self.modified = False
            self.update_title()

            return True

        except Exception as exc:
            messagebox.showerror(
                "Save Error",
                f"Could not save the file:\n\n{exc}"
            )

            return False

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

        try:
            if filename.lower().endswith(".txt"):
                self.save_txt(filename)
            else:
                if not filename.lower().endswith(".rtf"):
                    filename += ".rtf"

                self.save_rtf(filename)

            self.current_file = filename
            self.modified = False

            self.update_title()

            return True

        except Exception as exc:
            messagebox.showerror(
                "Save Error",
                f"Could not save the file:\n\n{exc}"
            )

            return False

    def save_txt(self, filename):
        data = self.text.get(
            "1.0",
            "end-1c"
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(data)

    # =============================================================
    # RTF EXPORT
    # =============================================================

    def escape_rtf(self, text):
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

        return text

    def collect_rtf_fonts(self):
        fonts = []

        for tag, fmt in self.format_tags.items():
            if fmt["font"] not in fonts:
                fonts.append(fmt["font"])

        if self.current_font not in fonts:
            fonts.append(self.current_font)

        if not fonts:
            fonts = ["Arial"]

        return fonts

    def collect_rtf_colors(self):
        colors = []

        for tag, fmt in self.format_tags.items():
            color = self.normalize_color(
                fmt["color"]
            )

            if color not in colors:
                colors.append(color)

        if self.current_color not in colors:
            colors.append(
                self.current_color
            )

        if not colors:
            colors = ["#000000"]

        return colors

    def rgb_from_hex(self, color):
        color = self.normalize_color(color)

        if color.startswith("#"):
            color = color[1:]

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

    def save_rtf(self, filename):
        fonts = self.collect_rtf_fonts()
        colors = self.collect_rtf_colors()

        font_index = {
            name: i
            for i, name in enumerate(fonts)
        }

        color_index = {
            color: i + 1
            for i, color in enumerate(colors)
        }

        output = []

        output.append(
            r"{\rtf1\ansi\deff0"
        )

        # Font table
        output.append(
            r"{\fonttbl"
        )

        for i, name in enumerate(fonts):
            safe_name = name.replace(
                "\\",
                ""
            )

            output.append(
                f"{{\\f{i} {safe_name};}}"
            )

        output.append("}")

        # Color table
        output.append(
            r"{\colortbl;"
        )

        for color in colors:
            r, g, b = self.rgb_from_hex(
                color
            )

            output.append(
                f"\\red{r}"
                f"\\green{g}"
                f"\\blue{b};"
            )

        output.append("}")

        output.append(
            r"\viewkind4\uc1"
        )

        text_data = self.text.get(
            "1.0",
            "end-1c"
        )

        lines = text_data.split(
            "\n"
        )

        for line_number, line in enumerate(lines, start=1):

            index = f"{line_number}.0"

            # Paragraph alignment
            alignment = self.get_alignment_at(
                index
            )

            if alignment == "center":
                output.append(r"\qc")
            elif alignment == "right":
                output.append(r"\qr")
            else:
                output.append(r"\ql")

            for char_offset, char in enumerate(line):

                pos = f"{line_number}.{char_offset}"

                fmt = self.get_format_at(pos)

                fi = font_index.get(
                    fmt["font"],
                    0
                )

                ci = color_index.get(
                    fmt["color"],
                    1
                )

                output.append(
                    f"\\f{fi}"
                    f"\\fs{int(fmt['size'] * 2)}"
                    f"\\cf{ci}"
                )

                output.append(
                    "\\b" if fmt["bold"]
                    else "\\b0"
                )

                output.append(
                    "\\i" if fmt["italic"]
                    else "\\i0"
                )

                output.append(
                    "\\ul" if fmt["underline"]
                    else "\\ul0"
                )

                output.append(
                    "\\strike" if fmt["strike"]
                    else "\\strike0"
                )

                if char == "\t":
                    output.append(
                        r"\tab "
                    )

                elif char in (
                    "\\",
                    "{",
                    "}"
                ):
                    output.append(
                        self.escape_rtf(char)
                    )

                else:
                    code = ord(char)

                    if code > 127:
                        signed = (
                            code
                            if code < 32768
                            else code - 65536
                        )

                        output.append(
                            f"\\u{signed}?"
                        )
                    else:
                        output.append(char)

            if line_number < len(lines):
                output.append(
                    r"\par "
                )

        output.append("}")

        with open(
            filename,
            "w",
            encoding="ascii",
            errors="ignore"
        ) as f:
            f.write(
                "".join(output)
            )

    def get_alignment_at(self, index):
        tags = self.text.tag_names(index)

        if "align_center" in tags:
            return "center"

        if "align_right" in tags:
            return "right"

        return "left"

    # =============================================================
    # RTF IMPORT
    # =============================================================

    def load_rtf(self, filename):
        with open(
            filename,
            "r",
            encoding="latin-1",
            errors="replace"
        ) as f:
            rtf = f.read()

        fonts = self.parse_rtf_fonts(
            rtf
        )

        colors = self.parse_rtf_colors(
            rtf
        )

        self.text.delete(
            "1.0",
            tk.END
        )

        state = {
            "font": "Arial",
            "size": 12,
            "color": "#000000",
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
            "alignment": "left"
        }

        if fonts:
            state["font"] = fonts[0]

        if colors:
            state["color"] = colors[0]

        stack = []

        output_pos = "1.0"

        i = 0

        while i < len(rtf):

            ch = rtf[i]

            # Ignore RTF header/group braces
            if ch == "{":
                stack.append(
                    state.copy()
                )

                i += 1
                continue

            if ch == "}":
                if stack:
                    state = stack.pop()

                i += 1
                continue

            if ch == "\\":
                i += 1

                if i >= len(rtf):
                    break

                # Escaped special chars
                if rtf[i] in "\\{}":
                    self.insert_rtf_text(
                        rtf[i],
                        state
                    )

                    i += 1
                    continue

                # Hex encoded character
                if rtf[i] == "'":
                    if i + 2 < len(rtf):
                        hex_value = rtf[
                            i + 1:i + 3
                        ]

                        try:
                            char = bytes.fromhex(
                                hex_value
                            ).decode(
                                "cp1252",
                                errors="replace"
                            )

                            self.insert_rtf_text(
                                char,
                                state
                            )

                            i += 3
                            continue

                        except ValueError:
                            pass

                # Read control word
                match = re.match(
                    r"([a-zA-Z]+)(-?\d+)? ?",
                    rtf[i:]
                )

                if not match:
                    i += 1
                    continue

                word = match.group(1)
                number = match.group(2)

                consumed = match.end()
                i += consumed

                if word == "par":
                    self.insert_rtf_text(
                        "\n",
                        state
                    )

                elif word == "line":
                    self.insert_rtf_text(
                        "\n",
                        state
                    )

                elif word == "tab":
                    self.insert_rtf_text(
                        "\t",
                        state
                    )

                elif word == "b":
                    state["bold"] = (
                        number != "0"
                    )

                elif word == "i":
                    state["italic"] = (
                        number != "0"
                    )

                elif word == "ul":
                    state["underline"] = True

                elif word == "ulnone":
                    state["underline"] = False

                elif word == "strike":
                    state["strike"] = (
                        number != "0"
                    )

                elif word == "f" and number is not None:
                    fi = int(number)

                    if 0 <= fi < len(fonts):
                        state["font"] = fonts[fi]

                elif word == "fs" and number:
                    state["size"] = max(
                        1,
                        int(number) // 2
                    )

                elif word == "cf" and number:
                    ci = int(number) - 1

                    if 0 <= ci < len(colors):
                        state["color"] = colors[ci]

                elif word == "qc":
                    state["alignment"] = "center"

                elif word == "qr":
                    state["alignment"] = "right"

                elif word == "ql":
                    state["alignment"] = "left"

                elif word == "u" and number:
                    try:
                        value = int(number)

                        if value < 0:
                            value += 65536

                        self.insert_rtf_text(
                            chr(value),
                            state
                        )

                        # Skip optional replacement char
                        if (
                            i < len(rtf)
                            and rtf[i] == "?"
                        ):
                            i += 1

                    except ValueError:
                        pass

                continue

            # Plain text
            if ch not in "\r\n":
                self.insert_rtf_text(
                    ch,
                    state
                )

            i += 1

        self.text.edit_reset()

        self.update_toolbar()

    def insert_rtf_text(self, text, state):
        fmt = {
            "font": state["font"],
            "size": state["size"],
            "color": state["color"],
            "bold": state["bold"],
            "italic": state["italic"],
            "underline": state["underline"],
            "strike": state["strike"],
        }

        tag = self.create_format_tag(
            fmt
        )

        start = self.text.index(
            "end-1c"
        )

        self.text.insert(
            tk.END,
            text,
            tag
        )

        end = self.text.index(
            "end-1c"
        )

        # Apply paragraph alignment
        line_start = self.text.index(
            f"{start} linestart"
        )

        line_end = self.text.index(
            f"{end} lineend"
        )

        align_tag = (
            f"align_{state['alignment']}"
        )

        self.text.tag_configure(
            align_tag,
            justify=state["alignment"]
        )

        self.text.tag_add(
            align_tag,
            line_start,
            line_end
        )

    def parse_rtf_fonts(self, rtf):
        match = re.search(
            r"{\\fonttbl(.*?)}",
            rtf,
            re.DOTALL
        )

        if not match:
            return ["Arial"]

        table = match.group(1)

        fonts = []

        for m in re.finditer(
            r"\\f\d+[^;]*\s([^;{}]+);",
            table
        ):
            name = m.group(1).strip()

            if name:
                fonts.append(name)

        if not fonts:
            fonts = ["Arial"]

        return fonts

    def parse_rtf_colors(self, rtf):
        match = re.search(
            r"{\\colortbl;(.*?)}",
            rtf,
            re.DOTALL
        )

        if not match:
            return ["#000000"]

        table = match.group(1)

        colors = []

        for entry in table.split(";"):
            r_match = re.search(
                r"\\red(\d+)",
                entry
            )

            g_match = re.search(
                r"\\green(\d+)",
                entry
            )

            b_match = re.search(
                r"\\blue(\d+)",
                entry
            )

            if (
                r_match
                and g_match
                and b_match
            ):
                r = int(r_match.group(1))
                g = int(g_match.group(1))
                b = int(b_match.group(1))

                colors.append(
                    f"#{r:02x}{g:02x}{b:02x}"
                )

        if not colors:
            colors = ["#000000"]

        return colors

    # =============================================================
    # FIND
    # =============================================================

    def show_find(self):
        if (
            self.find_window is not None
            and self.find_window.winfo_exists()
        ):
            self.find_window.lift()
            return

        window = tk.Toplevel(self.root)
        window.title("Find")
        window.resizable(False, False)

        self.find_window = window

        frame = ttk.Frame(
            window,
            padding=10
        )
        frame.pack(fill="both")

        ttk.Label(
            frame,
            text="Find:"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        entry = ttk.Entry(
            frame,
            width=35
        )
        entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text="Find Next",
            command=lambda: self.find_next(
                entry.get()
            )
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            pady=5
        )

        entry.focus_set()

        window.protocol(
            "WM_DELETE_WINDOW",
            window.destroy
        )

    def find_next(self, query):
        if not query:
            return

        try:
            start = self.text.index(
                "insert"
            )

            pos = self.text.search(
                query,
                start,
                stopindex=tk.END,
                nocase=True
            )

            if not pos:
                pos = self.text.search(
                    query,
                    "1.0",
                    stopindex=tk.END,
                    nocase=True
                )

            if pos:
                end = self.text.index(
                    f"{pos} + {len(query)} chars"
                )

                self.text.tag_remove(
                    "sel",
                    "1.0",
                    tk.END
                )

                self.text.tag_add(
                    "sel",
                    pos,
                    end
                )

                self.text.mark_set(
                    "insert",
                    end
                )

                self.text.see(pos)

                self.last_selection_start = pos
                self.last_selection_end = end

        except tk.TclError:
            pass

    # =============================================================
    # REPLACE
    # =============================================================

    def show_replace(self):
        window = tk.Toplevel(self.root)
        window.title("Find and Replace")
        window.resizable(False, False)

        frame = ttk.Frame(
            window,
            padding=10
        )
        frame.pack()

        ttk.Label(
            frame,
            text="Find:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        find_entry = ttk.Entry(
            frame,
            width=35
        )
        find_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            frame,
            text="Replace with:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        replace_entry = ttk.Entry(
            frame,
            width=35
        )
        replace_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text="Find Next",
            command=lambda: self.find_next(
                find_entry.get()
            )
        ).grid(
            row=2,
            column=0,
            pady=8
        )

        ttk.Button(
            frame,
            text="Replace",
            command=lambda: self.replace_current(
                find_entry.get(),
                replace_entry.get()
            )
        ).grid(
            row=2,
            column=1,
            pady=8
        )

        ttk.Button(
            frame,
            text="Replace All",
            command=lambda: self.replace_all(
                find_entry.get(),
                replace_entry.get()
            )
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            pady=5
        )

        find_entry.focus_set()

    def replace_current(self, find, replace):
        if not find:
            return

        start, end = self.get_selection_range()

        if not start or not end:
            self.find_next(find)
            return

        selected = self.text.get(
            start,
            end
        )

        if selected.lower() != find.lower():
            self.find_next(find)
            return

        self.text.delete(
            start,
            end
        )

        tag = self.create_format_tag(
            self.get_current_format()
        )

        self.text.insert(
            start,
            replace,
            tag
        )

        self.modified = True
        self.update_title()

    def replace_all(self, find, replace):
        if not find:
            return

        count = 0
        start = "1.0"

        while True:
            pos = self.text.search(
                find,
                start,
                stopindex=tk.END,
                nocase=True
            )

            if not pos:
                break

            end = self.text.index(
                f"{pos} + {len(find)} chars"
            )

            self.text.delete(
                pos,
                end
            )

            tag = self.create_format_tag(
                self.get_current_format()
            )

            self.text.insert(
                pos,
                replace,
                tag
            )

            start = self.text.index(
                f"{pos} + {len(replace)} chars"
            )

            count += 1

        if count:
            self.modified = True
            self.update_title()

            messagebox.showinfo(
                "Replace All",
                f"Replaced {count} occurrence(s)."
            )

    # =============================================================
    # PRINT
    # =============================================================

    def print_document(self):
        temp_txt = None

        try:
            if self.current_file:
                if self.current_file.lower().endswith(
                    ".txt"
                ):
                    print_file = self.current_file
                else:
                    # Create temporary text file
                    temp_txt = os.path.join(
                        os.path.dirname(
                            self.current_file
                        ),
                        "__poweredit_print.txt"
                    )

                    with open(
                        temp_txt,
                        "w",
                        encoding="utf-8"
                    ) as f:
                        f.write(
                            self.text.get(
                                "1.0",
                                "end-1c"
                            )
                        )

                    print_file = temp_txt

            else:
                temp_txt = os.path.join(
                    os.path.abspath("."),
                    "__poweredit_print.txt"
                )

                with open(
                    temp_txt,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(
                        self.text.get(
                            "1.0",
                            "end-1c"
                        )
                    )

                print_file = temp_txt

            if sys.platform.startswith("win"):
                os.startfile(
                    print_file,
                    "print"
                )

            elif sys.platform == "darwin":
                subprocess.run(
                    ["lp", print_file],
                    check=False
                )

            else:
                subprocess.run(
                    ["lp", print_file],
                    check=False
                )

        except Exception as exc:
            messagebox.showerror(
                "Print Error",
                f"Could not print the document.\n\n{exc}"

            )

        finally:
            if temp_txt and os.path.exists(
                temp_txt
            ):
                try:
                    os.remove(temp_txt)
                except OSError:
                    pass

    # =============================================================
    # CONTEXT MENU
    # =============================================================

    def show_context_menu(self, event):
        menu = tk.Menu(
            self.root,
            tearoff=False
        )

        menu.add_command(
            label="Undo",
            command=self.undo
        )

        menu.add_command(
            label="Redo",
            command=self.redo
        )

        menu.add_separator()

        menu.add_command(
            label="Cut",
            command=self.cut
        )

        menu.add_command(
            label="Copy",
            command=self.copy
        )

        menu.add_command(
            label="Paste",
            command=self.paste
        )

        menu.add_command(
            label="Select All",
            command=self.select_all
        )

        menu.add_separator()

        menu.add_command(
            label="Bold",
            command=self.toggle_bold
        )

        menu.add_command(
            label="Italic",
            command=self.toggle_italic
        )

        menu.add_command(
            label="Underline",
            command=self.toggle_underline
        )

        menu.tk_popup(
            event.x_root,
            event.y_root
        )

    # =============================================================
    # WINDOW / TITLE
    # =============================================================

    def update_title(self):
        if self.current_file:
            name = os.path.basename(
                self.current_file
            )
        else:
            name = "Untitled"

        marker = "*" if self.modified else ""

        self.root.title(
            f"{marker}{name} - PowerEdit"
        )

    def confirm_discard(self):
        if not self.modified:
            return True

        answer = messagebox.askyesnocancel(
            "PowerEdit",
            "The document has unsaved changes.\n\n"
            "Do you want to save them?"
        )

        if answer is None:
            return False

        if answer:
            return bool(
                self.save_document()
            )

        return True

    def on_close(self):
        if self.confirm_discard():
            self.root.destroy()

    # =============================================================
    # ABOUT
    # =============================================================

    def show_about(self):
        messagebox.showinfo(
            "About PowerEdit",
            "PowerEdit\n\n"
            "A WordPad-style Tkinter text editor.\n\n"
            "Supports TXT and basic RTF formatting."
        )


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":
    root = tk.Tk()

    try:
        style = ttk.Style()

        if "clam" in style.theme_names():
            style.theme_use("clam")

    except Exception:
        pass

    app = PowerEdit(root)

    root.mainloop()