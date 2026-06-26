import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dashboard import app

if __name__ == "__main__":
    app.run()