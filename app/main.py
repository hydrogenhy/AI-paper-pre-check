import os
import sys
from flask import Flask, render_template
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.api import upload as upload_routes
from app.api import check as check_routes

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)

upload_routes.register_routes(app)
check_routes.register_check_routes(app)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
