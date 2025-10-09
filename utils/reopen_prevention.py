"""
Window singleton pattern implementation for preventing duplicate windows.

This module provides the WindowSingleton class to ensure only one instance
of each window type is open at a time in the UI.
"""

import tkinter as tk

class WindowSingleton:
    """
    Manages singleton windows to prevent duplicate window instances.
    
    Ensures that only one instance of each window type exists at a time.
    If a window already exists, it is brought to front instead of creating a new one.
    
    Class Attributes:
        _windows (dict): Dictionary tracking open windows by ID
    """
    _windows = {}

    @classmethod
    def get(cls, window_id, create_func):
        """
        Get or create a singleton window.
        
        Args:
            window_id (str): Unique identifier for the window (e.g. 'armor_editor', 'skills_editor')
            create_func (callable): Function that creates the window (e.g. lambda: tk.Toplevel())
            
        Returns:
            tuple: (window, created) where created is True if a new window was created
        """
        win = cls._windows.get(window_id)
        if win is not None and win.winfo_exists():
            win.deiconify()
            win.lift()
            win.focus_force()
            return win, False
        win = create_func()
        cls._windows[window_id] = win
        def on_close():
            cls._windows[window_id] = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)
        return win, True
