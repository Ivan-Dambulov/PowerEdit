import os
import re
import sys
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog

# Optional dependencies
try:
    from reportlab.lib.pagesizes import letter, legal, A3, A4, A5, elevenSeventeen, B5
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PowerEdit:
    DEFAULT_FONT = "Arial"
    DEFAULT_SIZE = 12
    DEFAULT_COLOR = "#000000"
    BULLET_PREFIX = "• "
    NUMBER_PREFIX_RE = re.compile(r"^(\d+)\.\s")

    def __init__(self, root):
        self.root = root
        self.root.title("PowerEdit")
        self.root.geometry("1300x600")
        self.root.minsize(750, 500)

        self.filename = None
        self.modified = False

        self.current_font = self.DEFAULT_FONT
        self.current_size = self.DEFAULT_SIZE
        self.current_color = self.DEFAULT_COLOR
        self.bold = False
        self.italic = False
        self.underline = False
        self.strike = False
        self.current_alignment = "left"
        self.page_size = "Letter"

        self.last_selection_start = None
        self.last_selection_end = None
        self.find_window = None
        self.format_tags = {}

        # Keep strong references
        self.image_refs = []
        self.image_objects = []
        self.table_objects = []

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

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_document)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_document)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_document)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export to PDF...", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Print...", accelerator="Ctrl+P", command=self.print_document)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=self.show_find)
        edit_menu.add_command(label="Replace", accelerator="Ctrl+H", command=self.show_replace)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        format_menu = tk.Menu(menubar, tearoff=False)
        format_menu.add_command(label="Bold", accelerator="Ctrl+B", command=self.toggle_bold)
        format_menu.add_command(label="Italic", accelerator="Ctrl+I", command=self.toggle_italic)
        format_menu.add_command(label="Underline", accelerator="Ctrl+U", command=self.toggle_underline)
        format_menu.add_command(label="Strikethrough", command=self.toggle_strike)
        format_menu.add_separator()
        format_menu.add_command(label="Bulleted List", command=self.toggle_bullets)
        format_menu.add_command(label="Numbered List", command=self.toggle_numbering)
        format_menu.add_command(label="Remove List Formatting", command=self.remove_list_formatting)
        format_menu.add_separator()
        format_menu.add_command(label="Align Left", command=lambda: self.set_alignment("left"))
        format_menu.add_command(label="Center", command=lambda: self.set_alignment("center"))
        format_menu.add_command(label="Align Right", command=lambda: self.set_alignment("right"))
        format_menu.add_separator()
        format_menu.add_command(label="Insert Image...", command=self.insert_image)
        format_menu.add_command(label="Insert Table...", command=self.insert_table)
        menubar.add_cascade(label="Format", menu=format_menu)

        # About
        about_menu = tk.Menu(menubar, tearoff=False)
        about_menu.add_command(label="About PowerEdit", command=self.show_about)
        menubar.add_cascade(label="About", menu=about_menu)

        self.root.config(menu=menubar)

    def show_about(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("About PowerEdit")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.geometry("300x340")

        dialog.update_idletasks()
        dialog.deiconify()
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(dialog, padding=25)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="PowerEdit", font=("Segoe UI", 18, "bold")).pack(pady=(0, 5))
        ttk.Label(frame, text="Version 1.0", font=("Segoe UI", 14)).pack(pady=(0, 15))

        description = (
            "A clean and modern rich-text editor\n"
            "Made with ❤️ using Python\n\n"
            "Simple. Fast. Focused."
        )
        ttk.Label(frame, text=description, justify="center", font=("Segoe UI", 14)).pack(pady=(0, 20))

        ttk.Label(frame, text="Author: Ivan Dambulov", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        ttk.Label(frame, text="www.ivand.eu", font=("Segoe UI", 14)).pack()

        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=(25, 0))

        dialog.wait_window()

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

        # Row 1
        tk.Label(row1, text="Font:").pack(side="left", padx=(2, 2))
        self.font_var = tk.StringVar(value=self.DEFAULT_FONT)
        self.font_combo = ttk.Combobox(row1, textvariable=self.font_var, width=18, state="readonly")
        self.font_combo["values"] = sorted(set(self.root.tk.call("font", "families")))
        self.font_combo.pack(side="left", padx=2)
        self.font_combo.bind("<<ComboboxSelected>>", self.font_changed)

        tk.Label(row1, text="Size:").pack(side="left", padx=(8, 2))
        self.size_var = tk.StringVar(value=str(self.DEFAULT_SIZE))
        self.size_combo = ttk.Combobox(
            row1, textvariable=self.size_var, width=5, state="readonly",
            values=("8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "28", "32", "36", "48", "72")
        )
        self.size_combo.pack(side="left", padx=2)
        self.size_combo.bind("<<ComboboxSelected>>", self.size_changed)

        self.bold_button = tk.Button(row1, text="B", width=3, font=("Arial", 10, "bold"),
                                     command=self.toggle_bold, relief="raised")
        self.bold_button.pack(side="left", padx=1)

        self.italic_button = tk.Button(row1, text="I", width=3, font=("Arial", 10, "italic"),
                                       command=self.toggle_italic, relief="raised")
        self.italic_button.pack(side="left", padx=1)

        self.underline_button = tk.Button(row1, text="U", width=3, font=("Arial", 10, "underline"),
                                          command=self.toggle_underline, relief="raised")
        self.underline_button.pack(side="left", padx=1)

        self.strike_button = tk.Button(row1, text="S", width=3, font=("Arial", 10),
                                       command=self.toggle_strike, relief="raised")
        self.strike_button.pack(side="left", padx=1)

        tk.Label(row1, text="Color:").pack(side="left", padx=(8, 2))

        self.color_button = tk.Button(
            row1,
            text="A",
            width=3,
            font=("Arial", 11, "bold"),
            relief="raised",
            bd=2,
            command=self.show_color_palette
        )
        self.color_button.pack(side="left", padx=2)

        # Initialize the visual look
        self.update_color_button()

        ttk.Button(row1, text="• Bullet List", command=self.toggle_bullets).pack(side="left", padx=2)
        ttk.Button(row1, text="1. Number List", command=self.toggle_numbering).pack(side="left", padx=2)
        ttk.Button(row1, text="No List", command=self.remove_list_formatting).pack(side="left", padx=2)
        ttk.Separator(row1, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(row1, text="Undo", command=self.undo).pack(side="left", padx=2)
        ttk.Button(row1, text="Redo", command=self.redo).pack(side="left", padx=2)



        # Row 2
        ttk.Label(row2, text="Page Size:").pack(side="left", padx=(4, 2))
        self.page_var = tk.StringVar(value="A4")
        page_combo = ttk.Combobox(
            row2, textvariable=self.page_var, width=10, state="readonly",
            values=("Letter", "Legal", "A4", "A5", "A3", "Tabloid", "Executive", "B5")
        )
        page_combo.pack(side="left", padx=2)
        page_combo.bind("<<ComboboxSelected>>", self.page_size_changed)

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)

        tk.Label(row2, text="Align text:").pack(side="left", padx=(2))
        ttk.Button(row2, text="Left", command=lambda: self.set_alignment("left")).pack(side="left", padx=2)
        ttk.Button(row2, text="Center", command=lambda: self.set_alignment("center")).pack(side="left", padx=2)
        ttk.Button(row2, text="Right", command=lambda: self.set_alignment("right")).pack(side="left", padx=2)

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)


        ttk.Button(row2, text="Find text", command=self.show_find).pack(side="left", padx=2)
        ttk.Button(row2, text="Replace text", command=self.show_replace).pack(side="left", padx=2)

        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Button(row2, text="Insert Image", command=self.insert_image).pack(side="left", padx=2)
        ttk.Button(row2, text="Insert Table", command=self.insert_table).pack(side="left", padx=2)
        ttk.Separator(row2, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Button(row2, text="Print", command=self.print_document).pack(side="left", padx=2)
        ttk.Button(row2, text="Export PDF", command=self.export_pdf).pack(side="left", padx=2)

    # ============================================================
    # EDITOR
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
            tabs=("2c",),
            bg="white",  # background stays white
            fg="black",  # text stays black
            insertbackground="black"  # cursor stays visible
        )
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.tag_configure("align_left", justify="left")
        self.text.tag_configure("align_center", justify="center")
        self.text.tag_configure("align_right", justify="right")

    def create_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w", bd=1, relief="sunken")
        status.pack(side="bottom", fill="x")

    # ============================================================
    # BINDINGS
    # ============================================================
    def create_bindings(self):
        self.root.bind_all("<Control-n>", lambda e: self.shortcut(self.new_document))
        self.root.bind_all("<Control-o>", lambda e: self.shortcut(self.open_document))
        self.root.bind_all("<Control-s>", lambda e: self.shortcut(self.save_document))
        self.root.bind_all("<Control-Shift-S>", lambda e: self.shortcut(self.save_as))
        self.root.bind_all("<Control-z>", lambda e: self.shortcut(self.undo))
        self.root.bind_all("<Control-y>", lambda e: self.shortcut(self.redo))
        self.root.bind_all("<Control-x>", lambda e: self.shortcut(self.cut))
        self.root.bind_all("<Control-c>", lambda e: self.shortcut(self.copy))
        self.root.bind_all("<Control-v>", lambda e: self.shortcut(self.paste))
        self.root.bind_all("<Control-a>", lambda e: self.shortcut(self.select_all))
        self.root.bind_all("<Control-f>", lambda e: self.shortcut(self.show_find))
        self.root.bind_all("<Control-h>", lambda e: self.shortcut(self.show_replace))
        self.root.bind_all("<Control-p>", lambda e: self.shortcut(self.print_document))
        self.root.bind_all("<Control-b>", lambda e: self.shortcut(self.toggle_bold))
        self.root.bind_all("<Control-i>", lambda e: self.shortcut(self.toggle_italic))
        self.root.bind_all("<Control-u>", lambda e: self.shortcut(self.toggle_underline))

        self.text.bind("<<Modified>>", self.on_modified)
        self.text.bind("<KeyRelease>", self.cursor_changed)
        self.text.bind("<ButtonRelease-1>", self.remember_selection)
        self.text.bind("<B1-Motion>", self.remember_selection)
        self.text.bind("<Return>", self.handle_return)
        self.text.bind("<Tab>", self.handle_tab)
        self.text.bind("<Key>", self.on_key_press)

        # Reliable double-click / right-click detection
        self.text.bind("<Double-Button-1>", self.on_double_click)
        self.text.bind("<Button-3>", self.on_right_click)

    def shortcut(self, func):
        func()
        return "break"

    def on_key_press(self, event=None):
        if event and event.char and event.char.isprintable():
            self.root.after_idle(self._tag_last_inserted_char)

    def _tag_last_inserted_char(self):
        try:
            start = self.text.index("insert - 1c")
            end = self.text.index("insert")
            if self.text.compare(start, ">=", "1.0"):
                fmt = {
                    "font": self.current_font, "size": self.current_size,
                    "color": self.current_color, "bold": self.bold,
                    "italic": self.italic, "underline": self.underline, "strike": self.strike
                }
                tag = self.create_format_tag(fmt)
                self.remove_format_tags(start, end)
                self.text.tag_add(tag, start, end)
        except tk.TclError:
            pass

    def on_double_click(self, event):
        self._handle_special_click(event)

    def on_right_click(self, event):
        self._handle_special_click(event)

    def _handle_special_click(self, event):
        """Most reliable way to detect clicks on images."""
        try:
            index = self.text.index(f"@{event.x},{event.y}")
            # Check for image names
            for name in self.text.image_names():
                if self.text.index(name) == index or self.text.compare(index, "==", name):
                    # Extract index from name "img_X"
                    if name.startswith("img_"):
                        idx = int(name.split("_")[1])
                        self.resize_image_dialog(idx)
                        return "break"
        except Exception:
            pass

    # ============================================================
    # FORMATTING CORE (unchanged logic)
    # ============================================================
    def get_selection_range(self):
        try:
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
            self.last_selection_start = start
            self.last_selection_end = end
            return start, end
        except tk.TclError:
            if self.last_selection_start and self.last_selection_end:
                return self.last_selection_start, self.last_selection_end
            return None, None

    def remember_selection(self, event=None):
        try:
            self.last_selection_start = self.text.index("sel.first")
            self.last_selection_end = self.text.index("sel.last")
        except tk.TclError:
            pass
        self.update_toolbar()

    def get_format_at(self, index):
        tags = self.text.tag_names(index)
        for tag in reversed(tags):
            if tag.startswith("fmt_") and tag in self.format_tags:
                return self.format_tags[tag].copy()
        # Untagged text uses the widget's real base defaults
        return {
            "font": self.DEFAULT_FONT,
            "size": self.DEFAULT_SIZE,
            "color": self.DEFAULT_COLOR,
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
        }

    def create_format_tag(self, fmt):
        family = re.sub(r"[^A-Za-z0-9]", "_", str(fmt["font"]))
        color = str(fmt["color"]).replace("#", "")
        styles = []
        if fmt["bold"]:
            styles.append("bold")
        if fmt["italic"]:
            styles.append("italic")
        style_string = " ".join(styles)

        tag_name = (f"fmt_{family}_{fmt['size']}_{color}_"
                    f"{int(fmt['bold'])}_{int(fmt['italic'])}_"
                    f"{int(fmt['underline'])}_{int(fmt['strike'])}")

        if tag_name not in self.format_tags:
            self.format_tags[tag_name] = fmt.copy()
            self.text.tag_configure(
                tag_name,
                font=(fmt["font"], fmt["size"], style_string),
                foreground=fmt["color"],
                underline=fmt["underline"],
                overstrike=fmt["strike"]
            )
        return tag_name

    def remove_format_tags(self, start, end):
        for tag in self.text.tag_names():
            if tag.startswith("fmt_"):
                self.text.tag_remove(tag, start, end)

    def apply_single_property_to_selection(self, property_name, value):
        start, end = self.get_selection_range()
        if start and end and self.text.compare(start, "<", end):
            try:
                start_index = self.text.index(start)
                end_index = self.text.index(end)
                pos = start_index
                while self.text.compare(pos, "<", end_index):
                    next_pos = self.text.index(f"{pos} + 1c")
                    fmt = self.get_format_at(pos)
                    fmt[property_name] = value
                    tag = self.create_format_tag(fmt)
                    self.remove_format_tags(pos, next_pos)
                    self.text.tag_add(tag, pos, next_pos)
                    pos = next_pos
                self.restore_selection(start_index, end_index)
                self.modified = True
                self.update_title()
                return True
            except tk.TclError:
                return False
        else:
            setattr(self, property_name if property_name != "color" else "current_color", value)
            if property_name == "font":
                self.current_font = value
            elif property_name == "size":
                self.current_size = value
            elif property_name == "color":
                self.current_color = value
            elif property_name == "bold":
                self.bold = value
            elif property_name == "italic":
                self.italic = value
            elif property_name == "underline":
                self.underline = value
            elif property_name == "strike":
                self.strike = value
            return False

    def restore_selection(self, start, end):
        try:
            self.text.tag_remove("sel", "1.0", tk.END)
            self.text.tag_add("sel", start, end)
            self.text.mark_set("insert", end)
            self.last_selection_start = start
            self.last_selection_end = end
        except tk.TclError:
            pass

    def font_changed(self, event=None):
        value = self.font_var.get().strip()
        if value:
            self.apply_single_property_to_selection("font", value)
        self.text.focus_set()
        self.update_toolbar()

    def size_changed(self, event=None):
        try:
            value = int(self.size_var.get())
            if value >= 1:
                self.apply_single_property_to_selection("size", value)
        except (ValueError, TypeError):
            pass
        self.text.focus_set()
        self.update_toolbar()

    def toggle_bold(self):
        start, end = self.get_selection_range()
        if start and end and self.text.compare(start, "<", end):
            value = not self.get_format_at(start)["bold"]
            self.apply_single_property_to_selection("bold", value)
            self.bold = value
        else:
            self.bold = not self.bold
            self.apply_single_property_to_selection("bold", self.bold)
        self.text.focus_set()
        self.update_toolbar()

    def toggle_italic(self):
        start, end = self.get_selection_range()
        if start and end and self.text.compare(start, "<", end):
            value = not self.get_format_at(start)["italic"]
            self.apply_single_property_to_selection("italic", value)
            self.italic = value
        else:
            self.italic = not self.italic
            self.apply_single_property_to_selection("italic", self.italic)
        self.text.focus_set()
        self.update_toolbar()

    def toggle_underline(self):
        start, end = self.get_selection_range()
        if start and end and self.text.compare(start, "<", end):
            value = not self.get_format_at(start)["underline"]
            self.apply_single_property_to_selection("underline", value)
            self.underline = value
        else:
            self.underline = not self.underline
            self.apply_single_property_to_selection("underline", self.underline)
        self.text.focus_set()
        self.update_toolbar()

    def toggle_strike(self):
        start, end = self.get_selection_range()
        if start and end and self.text.compare(start, "<", end):
            value = not self.get_format_at(start)["strike"]
            self.apply_single_property_to_selection("strike", value)
            self.strike = value
        else:
            self.strike = not self.strike
            self.apply_single_property_to_selection("strike", self.strike)
        self.text.focus_set()
        self.update_toolbar()

    def show_color_palette(self):
        """Show a modern color palette popup with reliable color swatches."""
        if hasattr(self, "_color_palette") and self._color_palette.winfo_exists():
            self._color_palette.destroy()

        palette = tk.Toplevel(self.root)
        self._color_palette = palette
        palette.title("Text Color")
        palette.transient(self.root)
        palette.resizable(False, False)
        palette.attributes("-topmost", True)

        # Position under the color button
        try:
            x = self.color_button.winfo_rootx()
            y = self.color_button.winfo_rooty() + self.color_button.winfo_height() + 4
            palette.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

        main = ttk.Frame(palette, padding=12)
        main.pack()

        def make_swatch(parent, color, row, col):
            """Create a solid color swatch that actually shows the color."""
            swatch = tk.Label(
                parent,
                width=3,
                height=1,
                bg=color,
                relief="raised",
                bd=1,
                cursor="hand2"
            )
            swatch.grid(row=row, column=col, padx=2, pady=2)

            # Click to apply
            swatch.bind("<Button-1>", lambda e, c=color: self._apply_palette_color(c, palette))

            # Nice hover effect
            def on_enter(e):
                swatch.config(relief="sunken")

            def on_leave(e):
                swatch.config(relief="raised")

            swatch.bind("<Enter>", on_enter)
            swatch.bind("<Leave>", on_leave)

            return swatch

        # ---------- Theme Colors ----------
        ttk.Label(main, text="Theme Colors", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=10, sticky="w", pady=(0, 6)
        )

        theme_colors = [
            "#000000", "#FFFFFF", "#FF0000", "#00B050", "#0070C0",
            "#7030A0", "#FFC000", "#C00000", "#00B0F0", "#002060"
        ]

        for i, color in enumerate(theme_colors):
            make_swatch(main, color, 1, i)

        # ---------- Standard Colors ----------
        ttk.Label(main, text="Standard Colors", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, columnspan=10, sticky="w", pady=(14, 6)
        )

        standard_colors = [
            "#FF6B6B", "#FF9F43", "#FECA57", "#1DD1A1", "#54A0FF",
            "#5F27CD", "#C8D6E5", "#8395A7", "#222F3D", "#576574",
            "#EE5A24", "#F79F1F", "#A3CB38", "#1289A7", "#D980FA",
            "#B53471", "#FDA7DF", "#ED4C67", "#5758BB", "#341F97",
            "#2F3542", "#747D8C", "#A4B0BE", "#DFE4EA", "#F1F2F6",
            "#FF3838", "#FF9FF3", "#18DCFF", "#7D5FFF", "#32FF7E"
        ]

        for i, color in enumerate(standard_colors):
            r = 3 + i // 10
            c = i % 10
            make_swatch(main, color, r, c)

        # ---------- More Colors ----------
        ttk.Separator(main, orient="horizontal").grid(
            row=7, column=0, columnspan=10, sticky="ew", pady=12
        )

        ttk.Button(
            main, text="More Colors...",
            command=lambda: self._open_full_color_dialog(palette)
        ).grid(row=8, column=0, columnspan=10)

        palette.bind("<Escape>", lambda e: palette.destroy())
        palette.focus_set()

    def update_color_button(self):
        """Make the toolbar button clearly show the current text color."""
        color = self.current_color
        self.color_button.configure(fg=color, bg="white")

        # Optional: make the background a light version of the color for better visibility
        # You can also just leave it white + colored "A"

    def _apply_palette_color(self, color, palette_window):
        """Apply color from palette and close it."""
        self.set_color(color)
        self.update_color_button()
        palette_window.destroy()

    def _open_full_color_dialog(self, palette_window):
        """Fallback to the classic color chooser."""
        palette_window.destroy()
        result = colorchooser.askcolor(
            title="Choose Text Color",
            parent=self.root,
            initialcolor=self.current_color
        )
        if result[1]:
            self.set_color(result[1])
            self.update_color_button()

    def set_color(self, color):
        if isinstance(color, tuple):
            color = color[1]
        if color:
            self.apply_single_property_to_selection("color", str(color))
            self.current_color = str(color)
            self.update_color_button()  # ← add this line
        self.text.focus_set()
        self.update_toolbar()

    # ============================================================
    # ALIGNMENT + LISTS (kept concise)
    # ============================================================
    def get_selected_paragraphs(self):
        start, end = self.get_selection_range()
        if not start or not end:
            return [self.text.index("insert linestart")]
        first = self.text.index(f"{start} linestart")
        last = self.text.index(f"{end} linestart") if self.text.compare(end, ">", f"{end} linestart") else self.text.index(f"{end} -1c linestart")
        paragraphs = []
        current = first
        while self.text.compare(current, "<=", last):
            paragraphs.append(current)
            nxt = self.text.index(f"{current} +1 line linestart")
            if self.text.compare(nxt, ">", last):
                break
            current = nxt
        return paragraphs

    def set_alignment(self, alignment):
        for start in self.get_selected_paragraphs():
            end = self.text.index(f"{start} lineend")
            for tag in ("align_left", "align_center", "align_right"):
                self.text.tag_remove(tag, start, f"{end}+1c")
            self.text.tag_add(f"align_{alignment}", start, f"{end}+1c")
        self.current_alignment = alignment
        self.modified = True
        self.update_title()
        self.text.focus_set()

    def line_text(self, line_start):
        return self.text.get(line_start, f"{line_start} lineend")

    def line_has_bullet(self, text):
        return text.startswith(self.BULLET_PREFIX)

    def line_has_number(self, text):
        return bool(self.NUMBER_PREFIX_RE.match(text))

    def remove_list_from_line(self, line_start):
        text = self.line_text(line_start)
        if text.startswith(self.BULLET_PREFIX):
            self.text.delete(line_start, f"{line_start}+{len(self.BULLET_PREFIX)}c")
            return
        match = self.NUMBER_PREFIX_RE.match(text)
        if match:
            self.text.delete(line_start, f"{line_start}+{len(match.group(0))}c")

    def add_bullet_to_line(self, line_start):
        if not self.line_has_bullet(self.line_text(line_start)):
            if self.line_has_number(self.line_text(line_start)):
                self.remove_list_from_line(line_start)
            self.text.insert(line_start, self.BULLET_PREFIX)

    def add_number_to_line(self, line_start, number):
        text = self.line_text(line_start)
        if self.line_has_bullet(text) or self.line_has_number(text):
            self.remove_list_from_line(line_start)
        self.text.insert(line_start, f"{number}. ")

    def toggle_bullets(self):
        paragraphs = self.get_selected_paragraphs()
        all_bullets = all(self.line_has_bullet(self.line_text(p)) for p in paragraphs)
        for p in paragraphs:
            if all_bullets:
                self.remove_list_from_line(p)
            else:
                self.add_bullet_to_line(p)
        self.modified = True
        self.update_title()
        self.text.focus_set()

    def toggle_numbering(self):
        paragraphs = self.get_selected_paragraphs()
        all_numbered = all(self.line_has_number(self.line_text(p)) for p in paragraphs)
        if all_numbered:
            for p in paragraphs:
                self.remove_list_from_line(p)
        else:
            for i, p in enumerate(paragraphs, 1):
                self.add_number_to_line(p, i)
        self.modified = True
        self.update_title()
        self.text.focus_set()

    def remove_list_formatting(self):
        for p in self.get_selected_paragraphs():
            self.remove_list_from_line(p)
        self.modified = True
        self.update_title()
        self.text.focus_set()

    def handle_return(self, event=None):
        insert = self.text.index("insert")
        line_start = self.text.index(f"{insert} linestart")
        current = self.line_text(line_start)

        if current.startswith(self.BULLET_PREFIX):
            if not current[len(self.BULLET_PREFIX):].strip():
                self.text.delete(line_start, f"{line_start}+{len(self.BULLET_PREFIX)}c")
                self.text.insert(insert, "\n")
            else:
                self.text.insert(insert, "\n" + self.BULLET_PREFIX)
            self.modified = True
            return "break"

        match = self.NUMBER_PREFIX_RE.match(current)
        if match:
            num = int(match.group(1))
            prefix = match.group(0)
            if not current[len(prefix):].strip():
                self.text.delete(line_start, f"{line_start}+{len(prefix)}c")
                self.text.insert(insert, "\n")
            else:
                self.text.insert(insert, f"\n{num+1}. ")
            self.modified = True
            return "break"

        self.text.insert(insert, "\n")
        self.modified = True
        return "break"

    def handle_tab(self, event=None):
        insert = self.text.index("insert")
        line_start = self.text.index(f"{insert} linestart")
        text = self.line_text(line_start)
        if self.line_has_bullet(text) or self.line_has_number(text):
            self.text.insert(line_start, "    ")
            self.modified = True
            return "break"

    # ============================================================
    # PAGE SIZE
    # ============================================================
    def page_size_changed(self, event=None):
        self.page_size = self.page_var.get()
        self.status_var.set(f"Page size: {self.page_size}")

    def get_pagesize(self):
        if not REPORTLAB_AVAILABLE:
            return (612, 792)
        mapping = {
            "Letter": letter,
            "Legal": legal,
            "A4": A4,
            "A5": A5,
            "A3": A3,
            "Tabloid": elevenSeventeen,
            "Executive": (7.25 * inch, 10.5 * inch),
            "B5": B5,
        }
        return mapping.get(self.page_size, letter)

    # ============================================================
    # IMAGE - most reliable version
    # ============================================================
    def insert_image(self):
        if not PIL_AVAILABLE:
            messagebox.showwarning("Image Support", "Pillow is required.\n\npip install Pillow")
            return

        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            original = Image.open(path)
            default_width = min(400, original.width)
            ratio = default_width / float(original.width)
            default_height = int(original.height * ratio)

            resized = original.resize((default_width, default_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized)

            image_index = len(self.image_objects)
            data = {
                "original": original,
                "photo": photo,
                "width": default_width,
                "height": default_height,
            }
            self.image_objects.append(data)
            self.image_refs.append(photo)

            name = f"img_{image_index}"
            self.text.image_create("insert", image=photo, name=name)
            self.text.insert("insert", "\n")

            self.modified = True
            self.update_title()
            self.status_var.set("Image inserted – double-click or right-click to resize")
        except Exception as exc:
            messagebox.showerror("Image Error", str(exc))

    def resize_image_dialog(self, image_index):
        if image_index >= len(self.image_objects):
            return

        data = self.image_objects[image_index]
        original = data["original"]

        dialog = tk.Toplevel(self.root)
        dialog.title("Resize Image")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        # Reliable way to avoid "window not viewable"
        dialog.update_idletasks()
        dialog.deiconify()
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(dialog, padding=20)
        frame.pack()

        ttk.Label(frame, text="Width (px):").grid(row=0, column=0, sticky="w", pady=6)
        width_var = tk.IntVar(value=data["width"])
        ttk.Spinbox(frame, from_=20, to=3000, textvariable=width_var, width=10).grid(row=0, column=1, padx=10)

        ttk.Label(frame, text="Height (px):").grid(row=1, column=0, sticky="w", pady=6)
        height_var = tk.IntVar(value=data["height"])
        ttk.Spinbox(frame, from_=20, to=3000, textvariable=height_var, width=10).grid(row=1, column=1, padx=10)

        keep_ratio = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Keep aspect ratio", variable=keep_ratio).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=8
        )

        def sync_height(*args):
            if keep_ratio.get():
                try:
                    w = width_var.get()
                    height_var.set(int(w * original.height / original.width))
                except Exception:
                    pass

        def sync_width(*args):
            if keep_ratio.get():
                try:
                    h = height_var.get()
                    width_var.set(int(h * original.width / original.height))
                except Exception:
                    pass

        width_var.trace_add("write", sync_height)
        height_var.trace_add("write", sync_width)

        def apply():
            try:
                new_w = max(20, width_var.get())
                new_h = max(20, height_var.get())
                resized = original.resize((new_w, new_h), Image.Resampling.LANCZOS)
                new_photo = ImageTk.PhotoImage(resized)

                data["photo"] = new_photo
                data["width"] = new_w
                data["height"] = new_h
                self.image_refs.append(new_photo)

                name = f"img_{image_index}"
                # Replace image
                try:
                    self.text.image_configure(name, image=new_photo)
                except tk.TclError:
                    # Fallback: delete and re-insert
                    idx = self.text.index(name)
                    self.text.delete(idx)
                    self.text.image_create(idx, image=new_photo, name=name)

                self.modified = True
                self.update_title()
                self.status_var.set(f"Image resized to {new_w}×{new_h}")
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Resize Error", str(exc))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0))
        ttk.Button(btn_frame, text="Apply", command=apply).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=6)

        dialog.wait_window()

    # ============================================================
    # TABLE - most reliable version
    # ============================================================
    def insert_table(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Insert Table")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.update_idletasks()
        dialog.deiconify()
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(dialog, padding=15)
        frame.pack()

        ttk.Label(frame, text="Rows:").grid(row=0, column=0, sticky="w", pady=4)
        rows_var = tk.IntVar(value=3)
        ttk.Spinbox(frame, from_=1, to=20, textvariable=rows_var, width=6).grid(row=0, column=1, padx=8)

        ttk.Label(frame, text="Columns:").grid(row=1, column=0, sticky="w", pady=4)
        cols_var = tk.IntVar(value=3)
        ttk.Spinbox(frame, from_=1, to=12, textvariable=cols_var, width=6).grid(row=1, column=1, padx=8)

        header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="First row as header", variable=header_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=8
        )

        def create():
            rows = max(1, rows_var.get())
            cols = max(1, cols_var.get())
            dialog.destroy()
            self._create_table_widget(rows, cols, header_var.get())

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text="Insert", command=create).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

        dialog.wait_window()

    def _create_table_widget(self, rows, cols, has_header=True, existing_data=None):
        table_frame = ttk.Frame(self.text, relief="solid", borderwidth=1, padding=3)

        entries = []
        for r in range(rows):
            row_entries = []
            for c in range(cols):
                is_header = has_header and r == 0
                entry = ttk.Entry(table_frame, width=14, font=("Segoe UI", 10, "bold" if is_header else "normal"))
                if existing_data and r < len(existing_data) and c < len(existing_data[r]):
                    entry.insert(0, existing_data[r][c])
                elif is_header:
                    entry.insert(0, f"Header {c+1}")
                if is_header:
                    entry.configure(background="#e8f0fe")
                entry.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                row_entries.append(entry)
            entries.append(row_entries)

        for c in range(cols):
            table_frame.columnconfigure(c, weight=1)

        table_index = len(self.table_objects)
        info = {
            "frame": table_frame,
            "entries": entries,
            "rows": rows,
            "cols": cols,
            "has_header": has_header
        }
        self.table_objects.append(info)

        # Most reliable: bind directly on the frame and every cell
        def open_edit(event=None, idx=table_index):
            self.edit_table_dialog(idx)

        table_frame.bind("<Double-Button-1>", open_edit)
        table_frame.bind("<Button-3>", open_edit)
        for row in entries:
            for cell in row:
                cell.bind("<Double-Button-1>", open_edit)
                cell.bind("<Button-3>", open_edit)

        self.text.insert("insert", "\n")
        self.text.window_create("insert", window=table_frame)
        self.text.insert("insert", "\n\n")

        self.modified = True
        self.update_title()
        self.status_var.set(f"Table {rows}×{cols} inserted – double-click or right-click to edit")

    def edit_table_dialog(self, table_index):
        if table_index >= len(self.table_objects) or self.table_objects[table_index] is None:
            return

        info = self.table_objects[table_index]
        current_data = [[cell.get() for cell in row] for row in info["entries"]]

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Table")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.update_idletasks()
        dialog.deiconify()
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(dialog, padding=15)
        frame.pack()

        ttk.Label(frame, text="Rows:").grid(row=0, column=0, sticky="w", pady=4)
        rows_var = tk.IntVar(value=info["rows"])
        ttk.Spinbox(frame, from_=1, to=20, textvariable=rows_var, width=6).grid(row=0, column=1, padx=8)

        ttk.Label(frame, text="Columns:").grid(row=1, column=0, sticky="w", pady=4)
        cols_var = tk.IntVar(value=info["cols"])
        ttk.Spinbox(frame, from_=1, to=12, textvariable=cols_var, width=6).grid(row=1, column=1, padx=8)

        header_var = tk.BooleanVar(value=info["has_header"])
        ttk.Checkbutton(frame, text="First row as header", variable=header_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=8
        )

        def apply():
            new_rows = max(1, rows_var.get())
            new_cols = max(1, cols_var.get())
            dialog.destroy()

            try:
                info["frame"].destroy()
            except Exception:
                pass

            self.table_objects[table_index] = None
            self._create_table_widget(new_rows, new_cols, header_var.get(), existing_data=current_data)
            self.status_var.set(f"Table updated to {new_rows}×{new_cols}")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btn_frame, text="Apply", command=apply).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)

        dialog.wait_window()

    # ============================================================
    # REST OF THE METHODS (Edit, Find, Document, PDF, Print...)
    # ============================================================
    def update_toolbar(self):
        try:
            start, end = self.get_selection_range()
            if start and end and self.text.compare(start, "<", end):
                fmt = self.get_format_at(start)
                self.font_var.set(fmt["font"])
                self.size_var.set(str(fmt["size"]))
                self.current_color = fmt["color"]
                self.bold = fmt["bold"]
                self.italic = fmt["italic"]
                self.underline = fmt["underline"]
                self.strike = fmt["strike"]
            else:
                self.font_var.set(self.current_font)
                self.size_var.set(str(self.current_size))

            self.bold_button.configure(relief="sunken" if self.bold else "raised")
            self.italic_button.configure(relief="sunken" if self.italic else "raised")
            self.underline_button.configure(relief="sunken" if self.underline else "raised")
            self.strike_button.configure(relief="sunken" if self.strike else "raised")
            self.color_button.configure(fg=self.current_color)
            self.update_status()
        except tk.TclError:
            pass

    def cursor_changed(self, event=None):
        try:
            fmt = self.get_format_at(self.text.index("insert"))
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

    def cut(self):
        self.copy()
        try:
            self.text.delete("sel.first", "sel.last")
            self.modified = True
        except tk.TclError:
            pass

    def copy(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text.get("sel.first", "sel.last"))
        except tk.TclError:
            pass

    def paste(self):
        """Paste with rich formatting using BeautifulSoup when HTML is available."""
        try:
            html = None

            # Try different clipboard formats (cross-platform)
            for fmt in ("HTML Format", "text/html", "text/html;charset=utf-8"):
                try:
                    html = self.root.clipboard_get(type=fmt)
                    if html and len(html) > 10:
                        break
                except tk.TclError:
                    continue

            if html and ("<" in html and ">" in html):
                self._paste_html_bs4(html)
            else:
                # Fallback to plain text
                text = self.root.clipboard_get()
                self.text.insert("insert", text)

            self.modified = True
            self.update_title()
            self.update_status()
        except tk.TclError:
            pass

    def _paste_html_bs4(self, html):
        """Parse HTML with BeautifulSoup and apply formatting."""
        try:
            from bs4 import BeautifulSoup
            from bs4.element import NavigableString, Tag
        except ImportError:
            messagebox.showwarning(
                "Missing Dependency",
                "BeautifulSoup is required for rich paste.\n\nInstall it with:\n  pip install beautifulsoup4"
            )
            # Fallback
            self.text.insert("insert", self.root.clipboard_get())
            return

        from html import unescape
        import re

        # Clean up Word/Outlook conditional comments and extra junk
        html = re.sub(r'<!--\[if.*?\]>.*?<!\[endif\]-->', '', html, flags=re.DOTALL)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "meta", "link", "title"]):
            tag.decompose()

        def get_style_from_tag(tag):
            """Extract formatting from a tag and its style attribute."""
            fmt = {
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": self.current_color,
                "size": self.current_size,
                "font": self.current_font,
            }

            name = tag.name.lower() if tag.name else ""

            # Semantic tags
            if name in ("b", "strong"):
                fmt["bold"] = True
            if name in ("i", "em"):
                fmt["italic"] = True
            if name == "u":
                fmt["underline"] = True
            if name in ("s", "strike", "del"):
                fmt["strike"] = True

            # Headings → bigger + bold
            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                fmt["bold"] = True
                sizes = {"h1": 24, "h2": 20, "h3": 16, "h4": 14, "h5": 12, "h6": 11}
                fmt["size"] = sizes.get(name, 14)

            # Inline style attribute
            style = tag.get("style", "")
            if style:
                style = style.lower()

                if "font-weight:bold" in style or "font-weight: bold" in style or "font-weight:700" in style:
                    fmt["bold"] = True
                if "font-style:italic" in style or "font-style: italic" in style:
                    fmt["italic"] = True
                if "text-decoration:underline" in style or "text-decoration: underline" in style:
                    fmt["underline"] = True
                if "text-decoration:line-through" in style:
                    fmt["strike"] = True

                # Color
                m = re.search(r'color\s*:\s*([^;]+)', style)
                if m:
                    color = m.group(1).strip().replace(" ", "")
                    if color.startswith("#") or color in ("red", "blue", "green", "black", "white", "gray", "grey"):
                        fmt["color"] = color

                # Font size
                m = re.search(r'font-size\s*:\s*(\d+)(?:px|pt)?', style)
                if m:
                    fmt["size"] = int(m.group(1))

                # Font family (basic)
                m = re.search(r'font-family\s*:\s*([^;]+)', style)
                if m:
                    font = m.group(1).split(",")[0].strip().strip("'\"")
                    if font and font.lower() not in ("inherit", "initial", "serif", "sans-serif", "monospace"):
                        fmt["font"] = font

            # <font> tag attributes (old HTML)
            if name == "font":
                if tag.get("color"):
                    fmt["color"] = tag["color"]
                if tag.get("size"):
                    try:
                        # HTML font size 1-7 → approximate pt
                        size_map = {1: 8, 2: 10, 3: 12, 4: 14, 5: 18, 6: 24, 7: 36}
                        fmt["size"] = size_map.get(int(tag["size"]), 12)
                    except Exception:
                        pass
                if tag.get("face"):
                    fmt["font"] = tag["face"].split(",")[0].strip()

            return fmt

        def walk(node, inherited_fmt=None):
            """Recursively walk the HTML tree and insert formatted text."""
            if inherited_fmt is None:
                inherited_fmt = {
                    "bold": False, "italic": False, "underline": False, "strike": False,
                    "color": self.current_color, "size": self.current_size, "font": self.current_font
                }

            if isinstance(node, NavigableString):
                text = str(node)
                # Normalize whitespace but keep single spaces
                text = re.sub(r'[ \t]+', ' ', text)
                if not text:
                    return

                start = self.text.index("insert")
                self.text.insert("insert", text)
                end = self.text.index("insert")

                tag_name = self.create_format_tag(inherited_fmt)
                self.remove_format_tags(start, end)
                self.text.tag_add(tag_name, start, end)
                return

            if not isinstance(node, Tag):
                return

            name = node.name.lower()

            # Block elements → insert newline before (except first)
            block_tags = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
                          "li", "tr", "section", "article", "header", "footer"}
            if name in block_tags:
                # Avoid double newlines
                current = self.text.get("insert-1c", "insert")
                if current and current != "\n":
                    self.text.insert("insert", "\n")

            if name == "br":
                self.text.insert("insert", "\n")
                return

            # Merge formatting
            current_fmt = inherited_fmt.copy()
            tag_fmt = get_style_from_tag(node)
            for k, v in tag_fmt.items():
                if k in ("bold", "italic", "underline", "strike"):
                    current_fmt[k] = current_fmt[k] or v
                else:
                    if v != self.current_color and v != self.current_size and v != self.current_font:
                        current_fmt[k] = v
                    elif k in ("color", "size", "font") and v:
                        current_fmt[k] = v

            # Recurse into children
            for child in node.children:
                walk(child, current_fmt)

            # Closing block element → extra newline sometimes helps
            if name in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
                current = self.text.get("insert-1c", "insert")
                if current and current != "\n":
                    self.text.insert("insert", "\n")

        # Start walking from body (or the whole soup if no body)
        root = soup.body if soup.body else soup
        walk(root)

    def select_all(self):
        self.text.tag_add("sel", "1.0", "end-1c")
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

    def show_find(self):
        self.show_find_replace(False)

    def show_replace(self):
        self.show_find_replace(True)

    def show_find_replace(self, replace_mode=False):
        if self.find_window:
            try:
                self.find_window.destroy()
            except tk.TclError:
                pass

        self.find_window = tk.Toplevel(self.root)
        self.find_window.title("Replace" if replace_mode else "Find")
        self.find_window.transient(self.root)
        self.find_window.resizable(False, False)

        frame = tk.Frame(self.find_window, padx=10, pady=10)
        frame.pack()

        tk.Label(frame, text="Find:").grid(row=0, column=0, sticky="w", pady=3)
        find_var = tk.StringVar()
        find_entry = ttk.Entry(frame, textvariable=find_var, width=35)
        find_entry.grid(row=0, column=1, padx=5, pady=3)

        replace_var = tk.StringVar()
        if replace_mode:
            tk.Label(frame, text="Replace:").grid(row=1, column=0, sticky="w", pady=3)
            ttk.Entry(frame, textvariable=replace_var, width=35).grid(row=1, column=1, padx=5, pady=3)

        def find_next():
            target = find_var.get()
            if not target:
                return
            start = self.text.index("insert")
            pos = self.text.search(target, start, stopindex=tk.END)
            if not pos:
                pos = self.text.search(target, "1.0", stopindex=tk.END)
            if pos:
                end = self.text.index(f"{pos}+{len(target)}c")
                self.text.tag_remove("sel", "1.0", tk.END)
                self.text.tag_add("sel", pos, end)
                self.text.mark_set("insert", end)
                self.text.see(pos)

        def replace_one():
            target = find_var.get()
            if not target:
                return
            try:
                start = self.text.index("sel.first")
                end = self.text.index("sel.last")
                if self.text.get(start, end) == target:
                    self.text.delete(start, end)
                    self.text.insert(start, replace_var.get())
                    self.modified = True
                find_next()
            except tk.TclError:
                find_next()

        def replace_all():
            target = find_var.get()
            if not target:
                return
            content = self.text.get("1.0", tk.END).replace(target, replace_var.get())
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.modified = True
            self.update_title()

        buttons = tk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(buttons, text="Find Next", command=find_next).pack(side="left", padx=3)
        if replace_mode:
            ttk.Button(buttons, text="Replace", command=replace_one).pack(side="left", padx=3)
            ttk.Button(buttons, text="Replace All", command=replace_all).pack(side="left", padx=3)
        ttk.Button(buttons, text="Close", command=self.find_window.destroy).pack(side="left", padx=3)

        find_entry.focus_set()
        self.find_window.bind("<Return>", lambda e: find_next())

    def confirm_save(self):
        if not self.modified:
            return True
        result = messagebox.askyesnocancel("Save Changes", "The document has been modified.\n\nDo you want to save your changes?")
        if result is None:
            return False
        if result:
            return self.save_document()
        return True

    def new_document(self):
        if not self.confirm_save():
            return
        self.text.delete("1.0", tk.END)
        self.filename = None
        self.modified = False
        self.format_tags.clear()
        self.image_refs.clear()
        self.image_objects.clear()
        self.table_objects.clear()
        self.current_font = self.DEFAULT_FONT
        self.current_size = self.DEFAULT_SIZE
        self.current_color = self.DEFAULT_COLOR
        self.bold = self.italic = self.underline = self.strike = False
        self.update_title()
        self.update_toolbar()
        self.text.focus_set()

    def open_document(self):
        if not self.confirm_save():
            return
        filename = filedialog.askopenfilename(
            title="Open Document",
            filetypes=[("Rich Text Format", "*.rtf"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", data)
            self.filename = filename
            self.modified = False
            self.update_title()
        except Exception as exc:
            messagebox.showerror("Open Error", str(exc))

    def save_document(self):
        if not self.filename:
            return self.save_as()
        return self.save_to_file(self.filename)

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save Document",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Rich Text Format", "*.rtf"), ("All Files", "*.*")]
        )
        if not filename:
            return False
        return self.save_to_file(filename)

    def save_to_file(self, filename):
        try:
            if filename.lower().endswith(".rtf"):
                success = self.save_as_rtf(filename)
            else:
                content = self.text.get("1.0", "end-1c")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                success = True

            if success:
                self.filename = filename
                self.modified = False
                self.update_title()
            return success
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))
            return False

    def export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showwarning("PDF Export", "Install reportlab:\n\npip install reportlab")
            return
        filename = filedialog.asksaveasfilename(
            title="Export to PDF", defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not filename:
            return
        try:
            self._write_pdf(filename)
            messagebox.showinfo("PDF Export", f"Saved as:\n{filename}")
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc))

    def _write_pdf(self, filename):
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
        )
        from reportlab.lib.units import inch
        from reportlab.lib.utils import ImageReader
        from io import BytesIO

        pagesize = self.get_pagesize()
        page_width = pagesize[0] - 1.5 * inch

        doc = SimpleDocTemplate(
            filename, pagesize=pagesize,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
            topMargin=0.75 * inch, bottomMargin=0.75 * inch
        )

        styles = getSampleStyleSheet()
        style_left = ParagraphStyle(
            'Left', parent=styles['Normal'],
            alignment=TA_LEFT, spaceAfter=6, leading=14
        )
        style_center = ParagraphStyle(
            'Center', parent=styles['Normal'],
            alignment=TA_CENTER, spaceAfter=6, leading=14
        )
        style_right = ParagraphStyle(
            'Right', parent=styles['Normal'],
            alignment=TA_RIGHT, spaceAfter=6, leading=14
        )

        # -------------------------------------------------
        # Collect images
        # -------------------------------------------------
        image_positions = {}
        for name in self.text.image_names():
            if name.startswith("img_"):
                try:
                    idx = int(name.split("_")[1])
                    if 0 <= idx < len(self.image_objects):
                        pos = self.text.index(name)
                        image_positions[pos] = self.image_objects[idx]
                except (ValueError, IndexError, tk.TclError):
                    continue

        story = []
        content = self.text.get("1.0", "end-1c")
        lines = content.split("\n")

        for line_idx, line in enumerate(lines):
            line_start = f"{line_idx + 1}.0"
            line_end = f"{line_idx + 1}.end"

            # ----- Images on this line -----
            images_on_line = []
            for pos, data in image_positions.items():
                if (self.text.compare(pos, ">=", line_start) and
                        self.text.compare(pos, "<=", line_end)):
                    images_on_line.append((pos, data))

            if images_on_line:
                images_on_line.sort(key=lambda x: self.text.index(x[0]))

                for pos, data in images_on_line:
                    try:
                        pil_img = data["original"].copy()
                        target_w = data["width"]
                        target_h = data["height"]

                        if target_w > page_width:
                            ratio = page_width / target_w
                            target_w = page_width
                            target_h = target_h * ratio

                        pil_img = pil_img.resize(
                            (int(target_w), int(target_h)),
                            Image.Resampling.LANCZOS
                        )

                        buffer = BytesIO()
                        pil_img.save(buffer, format="PNG")
                        buffer.seek(0)

                        rl_img = RLImage(
                            ImageReader(buffer),
                            width=target_w * 0.75,
                            height=target_h * 0.75
                        )
                        rl_img.hAlign = "CENTER"
                        story.append(rl_img)
                        story.append(Spacer(1, 8))
                    except Exception as e:
                        print(f"PDF image error: {e}")
                        continue
                continue

            # ----- Empty line -----
            if not line.strip():
                story.append(Spacer(1, 8))
                continue

            # ----- Alignment -----
            align = "left"
            for tag in self.text.tag_names(line_start):
                if tag.startswith("align_"):
                    align = tag.replace("align_", "")
                    break
            style = {
                "left": style_left,
                "center": style_center,
                "right": style_right
            }.get(align, style_left)

            # ----- Build rich text runs -----
            rich = []
            pos = 0
            while pos < len(line):
                index = f"{line_idx + 1}.{pos}"
                fmt = self.get_format_at(index)

                run_end = pos + 1
                while run_end < len(line):
                    if self.get_format_at(f"{line_idx + 1}.{run_end}") != fmt:
                        break
                    run_end += 1

                text = line[pos:run_end]
                text = (text.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))

                # Use embedded font (or safe fallback)
                safe_font = self._get_reportlab_font(
                    fmt["font"], fmt["bold"], fmt["italic"]
                )

                parts = []
                if fmt["underline"]:
                    parts.append("<u>")

                parts.append(
                    f'<font name="{safe_font}" size="{fmt["size"]}" color="{fmt["color"]}">'
                )
                parts.append(text)
                parts.append("</font>")

                if fmt["underline"]:
                    parts.append("</u>")

                rich.append("".join(parts))
                pos = run_end

            para_text = "".join(rich) or "&nbsp;"
            story.append(Paragraph(para_text, style))

        doc.build(story)

    def _get_reportlab_font(self, font_name, bold=False, italic=False):
        """
        Try to embed the real font. Falls back to Helvetica family if not found.
        """
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        import sys

        font_name = (font_name or "Arial").strip()
        key = f"{font_name}|{int(bold)}|{int(italic)}"

        if not hasattr(self, "_rl_font_cache"):
            self._rl_font_cache = {}

        if key in self._rl_font_cache:
            return self._rl_font_cache[key]

        candidates = {
            (False, False): [f"{font_name}.ttf", f"{font_name}.otf",
                             f"{font_name}-Regular.ttf", f"{font_name} Regular.ttf"],
            (True, False): [f"{font_name}bd.ttf", f"{font_name}-Bold.ttf",
                            f"{font_name} Bold.ttf", f"{font_name}b.ttf"],
            (False, True): [f"{font_name}i.ttf", f"{font_name}-Italic.ttf",
                            f"{font_name} Italic.ttf"],
            (True, True): [f"{font_name}bi.ttf", f"{font_name}-BoldItalic.ttf",
                           f"{font_name} Bold Italic.ttf", f"{font_name}z.ttf"],
        }

        font_dirs = []
        if sys.platform.startswith("win"):
            windir = os.environ.get("WINDIR", r"C:\Windows")
            font_dirs.append(os.path.join(windir, "Fonts"))
        elif sys.platform == "darwin":
            font_dirs.extend([
                "/Library/Fonts",
                "/System/Library/Fonts",
                os.path.expanduser("~/Library/Fonts")
            ])
        else:
            font_dirs.extend([
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts")
            ])

        registered_name = None
        for directory in font_dirs:
            if not os.path.isdir(directory):
                continue
            for root, dirs, files in os.walk(directory):
                files_lower = {f.lower(): f for f in files}
                for candidate in candidates[(bold, italic)]:
                    if candidate.lower() in files_lower:
                        full_path = os.path.join(root, files_lower[candidate.lower()])
                        try:
                            internal_name = f"Embed_{font_name}_{int(bold)}_{int(italic)}"
                            pdfmetrics.registerFont(TTFont(internal_name, full_path))
                            registered_name = internal_name
                            break
                        except Exception:
                            continue
                if registered_name:
                    break
            if registered_name:
                break

        if not registered_name:
            if "times" in font_name.lower() or "serif" in font_name.lower():
                registered_name = ("Times-BoldItalic" if bold and italic else
                                   "Times-Bold" if bold else
                                   "Times-Italic" if italic else "Times-Roman")
            elif "courier" in font_name.lower() or "mono" in font_name.lower():
                registered_name = ("Courier-BoldOblique" if bold and italic else
                                   "Courier-Bold" if bold else
                                   "Courier-Oblique" if italic else "Courier")
            else:
                registered_name = ("Helvetica-BoldOblique" if bold and italic else
                                   "Helvetica-Bold" if bold else
                                   "Helvetica-Oblique" if italic else "Helvetica")

        self._rl_font_cache[key] = registered_name
        return registered_name

    def save_as_rtf(self, filename):
        """Save document as real RTF with font, size, bold, italic, underline, color and alignment."""
        try:
            content = self.text.get("1.0", "end-1c")
            lines = content.split("\n")

            # Collect used fonts and colors
            fonts = {}
            colors = {"#000000": 0}  # black is always index 0
            font_id = 0
            color_id = 1

            # First pass – collect fonts & colors
            for line_idx, line in enumerate(lines):
                for pos in range(len(line) + 1):
                    index = f"{line_idx + 1}.{pos}"
                    try:
                        fmt = self.get_format_at(index)
                    except Exception:
                        continue
                    f = fmt["font"]
                    if f not in fonts:
                        fonts[f] = font_id
                        font_id += 1
                    c = fmt["color"].upper()
                    if c not in colors:
                        colors[c] = color_id
                        color_id += 1

            # Build RTF header
            rtf = [r"{\rtf1\ansi\deff0"]

            # Font table
            rtf.append(r"{\fonttbl")
            for name, fid in fonts.items():
                rtf.append(rf"{{\f{fid}\fnil\fcharset0 {name};}}")
            rtf.append("}")

            # Color table
            rtf.append(r"{\colortbl;")
            sorted_colors = sorted(colors.items(), key=lambda x: x[1])
            for color, cid in sorted_colors:
                if cid == 0:
                    continue
                color = color.lstrip("#")
                if len(color) == 6:
                    r = int(color[0:2], 16)
                    g = int(color[2:4], 16)
                    b = int(color[4:6], 16)
                    rtf.append(rf"\red{r}\green{g}\blue{b};")
            rtf.append("}")

            rtf.append(r"\viewkind4\uc1")

            # Second pass – write content with alignment
            for line_idx, line in enumerate(lines):
                if line_idx > 0:
                    rtf.append(r"\par")

                # ----- Alignment detection -----
                line_start = f"{line_idx + 1}.0"
                align = "left"
                for tag in self.text.tag_names(line_start):
                    if tag.startswith("align_"):
                        align = tag.replace("align_", "")
                        break

                if align == "center":
                    rtf.append(r"\qc ")
                elif align == "right":
                    rtf.append(r"\qr ")
                else:
                    rtf.append(r"\ql ")  # left (default)

                # ----- Character formatting -----
                pos = 0
                while pos < len(line):
                    index = f"{line_idx + 1}.{pos}"
                    fmt = self.get_format_at(index)

                    # Find run length
                    run_end = pos + 1
                    while run_end < len(line):
                        if self.get_format_at(f"{line_idx + 1}.{run_end}") != fmt:
                            break
                        run_end += 1

                    text = line[pos:run_end]

                    fid = fonts.get(fmt["font"], 0)
                    cid = colors.get(fmt["color"].upper(), 0)
                    fs = int(fmt["size"] * 2)  # RTF uses half-points

                    controls = [rf"\f{fid}", rf"\fs{fs}", rf"\cf{cid}"]
                    if fmt["bold"]:
                        controls.append(r"\b")
                    if fmt["italic"]:
                        controls.append(r"\i")
                    if fmt["underline"]:
                        controls.append(r"\ul")

                    rtf.append("".join(controls) + " ")

                    # Escape special RTF characters
                    text = (text.replace("\\", r"\\")
                            .replace("{", r"\{")
                            .replace("}", r"\}"))
                    rtf.append(text)

                    # Turn formatting off
                    if fmt["bold"]:
                        rtf.append(r"\b0")
                    if fmt["italic"]:
                        rtf.append(r"\i0")
                    if fmt["underline"]:
                        rtf.append(r"\ul0")

                    pos = run_end

            rtf.append("}")

            with open(filename, "w", encoding="utf-8") as f:
                f.write("".join(rtf))

            return True
        except Exception as exc:
            messagebox.showerror("RTF Save Error", str(exc))
            return False

    def print_document(self):
        content = self.text.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Print", "There is nothing to print.")
            return

        if not REPORTLAB_AVAILABLE:
            messagebox.showinfo(
                "Print",
                "Formatted printing requires reportlab.\n\nInstall it with:\n    pip install reportlab"
            )
            return

        # First create the temporary PDF
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_path = tmp.name
            self._write_pdf(pdf_path)
        except Exception as exc:
            messagebox.showerror("Print Error", f"Could not create PDF:\n{exc}")
            return

        # Show printer selection dialog
        self._show_print_dialog(pdf_path)

    def _show_print_dialog(self, pdf_path):
        """Modern cross-platform printer selection dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Print")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.geometry("420x280")

        dialog.update_idletasks()
        dialog.deiconify()
        try:
            dialog.wait_visibility()
            dialog.grab_set()
        except tk.TclError:
            pass

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select Printer", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # List of printers
        printers = self._get_printers()
        printer_var = tk.StringVar()

        if printers:
            printer_var.set(printers[0])  # default to first
        else:
            printers = ["No printers found"]

        printer_combo = ttk.Combobox(
            frame,
            textvariable=printer_var,
            values=printers,
            state="readonly",
            width=45
        )
        printer_combo.pack(fill="x", pady=(0, 15))

        # Copies
        copies_frame = ttk.Frame(frame)
        copies_frame.pack(fill="x", pady=(5, 15))
        ttk.Label(copies_frame, text="Number of copies:").pack(side="left")
        copies_var = tk.IntVar(value=1)
        ttk.Spinbox(copies_frame, from_=1, to=99, textvariable=copies_var, width=5).pack(side="left", padx=10)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

        def do_print():
            selected = printer_var.get()
            if selected == "No printers found" or not selected:
                messagebox.showwarning("Print", "No printer selected.")
                return

            copies = max(1, copies_var.get())
            dialog.destroy()
            self._send_to_printer(pdf_path, selected, copies)

        ttk.Button(btn_frame, text="Print", command=do_print).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)

        # Also clean the temp file if user cancels
        def on_close():
            self._safe_unlink(pdf_path)
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
        dialog.wait_window()

    def _get_printers(self):
        """Return a list of available printers (cross-platform)."""
        printers = []
        system = sys.platform

        try:
            if system.startswith("win"):
                # Windows
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Printer | Select-Object -ExpandProperty Name"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    printers = [line.strip() for line in result.stdout.splitlines() if line.strip()]

            else:
                # Linux & macOS
                result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True, timeout=8)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.strip():
                            # Format is usually: "PrinterName accepting requests ..."
                            name = line.split()[0]
                            printers.append(name)
        except Exception:
            pass

        return printers

    def _send_to_printer(self, pdf_path, printer_name, copies=1):
        """Send the PDF to the selected printer."""
        system = sys.platform
        success = False

        try:
            if system.startswith("win"):
                # Windows – use PowerShell
                for _ in range(copies):
                    cmd = [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f'Start-Process -FilePath "{pdf_path}" -Verb PrintTo -ArgumentList "{printer_name}" -WindowStyle Hidden -ErrorAction SilentlyContinue'
                    ]
                    # Alternative more reliable method:
                    cmd2 = [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f'''
                        $printer = "{printer_name}"
                        Start-Process -FilePath "{pdf_path}" -Verb Print -WindowStyle Hidden
                        '''
                    ]
                    result = subprocess.run(cmd2, capture_output=True, text=True, timeout=20)
                    if result.returncode == 0:
                        success = True

            else:
                # Linux & macOS – use lp
                cmd = ["lp", "-d", printer_name, "-n", str(copies), pdf_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    success = True

            if success:
                messagebox.showinfo("Print", f"Document sent to printer:\n{printer_name}")
            else:
                # Final fallback
                if system.startswith("win"):
                    os.startfile(pdf_path)
                else:
                    subprocess.run(["xdg-open" if system != "darwin" else "open", pdf_path])
                messagebox.showinfo(
                    "Print",
                    "Could not send directly to the selected printer.\n"
                    "The PDF has been opened — please print manually."
                )

        except Exception as exc:
            messagebox.showerror("Print Error", f"Failed to print:\n{exc}")

        finally:
            # Clean up later
            self.root.after(30000, lambda: self._safe_unlink(pdf_path))

    def _safe_unlink(self, path):
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass

    def on_modified(self, event=None):
        try:
            if self.text.edit_modified():
                self.modified = True
                self.update_title()
                self.text.edit_modified(False)
        except tk.TclError:
            pass

    def update_title(self):
        name = os.path.basename(self.filename) if self.filename else "Untitled"
        self.root.title(f"{'* ' if self.modified else ''}{name} - PowerEdit")

    def update_status(self):
        try:
            line, col = self.text.index("insert").split(".")
            words = len(self.text.get("1.0", "end-1c").split())
            self.status_var.set(f"Line {line}, Column {int(col)+1}    Words: {words}")
        except tk.TclError:
            pass

    def exit_application(self):
        if self.confirm_save():
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PowerEdit(root)
    root.mainloop()