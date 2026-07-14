#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""XP Classic theme colors and style configuration."""

# XP Classic Style Colors
BG   = '#ECE9D8'  # 3D Face
BG2  = '#D4D0C8'  # 3D Shadow
BG3  = '#FFFFFF'  # Window
FG   = '#000000'  # Button Text
ACCENT  = '#316AC5'  # Selection Blue
ACCENT2 = '#008000'  # Green
WARN    = '#FF0000'  # Red
ERR     = '#CC0000'
BORDER  = '#ACA899'  # 3D Dark Shadow
ENTRY_BG = '#FFFFFF'


def apply_theme(style):
    """Apply the XP Classic theme to a ttk.Style instance."""
    try:
        style.theme_use('winnative')
    except Exception:
        try:
            style.theme_use('classic')
        except Exception:
            try:
                style.theme_use('vista')
            except Exception:
                pass

    style.configure('.', background=BG, foreground=FG)
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=FG, font=('Tahoma', 9))
    style.configure('TLabelframe', background=BG, foreground=FG)
    style.configure('TButton', font=('Tahoma', 9), padding=4)
    style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=FG, font=('Tahoma', 9))
    style.configure('TScale', background=BG)
    style.configure('TCheckbutton', background=BG, foreground=FG, font=('Tahoma', 9))
    style.configure('TRadiobutton', background=BG, foreground=FG, font=('Tahoma', 9))
    style.configure('TSeparator', background=BORDER)
    style.configure('TProgressbar', background=ACCENT, troughcolor=BG2)
    style.configure('TNotebook', background=BG, borderwidth=1)
    style.configure('TNotebook.Tab', background=BG2, foreground=FG, font=('Tahoma', 9), padding=(14, 4))
    style.map('TNotebook.Tab', background=[('selected', BG)], foreground=[('selected', FG)])
    style.configure('Treeview', background=ENTRY_BG, foreground=FG, fieldbackground=ENTRY_BG, font=('Tahoma', 9))
    style.configure('Treeview.Heading', background=BG, foreground=FG, font=('Tahoma', 9, 'bold'))
    style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', '#FFFFFF')])
    style.map('Treeview.Heading', background=[('active', BG2)])
