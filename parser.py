import re
from pathlib import Path
from typing import Optional

from exceptions import NoNewLogs
from structs import ParsedDmgLog


class LogParser:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch()
        self.last_pos: int = self.get_last_pos(log_path)

    @staticmethod
    def get_last_pos(log_path: Path) -> int:
        """
        Find the end of the log file so parser doesn't start from the beginning.
        """
        with open(log_path) as f:
            _ = f.seek(0, 2)
            pos = f.tell()

        return pos

    def get_new_logs(self) -> list[str]:
        """
        Only read the newest logs.
        """
        with open(self.log_path, "r") as f:
            _ = f.seek(self.last_pos)
            logs = f.read().split("\n")
            self.last_pos = f.tell()

        return logs

    @staticmethod
    def extract_damage(log: str) -> int:
        """
        Extract the damage number from each string.
        """
        if match := re.search("Damage too high:\\s*([\\d,]+)$", log):
            return int(match.group(1).replace(",", ""))
        else:
            return 0

    @staticmethod
    def find_text(search_text: str, full_text: str) -> str:
        """
        Finds search_text inside full_text and returns everything to the end of the line. Trims trailing commas.
        Should be called after `parse_dmg_source_type`.
        """
        idx = full_text.find(search_text)
        result = full_text[idx + len(search_text) :].strip(",")
        return result

    @staticmethod
    def parse_dmg_source_type(log: str) -> Optional[str]:
        text = "SourceObjectType: "
        m = re.search(f".+{text}.+", log)

        if m is None:
            return

        return m.group(0).strip()[len(text) :].split("/")[-1]

    @staticmethod
    def parse_victim_dmg(log: str) -> tuple[str, str]:
        v_txt = "Victim: "
        s_txt = ", source: "

        # find is ok because this method is called when re.search has a hit
        v_start = log.find(v_txt)
        v_end = log.find(s_txt)

        victim = log[v_start:v_end].split(",")[0][len(v_txt) :]
        source = log[v_end + len(s_txt) :]

        return (victim, source)

    def parse_logs(self, logs: list[str]) -> ParsedDmgLog:
        """
        Go through each line in `logs` and parse high damage events.
        """
        victims: ParsedDmgLog = dict()  # Victim: [(Source, Damage), ...]
        sources: dict[str, str] = dict()  # Source: Friendly Name

        for i, log in enumerate(logs):
            s_obj = self.parse_dmg_source_type(log)
            if s_obj is not None:
                s = self.find_text("Source: ", logs[i - 1])
                t = self.find_text("Types: ", logs[i - 2])
                if s not in sources:
                    sources[s] = f"{s_obj} ({t})"
                continue

            m = re.search(".+ Victim: .+, source: .+", log)
            if m is None:
                continue

            t = self.parse_victim_dmg(log)

            victim, source = t
            dmg = self.extract_damage(logs[i - 1])

            # use raw Source if there's no mapping to an asset name
            dmg_source = sources.get(source, source)

            try:
                victims[victim].append((dmg_source, dmg))
            except KeyError:
                victims[victim] = [(dmg_source, dmg)]

        return victims

    def process(self) -> ParsedDmgLog:
        """
        If new logs exists, process them and return `ParsedDmgLog`, a dictionary containing Victim: [(Source, Damage), ...].

        Otherwise raise `NoNewLogs`.
        """
        logs = self.get_new_logs()

        if not logs:
            raise NoNewLogs

        parsed = self.parse_logs(logs)
        if not parsed:
            raise NoNewLogs

        return parsed
