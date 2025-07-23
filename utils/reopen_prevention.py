import tkinter as tk

class WindowSingleton:
    _windows = {}

    @classmethod
    def get(cls, window_id, create_func):
        """
        window_id: egyedi string az ablakhoz (pl. 'armor_editor', 'skills_editor')
        create_func: függvény, ami létrehozza az ablakot (pl. lambda: tk.Toplevel(...))
        Visszatér: (win, created) ahol created True, ha új ablakot hozott létre.
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
