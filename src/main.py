import os

from contextlib import redirect_stdout

from io import StringIO

import webview

from config import port, global_dir

from server import app

if __name__ == '__main__':
    window = webview.create_window('GTCS CSS Client', app)
    webview.start()
