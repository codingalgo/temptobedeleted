import tkinter as tk
from tkinter import ttk, messagebox
import threading

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


class ConnectionTab:
    def __init__(self, notebook, run_tab_ref):
        self.frame = ttk.Frame(notebook)
        self.serial_conn = None
        self.run_tab_ref = run_tab_ref
        self.reader_thread = None
        self.stop_reader = False
        self.shared_buffer = []  # <--- NEW: buffer for RunTab to read responses

        ttk.Label(self.frame, text="Select Port:").pack(pady=5)

        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(
            self.frame, textvariable=self.port_var, width=32, state="readonly"
        )
        self._refresh_ports()
        self.port_dropdown.pack(pady=5)

        self.connect_button = ttk.Button(
            self.frame, text="Connect", command=self.connect
        )
        self.connect_button.pack(pady=5)

        self.disconnect_button = ttk.Button(
            self.frame, text="Disconnect", command=self.disconnect, state="disabled"
        )
        self.disconnect_button.pack(pady=5)

        self.status_label = ttk.Label(
            self.frame, text="Status: Not connected", foreground="red"
        )
        self.status_label.pack(pady=5)

    def _refresh_ports(self):
        ports = []
        if serial:
            ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_dropdown["values"] = ports or ["No ports found"]
        self.port_dropdown.current(0)

    def connect(self):
        if not serial:
            messagebox.showerror(
                "Missing dependency", "pyserial not installed (pip install pyserial)"
            )
            return
        selected = self.port_var.get()
        if selected == "No ports found":
            messagebox.showerror("No Ports", "No serial ports detected.")
            return
        try:
            self.serial_conn = serial.Serial(selected, baudrate=9600, timeout=1)
            self.status_label.config(
                text=f"Status: Connected to {selected}", foreground="green"
            )
            self.connect_button["state"] = "disabled"
            self.disconnect_button["state"] = "normal"
            # Start live reader
            self.stop_reader = False
            self.reader_thread = threading.Thread(
                target=self._reader_loop, daemon=True
            )
            self.reader_thread.start()
        except Exception as e:
            self.serial_conn = None
            messagebox.showerror("Connection Failed", str(e))

    def _reader_loop(self):
        while not self.stop_reader and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline().decode(errors="ignore").strip()
                if line:
                    # Log live output
                    self.run_tab_ref.log(f"[LIVE] {line}")
                    # Save into buffer for RunTab evaluation
                    self.shared_buffer.append(line)
            except Exception:
                pass

    def disconnect(self):
        self.stop_reader = True
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.serial_conn = None
        self.status_label.config(text="Status: Not connected", foreground="red")
        self.connect_button["state"] = "normal"
        self.disconnect_button["state"] = "disabled"
