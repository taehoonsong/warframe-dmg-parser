import os
import platform
import sys
from pathlib import Path

from gui import App, path_not_found, unsupported
from parser import LogParser


def main() -> None:
    p = platform.system()
    if p == "Windows":
        app_data = os.getenv("LOCALAPPDATA")
        if app_data is None:
            path_not_found()
            sys.exit(1)
    elif p == "Linux":
        app_data = Path(
            "~/.local/share/Steam/steamapps/compatdata/230410/pfx/drive_c/users/steamuser/AppData/Local"
        ).expanduser()
        if not app_data.exists():
            path_not_found()
            sys.exit(1)
    else:
        unsupported()
        sys.exit(1)

    log_path = Path(app_data, "Warframe", "EE.log")
    parser = LogParser(log_path)
    app = App(parser)
    app.mainloop()


if __name__ == "__main__":
    main()
