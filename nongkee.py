"""Nongkee native client. Only the Python standard library is required."""
import json
import os
import tkinter as tk
from http.cookiejar import CookieJar
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

GREEN, LIME, INK, WHITE = "#00c060", "#b8ff66", "#173329", "#ffffff"


class Client:
    def __init__(self):
        self.base = os.environ.get("NONGKEE_URL", "http://127.0.0.1:8000").rstrip("/")
        url = urlsplit(self.base)
        if url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1")):
            raise ValueError("Gunakan HTTPS untuk server di luar komputer ini.")
        self.http = build_opener(HTTPCookieProcessor(CookieJar()))
        self.csrf = ""

    def request(self, path, data=None):
        headers = {"Accept": "application/json", "X-CSRFToken": self.csrf, "Referer": self.base + "/"}
        body = urlencode(data).encode() if data is not None else None
        try:
            with self.http.open(Request(self.base + path, body, headers), timeout=6) as response:
                result = json.load(response)
        except HTTPError as error:
            if error.headers.get_content_type() == "application/json":
                raise ValueError(json.load(error).get("error", str(error))) from error
            raise ValueError(f"Tindakan gagal (HTTP {error.code}). Muat ulang data.") from error
        except (URLError, TimeoutError, OSError, ValueError) as error:
            raise ValueError("Server Nongkee tidak tersedia atau sesi berakhir. Periksa NONGKEE_URL dan muat ulang.") from error
        if "csrf" in result:
            self.csrf = result["csrf"]
        return result


