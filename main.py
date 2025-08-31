import tkinter as tk
from tkinter import ttk
from connection_tab import ConnectionTab
from editor_tab import EditorTab
from run_tab import RunTab

class TestManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QA Test Manager v3.0")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.editor_tab = EditorTab(self.notebook)
        self.run_tab = RunTab(self.notebook, self.editor_tab, None)
        self.connection_tab = ConnectionTab(self.notebook, self.run_tab)

        self.notebook.add(self.connection_tab.frame, text="Connection")
        self.notebook.add(self.editor_tab.frame, text="Editor")
        self.notebook.add(self.run_tab.frame, text="Run & Export")

        # Link back run_tab to connection_tab after init
        self.run_tab.connection_tab = self.connection_tab

if __name__ == "__main__":
    root = tk.Tk()
    app = TestManagerApp(root)
    root.mainloop()
