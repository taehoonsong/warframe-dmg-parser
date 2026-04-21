import re
from pathlib import Path

from exceptions import NoNewLogsError
from structs import ParsedDmgLog


class LogParser:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch()
        self.last_pos: int = 0
        # self.get_last_pos(log_path)

    @staticmethod
    def get_last_pos(log_path: Path) -> int:
        """
        Find the end of the log file so parser doesn't start from the beginning.

        Returns:
            Byte position at the end of the file.

        """
        with Path(log_path).open(encoding="utf-8") as f:
            _ = f.seek(0, 2)
            pos = f.tell()

        return pos

    def get_new_logs(self) -> list[str]:
        """
        Only read the newest logs.

        Returns:
            List of new log lines since last read position.

        """
        with Path(self.log_path).open("r", encoding="utf-8") as f:
            _ = f.seek(self.last_pos)
            logs = f.read().split("\n")
            self.last_pos = f.tell()

        return logs

    @staticmethod
    def extract_damage(log: str) -> int:
        """
        Extract the damage number from each string.

        Returns:
            Damage value parsed from the log line, or 0 if not found.

        """
        if match := re.search(r"high dmg:\s*([\d,]+),", log):
            return int(match.group(1).replace(",", ""))
        return 0

    @staticmethod
    def find_text(search_text: str, full_text: str) -> str:
        """
        Find search_text inside full_text and return everything to end of line, trimming trailing commas.

        Should be called after `parse_dmg_source_type`.

        Returns:
            Substring following search_text with trailing commas stripped.

        """
        idx = full_text.find(search_text)
        result = full_text[idx + len(search_text) :].strip(",")
        return result

    # TODO: new log style
    def parse_logs(self, logs: list[str]) -> ParsedDmgLog:
        """
        Go through each line in `logs` and parse high damage events.

        Returns:
            ParsedDmgLog mapping each victim to a list of (source, damage) tuples.

        """
        victims: ParsedDmgLog = {}  # Victim: [(Source, Damage), ...]
        sources: dict[str, str] = {}  # Source: Friendly Name

        for i, log in enumerate(logs):
            s_obj = self.parse_dmg_source_type(log)
            if s_obj is not None:
                s = self.find_text("Source: ", logs[i - 1])
                t = self.find_text("Types: ", logs[i - 2])
                if s not in sources:
                    sources[s] = f"{s_obj} ({t})"
                continue

            m = re.search(r".+ Victim: .+, source: .+", log)
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
        Process new logs and return parsed damage data.

        Returns:
            ParsedDmgLog mapping each victim to a list of (source, damage) tuples.

        Raises:
            NoNewLogsError: If no new logs exist or no damage events were parsed.

        """
        logs = self.get_new_logs()

        if not logs:
            raise NoNewLogsError

        parsed = self.parse_logs(logs)
        if not parsed:
            raise NoNewLogsError

        return parsed
