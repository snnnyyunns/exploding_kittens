"""
main.py — Entry point for Exploding Kittens Digital Edition.

Run with:
    python main.py

Step-by-step:
1) Add the project root to `sys.path` so package imports work when running
   this file directly with Python.
2) Import the Tkinter application class from `gui.app`.
3) Create the app instance in `main()`.
4) Start Tk's event loop with `mainloop()`, which keeps the UI running
   and dispatches button/click events.
5) Only execute `main()` when this file is launched as a script.
"""

import sys
import os

# Ensure the project root is on the Python path so all packages resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
