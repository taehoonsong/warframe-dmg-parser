import os
import platform
import sys
from pathlib import Path

from config import get_app_data_path, load_or_create_config
from gui import App, path_not_found, unsupported
from parser import LogParser


def main() -> None:
    p = platform.system()
    if p == "Windows":
        default = os.getenv("LOCALAPPDATA")
        if default is None:
            path_not_found()
            sys.exit(1)
    elif p == "Linux":
        default = "~/.local/share/Steam/steamapps/compatdata/230410/pfx/drive_c/users/steamuser/AppData/Local"
    else:
        unsupported()
        sys.exit(1)

    config = load_or_create_config(default)
    app_data = get_app_data_path(config)
    if not app_data.exists():
        path_not_found()
        sys.exit(1)

    log_path = Path(app_data, "Warframe", "EE.log")
    parser = LogParser(log_path)
    app = App(parser)
    app.mainloop()


if __name__ == "__main__":
    main()
