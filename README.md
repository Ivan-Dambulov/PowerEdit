# PowerEdit

**PowerEdit** is a lightweight desktop text editor built with **Python and Tkinter**, designed to provide a familiar, WordPad-style editing experience while keeping the implementation simple and transparent.

The project focuses on practical desktop application development: rich-text formatting, document management, keyboard-driven workflows, basic RTF support, and a responsive two-row toolbar.

---

## Features

### Rich Text Editing

* Font family selection
* Font size selection
* Text color selection
* **Bold**, *Italic*, <u>Underline</u>, and ~~Strike-through~~
* Paragraph alignment:

  * Left
  * Center
  * Right
* Persistent formatting when editing existing text
* Property-specific formatting, allowing individual attributes to change without unintentionally overwriting other formatting

### Lists

* Bulleted lists
* Numbered lists
* Automatic numbering
* Continue lists when pressing `Enter`
* Exit a list by pressing `Enter` on an empty list item
* Remove list formatting
* Basic indentation with `Tab`

### Document Management

* New document
* Open existing files
* Save
* Save As
* Basic `.txt` support
* Basic `.rtf` support
* Unsaved-change detection
* Document title updates

### Editing

* Undo / Redo
* Cut / Copy / Paste
* Select All
* Find
* Find & Replace
* Keyboard shortcuts

### Printing

* Basic document printing through the system's `lpr` command on Linux environments.

---

## Interface

PowerEdit uses a compact two-row toolbar to keep commonly used editing operations accessible without taking excessive screen space.

The interface is intentionally familiar for users who have worked with classic Windows text editors such as WordPad.

---

## Keyboard Shortcuts

| Shortcut           | Action       |
| ------------------ | ------------ |
| `Ctrl + N`         | New document |
| `Ctrl + O`         | Open         |
| `Ctrl + S`         | Save         |
| `Ctrl + Shift + S` | Save As      |
| `Ctrl + Z`         | Undo         |
| `Ctrl + Y`         | Redo         |
| `Ctrl + X`         | Cut          |
| `Ctrl + C`         | Copy         |
| `Ctrl + V`         | Paste        |
| `Ctrl + A`         | Select All   |
| `Ctrl + F`         | Find         |
| `Ctrl + H`         | Replace      |
| `Ctrl + P`         | Print        |
| `Ctrl + B`         | Bold         |
| `Ctrl + I`         | Italic       |
| `Ctrl + U`         | Underline    |

---

## Technology

PowerEdit is intentionally built with Python's standard GUI stack:

* **Python 3**
* **Tkinter**
* **Tkinter ttk**
* Standard Python libraries
* Basic RTF parsing and generation

No large external GUI framework is required.

---

## Project Structure

```text
PowerEdit/
├── main.py
├── README.md
└── ...
```

The current implementation is intentionally kept compact so the application logic remains easy to understand and extend.

---

## Design Approach

One of the more interesting implementation details is formatting persistence.

Instead of treating formatting as a single global editor state, PowerEdit stores formatting properties independently:

```text
Font
Size
Color
Bold
Italic
Underline
Strike-through
```

This allows an operation such as changing the font size to modify **only the size** of selected text while preserving its existing font, color, and styles.

This approach also makes the editor easier to extend with additional formatting features in the future.

---

## RTF Support

PowerEdit includes basic RTF import and export functionality.

The implementation supports common formatting concepts such as:

* Font information
* Font size
* Text color
* Bold
* Italic
* Underline
* Strike-through
* Paragraph alignment
* Basic list representation

The RTF implementation is intentionally lightweight rather than attempting to reproduce the complete RTF specification.

For complex documents created by full-featured word processors, compatibility may therefore vary.

---

## Current Status

PowerEdit is an actively developed desktop-editor project.

The current focus is on improving:

* RTF compatibility
* Formatting consistency
* List behavior
* Document handling
* Cross-platform behavior
* Overall editor usability

---

## Future Improvements

Potential areas for future development include:

* More complete RTF support
* Improved document formatting preservation
* Better printing and print preview
* Image insertion
* Hyperlinks
* Tables
* Page layout
* Customizable toolbars
* Improved cross-platform packaging
* Automated tests

---

## Why This Project?

PowerEdit started as a practical project for exploring desktop GUI development with Python.

Rather than building a minimal text area with a few buttons, the goal is to understand the problems that appear in a real editor:

* Managing formatting state
* Preserving user formatting
* Handling selections correctly
* Implementing list behavior
* Managing document state
* Importing and exporting formatted documents
* Connecting UI actions with keyboard workflows

These details make a text editor considerably more interesting than a basic CRUD-style desktop application.

---


If you find the project useful or have ideas for improvements, feel free to open an issue or submit a pull request.
