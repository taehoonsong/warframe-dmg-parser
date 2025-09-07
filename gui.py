import datetime as dt
import math
import tkinter as tk
from pathlib import Path
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText
from typing import NamedTuple, Protocol

from exceptions import NoNewLogs
from structs import ParsedDmgLog


class Parser(Protocol):
    @property
    def log_path(self) -> Path: ...
    def process(self) -> ParsedDmgLog: ...


class RGB(NamedTuple):
    r: int
    g: int
    b: int


class App(tk.Frame):
    def __init__(self, parser: Parser, check_interval_ms: int = 1000) -> None:
        self.parser = parser
        self.check_interval = check_interval_ms
        self.tags: dict[str, RGB] = {
            "time": RGB(91, 142, 253),
            "dmg": RGB(221, 33, 125),
            "victim": RGB(255, 176, 13),
            "source": RGB(114, 93, 239),
        }

        # Create window
        self.root = tk.Tk()
        self.root.withdraw()
        super().__init__(self.root)
        self.make_window()

        # Periodically check logs while running mainloop
        self.after(self.check_interval, self.parse_logs)
        self.mainloop()

    def make_window(self) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        top_window = tk.Toplevel(self.root)
        top_window.title("Warframe Damage Parser")
        top_window.geometry(f"{int(screen_width / 3)}x{int(screen_height / 5)}")
        top_window.wm_attributes("-topmost", True)
        top_window.protocol("WM_DELETE_WINDOW", self.root.quit)

        # Log window
        self.log = ScrolledText(top_window, width=200, height=10, wrap=tk.WORD)
        self.log.pack(padx=10, pady=10, fill=tk.BOTH, side=tk.LEFT, expand=True)
        for tag, rgb in self.tags.items():
            self.log.tag_configure(tag, foreground=self.rgb_to_hex(rgb))
        self.log.configure(state="disabled")  # disable user input

    @staticmethod
    def rgb_to_hex(rgb: RGB):
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def millify(n: int | float) -> str:
        """
        Human-readable large numbers.

        https://stackoverflow.com/questions/3154460/python-human-readable-large-numbers
        """
        n = float(n)
        names = ["", " K", " M", " B", " T", " Q"]
        idx = max(
            0,
            min(
                len(names) - 1, int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))
            ),
        )

        number = f"{n / 10 ** (3 * idx):0<5.4}"  # always show 5 characters (including decimal point)
        unit = names[idx]

        return f"{number}{unit}"

    def parse_logs(self) -> None:
        """
        If there are new logs, process logs and add relevant messages to `ScrolledText`.
        Otherwise, schedule next iteration and exit early.
        """
        try:
            new_logs = self.parser.process()
        except NoNewLogs:
            self.after(self.check_interval, self.parse_logs)
            return

        self.log.configure(state="normal")
        for v, dmgs in new_logs.items():
            max_dmg = 0
            max_dmg_src = "Unknown"
            for t in dmgs:
                source, dmg = t
                if dmg > max_dmg:
                    max_dmg = dmg
                    max_dmg_src = source

            self.add_line(v, max_dmg, max_dmg_src)

        self.log.yview(tk.END)  # show latest message
        self.log.update()
        self.log.configure(state="disabled")

        self.after(self.check_interval, self.parse_logs)

    def _insert_msg(self, text: str, tag: str = "") -> None:
        self.log.insert(tk.END, text, tag)

    def add_line(self, victim: str, dmg: int | float, source: str) -> None:
        messages: list[tuple[str, ...]] = [
            (f"{dt.datetime.now().strftime('%H:%M:%S')}", "time"),  # text, tag
            (" - ",),
            ("Damage: ",),
            (f"{self.millify(dmg):<10}", "dmg"),
            ("Victim: ",),
            (f"{victim:<44}", "victim"),
            ("\tBy: ",),
            (source, "source"),
            ("\n",),
        ]

        for msg in messages:
            self._insert_msg(*msg)


def unsupported() -> None:
    root = tk.Tk()
    root.withdraw()
    showerror(
        "Unsupported OS",
        "Only Windows and Linux are supported",
        icon="error",
        parent=root,
    )


def path_not_found() -> None:
    root = tk.Tk()
    root.withdraw()
    showerror(
        "Path Not Found",
        "Could not find AppData/Local folder",
        icon="error",
        parent=root,
    )
