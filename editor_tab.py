import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json

REQUIRED_COLS = (
    "command_name","command","expected","regex","negative",
    "wait_till","print_after","print_ahead_chars","message","retries"
)

class EditorTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        self.data = []

        bf = ttk.Frame(self.frame); bf.pack(fill="x")
        ttk.Button(bf, text="Load JSON", command=self.load_json).pack(side="left", padx=5, pady=5)
        ttk.Button(bf, text="Save JSON", command=self.save_json).pack(side="left", padx=5, pady=5)
        ttk.Button(bf, text="Add Command", command=self.add_command).pack(side="left", padx=5, pady=5)
        ttk.Button(bf, text="Duplicate", command=self.duplicate_row).pack(side="left", padx=5, pady=5)
        ttk.Button(bf, text="Delete", command=self.delete_row).pack(side="left", padx=5, pady=5)

        self.tree = ttk.Treeview(self.frame, columns=REQUIRED_COLS, show="headings", selectmode="browse")
        for col in REQUIRED_COLS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, stretch=True)
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.bind("<B1-Motion>", self.drag)
        self.tree.bind("<ButtonRelease-1>", self.drop)

        self.edit_frame = ttk.LabelFrame(self.frame, text="Edit Command")
        self.edit_frame.pack(fill="x", pady=6)

        self.edit_vars = {col: tk.StringVar() for col in REQUIRED_COLS}
        for i, col in enumerate(REQUIRED_COLS):
            r, c = divmod(i, 4)
            ttk.Label(self.edit_frame, text=col).grid(row=r, column=c*2, padx=5, pady=4, sticky="e")
            ttk.Entry(self.edit_frame, textvariable=self.edit_vars[col], width=18).grid(row=r, column=c*2+1, padx=5, pady=4, sticky="w")

        self.save_edit_btn = ttk.Button(self.edit_frame, text="Save Edit", command=self.save_edit, state="disabled")
        self.save_edit_btn.grid(row=(len(REQUIRED_COLS)//4)+1, column=0, columnspan=8, pady=6)

        self.dragging_index = None

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not file_path: return
        try:
            with open(file_path, "r", encoding="utf-8") as f: data = json.load(f)
            if not isinstance(data, list): raise ValueError("JSON root must be a list of objects.")
            fixed=[]
            for item in data:
                row={k:"" for k in REQUIRED_COLS}
                if isinstance(item, dict):
                    for k in REQUIRED_COLS:
                        if k in item: row[k]=str(item[k])
                fixed.append(row)
            self.data=fixed
            self.refresh_table()
            messagebox.showinfo("Loaded", f"Loaded {len(self.data)} commands.")
        except Exception as e:
            messagebox.showerror("Load Failed", f"Could not load JSON: {e}")

    def save_json(self):
        file_path=filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not file_path:return
        with open(file_path,"w",encoding="utf-8") as f: json.dump(self.data,f,indent=2)
        messagebox.showinfo("Saved", f"Commands saved to {file_path}")

    def add_command(self):
        self.data.append({
            "command_name":"New Command","command":"","expected":"","regex":"","negative":"",
            "wait_till":"1","print_after":"0","print_ahead_chars":"0","message":"","retries":"1"
        }); self.refresh_table()

    def duplicate_row(self):
        sel=self.tree.selection(); 
        if not sel:return
        idx=self.tree.index(sel[0]); self.data.insert(idx+1, dict(self.data[idx])); self.refresh_table()

    def delete_row(self):
        sel=self.tree.selection(); 
        if not sel:return
        idx=self.tree.index(sel[0]); del self.data[idx]; self.refresh_table()

    def on_row_select(self,_):
        sel=self.tree.selection(); 
        if not sel:return
        idx=self.tree.index(sel[0]); cmd=self.data[idx]
        for k,v in self.edit_vars.items(): v.set(cmd.get(k,""))
        self.save_edit_btn["state"]="normal"

    def save_edit(self):
        sel=self.tree.selection(); 
        if not sel:return
        idx=self.tree.index(sel[0])
        for k,v in self.edit_vars.items(): self.data[idx][k]=v.get()
        self.refresh_table(); self.save_edit_btn["state"]="disabled"

    def refresh_table(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for cmd in self.data: self.tree.insert("", "end", values=[cmd.get(c,"") for c in REQUIRED_COLS])

    def drag(self, event):
        row=self.tree.identify_row(event.y); 
        if row: self.dragging_index=self.tree.index(row)

    def drop(self, event):
        if self.dragging_index is None:return
        row=self.tree.identify_row(event.y)
        if row:
            new=self.tree.index(row)
            if new!=self.dragging_index:
                self.data.insert(new, self.data.pop(self.dragging_index)); self.refresh_table()
        self.dragging_index=None
