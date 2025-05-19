"""Simple Flask dashboard to display calculation results."""

from typing import Any, Dict

from flask import Flask


def create_app(summary: Dict[str, Any]) -> Flask:
    """Create a Flask application showing the calculation summary."""

    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        lines = [f"{key}: {value}" for key, value in summary.items()]
        return "<br>".join(lines)

    return app


def run_dashboard(summary: Dict[str, Any]) -> None:
    """Run the dashboard web server."""

    app = create_app(summary)
    app.run()
