import os
import sys


def resolve_path(path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, path)


if __name__ == "__main__":
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.fileWatcherType=none",
    ]
    sys.exit(stcli.main())