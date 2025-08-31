import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, re, queue
from export_utils import export_to_html


class RunTab:
    POLL_MS = 100  # ms between checking the connection_tab queue

    def __init__(self, notebook, editor_tab, connection_tab):
        self.frame = ttk.Frame(notebook)
        self.editor_tab = editor_tab
        self.connection_tab = connection_tab
        self.running = False
        self.stop_flag = False
        self.results = []
        self.iterations = tk.IntVar(value=1)

        # queue for background-to-UI logging
        self.ui_queue = queue.Queue()

        # --- Controls ---
        bf = ttk.Frame(self.frame)
        bf.pack(fill="x")
        ttk.Label(bf, text="Iterations:").pack(side="left")
        ttk.Entry(bf, textvariable=self.iterations, width=5).pack(side="left", padx=5)
        ttk.Button(bf, text="Run All", command=self.run_all).pack(side="left", padx=5)
        self.stop_button = ttk.Button(bf, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        self.export_button = ttk.Button(bf, text="Export HTML", command=self.export_html, state="disabled")
        self.export_button.pack(side="left", padx=5)

        # --- Results table ---
        cols = (
            "iteration","command_name","command","expected","regex","negative",
            "wait_till","print_after","print_ahead_chars","message","retries",
            "found","result"
        )
        self.tree = ttk.Treeview(self.frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, stretch=True)
        self.tree.pack(fill="both", expand=True)

        # Configure row colors
        self.tree.tag_configure("pending", background="#e2e3e5")   # gray
        self.tree.tag_configure("running", background="#fff3cd")   # yellow
        self.tree.tag_configure("pass", background="#d4edda")      # green
        self.tree.tag_configure("fail", background="#f8d7da")      # red

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
        ttk.Entry(search_frame, textvariable=self.search_var, width=25).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Find", command=self.search_log).pack(side="left")

        # Start polling
        self.frame.after(self.POLL_MS, self._poll_queues)

    # --- Logging helpers ---
    def _append_log_to_text(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self.log_text.insert("end", line)
        self.log_text.see("end")
        with open("session.log", "a", encoding="utf-8") as f:
            f.write(line)

    def enqueue_log(self, msg):
        self.ui_queue.put(msg)

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

    # --- Poll queues ---
    def _poll_queues(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                self._append_log_to_text(msg)
        except queue.Empty:
            pass

        if self.connection_tab and hasattr(self.connection_tab, "shared_queue"):
            try:
                while True:
                    line = self.connection_tab.shared_queue.get_nowait()
                    with self.connection_tab.history_lock:
                        self.connection_tab.history.append(line)
                    self._append_log_to_text(f"[LIVE] {line}")
            except queue.Empty:
                pass

        self.frame.after(self.POLL_MS, self._poll_queues)

    # --- Execution ---
    def run_all(self):
        if self.running:
            return
        if not self.connection_tab or not self.connection_tab.serial_conn or not self.connection_tab.serial_conn.is_open:
            messagebox.showerror("Not Connected", "Connect to a port first.")
            return

        self.results.clear()
        for r in self.tree.get_children():
            self.tree.delete(r)

        # preload all commands as pending (gray)
        for it in range(1, self.iterations.get() + 1):
            for cmd in list(self.editor_tab.data):
                row_values = (
                    it, cmd.get("command_name",""), cmd.get("command",""),
                    cmd.get("expected",""), cmd.get("regex",""), cmd.get("negative",""),
                    cmd.get("wait_till",""), cmd.get("print_after",""),
                    cmd.get("print_ahead_chars",""), cmd.get("message",""),
                    cmd.get("retries",""), "", "PENDING"
                )
                self.tree.insert("", "end", values=row_values, tags=("pending",))

        self.running = True
        self.stop_flag = False
        self.stop_button["state"] = "normal"
        self.export_button["state"] = "disabled"  # reset disabled

        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        conn = self.connection_tab
        first_command_done = False

        # iterate through all rows in order
        items = self.tree.get_children()
        for idx, item_id in enumerate(items, 1):
            if self.stop_flag:
                break

            values = list(self.tree.item(item_id, "values"))
            it = values[0]
            cmd = {
                "command_name": values[1],
                "command": values[2],
                "expected": values[3],
                "regex": values[4],
                "negative": values[5],
                "wait_till": values[6],
                "print_after": values[7],
                "print_ahead_chars": values[8],
                "message": values[9],
                "retries": values[10],
            }

            self.enqueue_log(f"[DEBUG] Starting command: {cmd['command_name']} ({cmd['command']})")
            self.tree.item(item_id, tags=("running",))
            self.tree.set(item_id, "result", "RUNNING")

            retries = int(cmd.get("retries", "1") or "1")
            if retries < 1:
                retries = 1

            final_result = "FAIL"
            found_text = ""

            for attempt in range(retries):
                if self.stop_flag:
                    break

                command = cmd.get("command", "")
                self.enqueue_log(f"[SEND] {command} (attempt {attempt+1}/{retries})")
                try:
                    conn.serial_conn.write((command + "\r\n").encode())
                except Exception as e:
                    self.enqueue_log(f"[ERROR] {e}")
                    continue

                with conn.history_lock:
                    start_idx = len(conn.history)

                timeout = float(cmd.get("wait_till", "1") or "1")
                if timeout < 0.1:
                    timeout = 1.0

                end_time = time.time() + timeout
                success = False
                while time.time() < end_time and not self.stop_flag:
                    with conn.history_lock:
                        new_lines = conn.history[start_idx:]
                    if new_lines:
                        response = "\n".join(new_lines)
                        found_text = response.strip()

                        expected = cmd.get("expected", "").strip()
                        regex = cmd.get("regex", "").strip()
                        negative = cmd.get("negative", "").strip()

                        if regex:
                            try:
                                if re.search(regex, response, re.MULTILINE):
                                    success = True
                            except re.error as e:
                                self.enqueue_log(f"[ERROR] Invalid regex: {e}")
                        elif expected:
                            if expected in response:
                                success = True
                        else:
                            if response:
                                success = True

                        if negative and negative in response:
                            success = False

                        if success:
                            final_result = "PASS"
                            break
                    time.sleep(0.05)

                if not success:
                    final_result = "FAIL"

                if final_result == "PASS":
                    break

            # update row color + result
            values[11] = found_text
            values[12] = final_result
            self.tree.item(item_id, values=values, tags=("pass" if final_result=="PASS" else "fail",))

            self.enqueue_log(f"[{final_result}] {cmd['command_name']} (Retries {retries})")
            self.results.append({"iteration": it, **cmd, "found": found_text, "result": final_result})

            if not first_command_done:
                self.frame.after(0, lambda: self.export_button.config(state="normal"))
                first_command_done = True

        self.running = False
        self.frame.after(0, lambda: self.stop_button.config(state="disabled"))
        self.enqueue_log("[INFO] Test execution finished.")

    def stop(self):
        self.stop_flag = True
        self.enqueue_log("[STOP] Execution stopped by user.")

    def export_html(self):
        if not self.results:
            messagebox.showerror("No Results", "No results to export.")
            return
        export_to_html(self.results)
