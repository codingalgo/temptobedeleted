import tkinter as tk
from tkinter import ttk
from connection_tab import ConnectionTab
from editor_tab import EditorTab
from run_tab import RunTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Serial Test Tool v3.1")
        self.geometry("1200x700")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs in correct order and wire them
        self.editor_tab = EditorTab(self.notebook)

        # RunTab initially without connection_tab
        self.run_tab = RunTab(self.notebook, self.editor_tab, None)

        # ConnectionTab created with reference to run_tab
        self.connection_tab = ConnectionTab(self.notebook, self.run_tab)

        # Back-fill connection_tab into run_tab
        self.run_tab.connection_tab = self.connection_tab

        # Add tabs to notebook
        self.notebook.add(self.connection_tab.frame, text="Connection")
        self.notebook.add(self.editor_tab.frame, text="Editor")
        self.notebook.add(self.run_tab.frame, text="Run & Export")


if __name__ == "__main__":
    app = App()
    app.mainloop()
