import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, re
from export_utils import export_to_html


class RunTab:
    def __init__(self, notebook, editor_tab, connection_tab):
        self.frame = ttk.Frame(notebook)
        self.editor_tab = editor_tab
        self.connection_tab = connection_tab
        self.running = False
        self.stop_flag = False
        self.results = []
        self.iterations = tk.IntVar(value=1)

        # --- Control buttons ---
        bf = ttk.Frame(self.frame)
        bf.pack(fill="x")
        ttk.Label(bf, text="Iterations:").pack(side="left")
        ttk.Entry(bf, textvariable=self.iterations, width=5).pack(side="left", padx=5)
        ttk.Button(bf, text="Run All", command=self.run_all).pack(side="left", padx=5)
        self.stop_button = ttk.Button(
            bf, text="Stop", command=self.stop, state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        self.export_button = ttk.Button(
            bf, text="Export HTML", command=self.export_html, state="disabled"
        )
        self.export_button.pack(side="left", padx=5)

        # --- Results table ---
        cols = (
            "iteration",
            "command_name",
            "command",
            "expected",
            "regex",
            "negative",
            "wait_till",
            "print_after",
            "print_ahead_chars",
            "message",
            "retries",
            "found",
            "result",
        )
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, stretch=True)
        self.tree.pack(fill="both", expand=True)

        # --- Live logs ---
        log_frame = ttk.LabelFrame(self.frame, text="Live Logs")
        log_frame.pack(fill="both", expand=True, pady=6)

        self.log_text = tk.Text(log_frame, wrap="word", height=12)
        self.log_text.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text["yscrollcommand"] = scrollbar.set

        # Search
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill="x")
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=25).pack(
            side="left", padx=5
        )
        ttk.Button(search_frame, text="Find", command=self.search_log).pack(
            side="left"
        )

    # --- Logging ---
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self.log_text.insert("end", line)
        self.log_text.see("end")
        with open("session.log", "a", encoding="utf-8") as f:
            f.write(line)

    def search_log(self):
        self.log_text.tag_remove("search", "1.0", "end")
        term = self.search_var.get()
        if not term:
            return
        start = self.log_text.search(term, "1.0", "end")
        if start:
            end = f"{start}+{len(term)}c"
            self.log_text.tag_add("search", start, end)
            self.log_text.tag_config("search", background="yellow")
            self.log_text.see(start)

    # --- Execution ---
    def run_all(self):
        if self.running:
            return
        if not self.connection_tab.serial_conn or not self.connection_tab.serial_conn.is_open:
            messagebox.showerror("Not Connected", "Connect to a port first.")
            return

        self.results.clear()
        for r in self.tree.get_children():
            self.tree.delete(r)

        self.running = True
        self.stop_flag = False
        self.stop_button["state"] = "normal"
        self.export_button["state"] = "disabled"

        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        for it in range(1, self.iterations.get() + 1):
            for cmd in self.editor_tab.data:
                if self.stop_flag:
                    break

                retries = int(cmd.get("retries", "1") or "1")
                final_result = "FAIL"
                found_text = ""

                for r in range(retries):
                    if self.stop_flag:
                        break
                    command = cmd.get("command", "")
                    self.log(f"[SEND] {command}")
                    try:
                        self.connection_tab.serial_conn.write(
                            (command + "\r\n").encode()
                        )
                    except Exception as e:
                        self.log(f"[ERROR] {e}")
                        continue

                    # --- FIX: Read until timeout ---
                    timeout = float(cmd.get("wait_till", "1") or "1")
                    end_time = time.time() + timeout
                    lines = []
                    while time.time() < end_time:
                        try:
                            chunk = self.connection_tab.serial_conn.readline().decode(errors="ignore").strip()
                            if chunk:
                                lines.append(chunk)
                                self.log(f"[RECV] {chunk}")
                        except Exception:
                            break
                    response = "\n".join(lines)
                    found_text = response.strip()

                    # Evaluation
                    expected = cmd.get("expected", "").strip()
                    regex = cmd.get("regex", "").strip()
                    negative = cmd.get("negative", "").strip()

                    final_result = "FAIL"  # default
                    if regex:
                        if re.search(regex, response):
                            final_result = "PASS"
                    elif expected:
                        if expected in response:
                            final_result = "PASS"
                    else:
                        # if nothing to check, consider pass
                        if response:
                            final_result = "PASS"

                    if negative and negative in response:
                        final_result = "FAIL"

                    if final_result == "PASS":
                        break  # no need more retries

                self.log(
                    f"[{final_result}] {cmd.get('command_name','')} (Retries {retries})"
                )
                self.results.append(
                    {
                        "iteration": it,
                        **cmd,
                        "found": found_text,
                        "result": final_result,
                    }
                )
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        it,
                        cmd.get("command_name", ""),
                        cmd.get("command", ""),
                        cmd.get("expected", ""),
                        cmd.get("regex", ""),
                        cmd.get("negative", ""),
                        cmd.get("wait_till", ""),
                        cmd.get("print_after", ""),
                        cmd.get("print_ahead_chars", ""),
                        cmd.get("message", ""),
                        cmd.get("retries", ""),
                        found_text,
                        final_result,
                    ),
                )

            if self.stop_flag:
                break

        self.running = False
        self.stop_button["state"] = "disabled"
        self.export_button["state"] = "normal"

    def stop(self):
        self.stop_flag = True
        self.log("[STOP] Execution stopped by user.")

    def export_html(self):
        if not self.results:
            messagebox.showerror("No Results", "No results to export.")
            return
        export_to_html(self.results)
