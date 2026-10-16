"""
iPhone Teleport - set a fake GPS location on an iPhone over USB (Windows).
Uses pymobiledevice3 (open-source) to talk to Apple's developer services.
"""
import ctypes, json, os, subprocess, sys, threading, time
import tkinter as tk
from tkinter import ttk

try:
    import tkintermapview
except ImportError:
    tkintermapview = None

PY = sys.executable
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", PY, f'"{script}"', None, 1)
    sys.exit(0)


def pmd(*args):
    return [PY, "-m", "pymobiledevice3", *args]


def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           creationflags=NO_WINDOW)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "Timed out."


class App:
    def __init__(self, root):
        self.root = root
        self.tunnel_proc = None
        self.sim_proc = None
        self.ios_major = None
        self.marker = None

        root.title("iPhone Teleport")
        root.geometry("900x680")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        self.connect_btn = ttk.Button(top, text="Connect iPhone", command=self.connect)
        self.connect_btn.pack(side="left")
        ttk.Button(top, text="Show Developer Mode on phone",
                   command=self.reveal_dev_mode).pack(side="left", padx=6)
        self.status = ttk.Label(top, text="Not connected", foreground="#a33")
        self.status.pack(side="left", padx=10)

        row = ttk.Frame(root, padding=(8, 0))
        row.pack(fill="x")
        ttk.Label(row, text="Search place:").pack(side="left")
        self.search = ttk.Entry(row, width=30)
        self.search.pack(side="left", padx=4)
        self.search.bind("<Return>", lambda e: self.find_place())
        ttk.Button(row, text="Find", command=self.find_place).pack(side="left")
        ttk.Label(row, text="   Lat:").pack(side="left")
        self.lat = ttk.Entry(row, width=12)
        self.lat.pack(side="left")
        ttk.Label(row, text="Lon:").pack(side="left")
        self.lon = ttk.Entry(row, width=12)
        self.lon.pack(side="left")
        self.go_btn = ttk.Button(row, text="Teleport", command=self.teleport, state="disabled")
        self.go_btn.pack(side="left", padx=6)
        self.reset_btn = ttk.Button(row, text="Back to real location",
                                    command=self.reset, state="disabled")
        self.reset_btn.pack(side="left")

        if tkintermapview:
            self.map = tkintermapview.TkinterMapView(root, corner_radius=0)
            self.map.pack(fill="both", expand=True, padx=8, pady=8)
            self.map.set_position(47.3769, 8.5417)
            self.map.set_zoom(12)
            self.map.add_left_click_map_command(self.on_map_click)
        else:
            self.map = None
            ttk.Label(root, text="Map not available (run install.bat). "
                                 "You can still type coordinates.").pack(pady=20)

        self.log_box = tk.Text(root, height=8, wrap="word", state="disabled")
        self.log_box.pack(fill="x", padx=8, pady=(0, 8))
        self.log("Plug in your iPhone, unlock it, then click 'Connect iPhone'.")
        self.log("Tip: click anywhere on the map to pick a spot.")

    # ---------- helpers ----------
    def log(self, msg):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.root.after(0, _do)

    def set_status(self, text, ok):
        self.root.after(0, lambda: self.status.config(
            text=text, foreground="#2a7a2a" if ok else "#a33"))

    def bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def pump_output(self, proc, prefix):
        for line in proc.stdout:
            line = line.strip()
            if line:
                self.log(f"{prefix}{line}")

    # ---------- map ----------
    def on_map_click(self, coords):
        lat, lon = coords
        self.put_coords(lat, lon)

    def put_coords(self, lat, lon):
        for entry, val in ((self.lat, lat), (self.lon, lon)):
            entry.delete(0, "end")
            entry.insert(0, f"{val:.6f}")
        if self.map:
            if self.marker:
                self.marker.set_position(lat, lon)
            else:
                self.marker = self.map.set_marker(lat, lon, text="Fake location")

    def find_place(self):
        q = self.search.get().strip()
        if not q or not self.map:
            return
        if self.map.set_address(q, marker=False):
            lat, lon = self.map.get_position()
            self.put_coords(lat, lon)
            self.log(f"Found '{q}'. Click Teleport to go there.")
        else:
            self.log(f"Couldn't find '{q}'. Try a city name or address.")

    # ---------- device ----------
    def reveal_dev_mode(self):
        def work():
            code, out = run(pmd("amfi", "reveal-developer-mode"))
            self.log(out or "Done.")
            self.log("On the iPhone: Settings > Privacy & Security > Developer Mode > On, "
                     "then restart the phone and confirm.")
        self.bg(work)

    def connect(self):
        self.connect_btn.config(state="disabled")
        self.bg(self._connect)

    def _connect(self):
        try:
            self.log("Looking for iPhone...")
            code, out = run(pmd("usbmux", "list"), timeout=20)
            try:
                devices = json.loads(out)
            except Exception:
                devices = []
            if not devices:
                self.log("No iPhone found. Check: cable plugged in, phone unlocked, "
                         "you tapped 'Trust This Computer', and iTunes / Apple Devices "
                         "is installed on this PC.")
                self.set_status("Not connected", False)
                return
            d = devices[0]
            version = d.get("ProductVersion", "0")
            self.ios_major = int(version.split(".")[0])
            self.log(f"Found {d.get('DeviceName', 'iPhone')} (iOS {version}).")

            if self.ios_major >= 17:
                if not (self.tunnel_proc and self.tunnel_proc.poll() is None):
                    self.log("Starting secure tunnel (needed on iOS 17+)...")
                    self.tunnel_proc = subprocess.Popen(
                        pmd("remote", "tunneld"), stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, creationflags=NO_WINDOW)
                    threading.Thread(target=self.pump_output,
                                     args=(self.tunnel_proc, "[tunnel] "),
                                     daemon=True).start()
                    time.sleep(6)

            self.log("Mounting developer image (first time can take a minute)...")
            code, out = run(pmd("mounter", "auto-mount"), timeout=180)
            if code != 0 and "already" not in out.lower():
                self.log(out)
                if "developer mode" in out.lower():
                    self.log("Developer Mode is off. Click 'Show Developer Mode on phone'.")
                    self.set_status("Developer Mode needed", False)
                    return
            self.log("Ready! Pick a spot and click Teleport.")
            self.set_status(f"Connected (iOS {version})", True)
            self.root.after(0, lambda: (self.go_btn.config(state="normal"),
                                        self.reset_btn.config(state="normal")))
        finally:
            self.root.after(0, lambda: self.connect_btn.config(state="normal"))

    def stop_sim(self):
        if self.sim_proc and self.sim_proc.poll() is None:
            self.sim_proc.terminate()
            try:
                self.sim_proc.wait(5)
            except Exception:
                self.sim_proc.kill()
        self.sim_proc = None

    def teleport(self):
        try:
            lat = float(self.lat.get())
            lon = float(self.lon.get())
            assert -90 <= lat <= 90 and -180 <= lon <= 180
        except Exception:
            self.log("Enter a valid latitude (-90 to 90) and longitude (-180 to 180).")
            return
        self.put_coords(lat, lon)
        self.bg(lambda: self._teleport(lat, lon))

    def _teleport(self, lat, lon):
        self.stop_sim()
        self.log(f"Teleporting to {lat:.6f}, {lon:.6f}...")
        if self.ios_major and self.ios_major >= 17:
            # Must stay running: iOS 17+ drops the fake location when this closes.
            self.sim_proc = subprocess.Popen(
                pmd("developer", "dvt", "simulate-location", "set", "--tunnel", "",
                    "--", str(lat), str(lon)),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, creationflags=NO_WINDOW)
            threading.Thread(target=self.pump_output, args=(self.sim_proc, ""),
                             daemon=True).start()
            time.sleep(4)
            if self.sim_proc.poll() not in (None, 0):
                self.log("Teleport failed. Try clicking 'Connect iPhone' again.")
                return
        else:
            code, out = run(pmd("developer", "simulate-location", "set",
                                "--", str(lat), str(lon)))
            if code != 0:
                self.log(out or "Teleport failed.")
                return
        self.log("Done! Open Maps on your iPhone to check.")

    def reset(self):
        def work():
            self.stop_sim()
            if self.ios_major and self.ios_major >= 17:
                cmd = pmd("developer", "dvt", "simulate-location", "clear", "--tunnel", "")
            else:
                cmd = pmd("developer", "simulate-location", "clear")
            code, out = run(cmd)
            self.log("Back to real location." if code == 0 else (out or "Reset failed."))
            self.log("If it still looks stuck, restart the iPhone.")
        self.bg(work)

    def on_close(self):
        self.stop_sim()
        if self.tunnel_proc and self.tunnel_proc.poll() is None:
            self.tunnel_proc.terminate()
        self.root.destroy()


if __name__ == "__main__":
    if os.name == "nt" and not is_admin():
        relaunch_as_admin()
    root = tk.Tk()
    App(root)
    root.mainloop()