class App:
    def __init__(self, root):
        self.root = root
        self.api = Client()
        self.section = "Open Meets"
        root.title("nongkee")
        root.geometry("1060x740")
        root.minsize(720, 540)
        root.configure(bg=WHITE)
        root.report_callback_exception = self.error
        top = tk.Frame(root, bg=WHITE, padx=24, pady=14)
        top.pack(fill="x")
        tk.Label(top, text="◎  nongkee", font=("Segoe UI", 25, "bold"), fg=GREEN, bg=WHITE).pack(side="left")
        self.account = ttk.Button(top, text="Sign in", command=self.profile)
        self.account.pack(side="right")
        rail = tk.Frame(root, bg=GREEN, padx=5, pady=6)
        rail.pack(side="left", padx=(12, 0))
        self.nav = {}
        for label in ("Kelas Kosong", "Open Meets", "Friends"):
            button = tk.Button(rail, text=label, borderwidth=0, width=12, pady=9, command=lambda s=label: self.show(s))
            button.pack(fill="x")
            self.nav[label] = button
        canvas = tk.Canvas(root, bg=WHITE, highlightthickness=0)
        bar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        bar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        canvas.configure(yscrollcommand=bar.set)
        self.body = tk.Frame(canvas, bg=WHITE, padx=18)
        item = canvas.create_window(0, 0, anchor="nw", window=self.body)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(item, width=e.width))
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.canvas = canvas
        self.data = {"user": None}
        self.show("Open Meets")

    def error(self, kind, value, traceback):
        messagebox.showerror("nongkee", str(value), parent=self.root)

    def show(self, section=None):
        self.section = section or self.section
        for widget in self.body.winfo_children():
            widget.destroy()
        self.canvas.yview_moveto(0)
        for label, button in self.nav.items():
            button.configure(bg=LIME if label == self.section else GREEN)
        tk.Label(self.body, text="Katalog Kelas Kosong" if self.section == "Kelas Kosong" else self.section,
                 bg=WHITE, font=("Segoe UI", 23, "bold"), pady=18).pack()
        ttk.Button(self.body, text="Muat ulang", command=self.show).pack(anchor="e")
        try:
            self.data = self.api.request("/api/state/")
        except ValueError as error:
            ttk.Label(self.body, text=str(error), wraplength=480).pack(pady=18)
            return
        user = self.data["user"]
        self.account.configure(text=user["name"] + " · Profil" if user else "Sign in")
        if self.section == "Friends":
            self.friends() if user else ttk.Button(self.body, text="Sign in", command=self.auth).pack()
        elif self.section == "Kelas Kosong":
            self.slot_picker(self.body, False)
        else:
            grid = tk.Frame(self.body, bg=WHITE)
            grid.pack(fill="x", pady=12)
            for col in range(3):
                grid.columnconfigure(col, weight=1, uniform="card")
            self.card(grid, 0, "⊕", WHITE, self.create)
            for i, meet in enumerate(self.data["meets"], 1):
                initials = [n[:1].upper() for n in meet["attendees"][:3]]
                label = f"{meet['title']}\nopened by: {meet['host']}\n{meet['topic']} · {meet['room']}"
                self.card(grid, i, label, GREEN if meet["is_host"] or meet["status"] == "joined" else LIME,
                          lambda m=meet: self.detail(m), initials)

    def card(self, grid, i, label, color, command, initials=()):
        card = tk.Canvas(grid, width=1, height=166, bg=WHITE, highlightthickness=1,
                         highlightbackground=WHITE, highlightcolor=GREEN, takefocus=True, cursor="hand2")
        card.grid(row=i//3, column=i%3, padx=6, pady=6, sticky="nsew")

        def draw(event):
            card.delete("all")
            w, h, r = event.width - 3, event.height - 3, 25
            points = (r, 2, w-r, 2, w, 2, w, r, w, h-r, w, h, w-r, h, r, h,
                      2, h, 2, h-r, 2, r, 2, 2)
            card.create_polygon(points, smooth=True, fill=color, outline=GREEN,
                                dash=(3, 3) if not initials else ())
            for index, initial in enumerate(initials):
                x = w/2 + (index - (len(initials)-1)/2)*34
                card.create_oval(x-16, 15, x+16, 47, fill=WHITE, outline=GREEN, width=2)
                card.create_text(x, 31, text=initial, fill=INK, font=("Segoe UI", 11, "bold"))
            card.create_text(w/2, h*0.61 if initials else h/2, text=label, width=w-18,
                             justify="center", fill=INK if initials else GREEN,
                             font=("Segoe UI", 10 if initials else 24, "bold"))
        card.bind("<Configure>", draw)
        for event in ("<Button-1>", "<Return>", "<space>"):
            card.bind(event, lambda e: command())

    def dialog(self, title):
        win = tk.Toplevel(self.root, bg=WHITE, padx=24, pady=16)
        win.title(title)
        win.transient(self.root)
        win.grab_set()
        tk.Label(win, text=title, bg=WHITE, font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=6)
        return win

    def field(self, win, label, value="", secret=False):
        ttk.Label(win, text=label).pack(anchor="w")
        entry = ttk.Entry(win, width=38, show="*" if secret else "")
        entry.insert(0, value)
        entry.pack(fill="x", pady=(0, 6))
        return entry

    def choice(self, win, label, values, default=None):
        ttk.Label(win, text=label).pack(anchor="w")
        combo = ttk.Combobox(win, values=values, state="readonly")
        combo.set(default or values[0])
        combo.pack(fill="x", pady=(0, 5))
        return combo

    def finish(self, win, path, fields):
        self.api.request(path, fields)
        win.destroy()
        self.show()

    def auth(self, signup=False):
        win = self.dialog("Create account" if signup else "Sign in")
        fields = {"username": self.field(win, "Email")}
        if signup:
            fields["first_name"] = self.field(win, "Nama tampilan")
        fields["password1" if signup else "password"] = self.field(win, "Password", secret=True)
        if signup:
            fields["password2"] = self.field(win, "Ulangi password", secret=True)
        action = "signup" if signup else "login"
        ttk.Button(win, text="Create account" if signup else "Sign in", command=lambda: self.finish(
            win, f"/api/account/{action}/", {key: entry.get() for key, entry in fields.items()})).pack(pady=6)
        if not signup:
            def register():
                win.destroy()
                self.auth(True)
            ttk.Button(win, text="Create account", command=register).pack()

    def profile(self):
        user = self.data["user"]
        if not user:
            return self.auth()
        win = self.dialog("Profil")
        ttk.Label(win, text=user["email"]).pack(anchor="w")
        display = self.field(win, "Nama tampilan", user["name"])
        ttk.Button(win, text="Simpan profil", command=lambda: self.finish(win, "/profile/", {"first_name": display.get()})).pack()
        ttk.Label(win, text="Mahasiswa UI · Belum terverifikasi").pack(pady=10)
        ttk.Button(win, text="Verifikasi mahasiswa UI", command=lambda: messagebox.showinfo(
            "SSO UI", self.api.request("/profile/verify/", {})["message"], parent=win)).pack()
        ttk.Button(win, text="Sign out", command=lambda: self.finish(win, "/api/account/logout/", {})).pack(pady=8)

    def friends(self):
        email = self.field(self.body, "Email teman")
        def update(fields):
            self.api.request("/friends/", fields)
            self.show()
        ttk.Button(self.body, text="Tambah teman", command=lambda: update({"action": "invite", "email": email.get()})).pack(anchor="w")
        people = self.api.request("/friends/")["people"]
        if not people:
            ttk.Label(self.body, text="Belum ada teman.").pack(pady=12)
        for person in people:
            row = tk.Frame(self.body, bg=LIME, padx=12, pady=10)
            row.pack(fill="x", pady=4)
            tk.Label(row, bg=LIME, text=person["name"] + " · " + person["status"]).pack(side="left")
            if person["status"] == "Permintaan masuk":
                ttk.Button(row, text="Terima", command=lambda i=person["id"]: update({"action": "accept", "id": i})).pack(side="right")

    def slot_picker(self, win, picker):
        date = self.field(win, "Tanggal (YYYY-MM-DD)", self.data["date"])
        window = self.choice(win, "Waktu (WIB)", self.data["windows"], self.data["window"])
        buildings = {label: key for key, label in self.data["buildings"]}
        if picker:
            buildings["Casual"] = "casual"
        building = self.choice(win, "Area", list(buildings))
        rooms = tk.Listbox(win, height=6 if picker else 14, exportselection=False)
        options = []
        def refresh(*args):
            options.clear()
            rooms.delete(0, "end")
            query = urlencode(dict(date=date.get(), window=window.get(), building=buildings[building.get()], picker=int(picker)))
            options.extend(self.api.request("/api/state/?" + query)["rooms"])
            for room in options:
                rooms.insert("end", ("Terisi" if room["busy"] else "Tersedia") + "   ·   " + room["name"])
        ttk.Button(win, text="Cari kelas", command=refresh).pack(anchor="w", pady=4)
        rooms.pack(fill="both", expand=True)
        def clear(event):
            options.clear()
            rooms.delete(0, "end")
        date.bind("<KeyRelease>", clear)
        window.bind("<<ComboboxSelected>>", refresh)
        building.bind("<<ComboboxSelected>>", refresh)
        refresh()
        def selected():
            if not rooms.curselection() or options[rooms.curselection()[0]]["busy"]:
                raise ValueError("Pilih kelas yang tersedia.")
            return dict(date=date.get(), window=window.get(), room=options[rooms.curselection()[0]]["name"])
        if not picker:
            ttk.Button(win, text="Start a Meet", command=lambda: self.create(selected())).pack(pady=6)
        return selected

    def create(self, slot=None):
        if not self.data["user"]:
            return self.auth()
        win = self.dialog("Start a Meet")
        title = self.field(win, "Meet Title")
        topic = self.choice(win, "Topic / Category", self.data["topics"])
        mode = self.choice(win, "Who can join?", ["Anyone can join", "Host approves requests"])
        if slot:
            ttk.Label(win, text=f"{slot['room']} · {slot['date']} · {slot['window']}").pack()
        select = (lambda: slot) if slot else self.slot_picker(win, True)
        ttk.Button(win, text="Start Meet", command=lambda: self.finish(win, "/meets/create/", dict(
            select(), title=title.get(), topic=topic.get(), join_mode="direct" if mode.current() == 0 else "approval"))).pack(pady=8)

    def detail(self, meet):
        win = self.dialog(meet["title"])
        for line in (meet["topic"], meet["room"], f"{meet['date']} · {meet['window']} WIB",
                     "Host · " + meet["host"], "Attendees · " + ", ".join(meet["attendees"])):
            ttk.Label(win, text=line, wraplength=420).pack(anchor="w", pady=3)
        def act(action, member=""):
            if action == "cancel" and not messagebox.askyesno("Cancel meet", "Batalkan meet ini?", parent=win):
                return
            self.finish(win, f"/meets/{meet['id']}/action/", dict(action=action, member=member))
        if not self.data["user"]:
            def signin():
                win.destroy()
                self.auth()
            ttk.Button(win, text="Sign in to join", command=signin).pack()
            return
        if meet["is_host"]:
            for person in meet["requests"]:
                row = ttk.Frame(win)
                row.pack(fill="x")
                ttk.Label(row, text=person["name"]).pack(side="left")
                for action in ("approve", "decline"):
                    ttk.Button(row, text=action.title(), command=lambda a=action, i=person["id"]: act(a, i)).pack(side="left")
            label, action = "Cancel meet", "cancel"
        elif meet["status"]:
            label, action = ("Withdraw request" if meet["status"] == "pending" else "Leave"), "leave"
        else:
            label, action = ("Request to join" if meet["mode"] == "approval" else "Join"), "join"
        ttk.Button(win, text=label, command=lambda: act(action)).pack(pady=8)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
