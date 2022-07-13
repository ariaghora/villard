import os

import jinja2
import joblib
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Villard Explorer</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
    <style>
        .table>:not(:first-child) {
            border-top: 0px;
        }
        .table {
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
    <h1>Experiment runs</h1>
    {{ html_table }}
    </div>
</body>
</html>
"""


class Explorer:
    def __init__(self, root_dir: str, host: str, port: int):
        self.root_dir = root_dir
        self.host = host
        self.port = port

        @app.get("/")
        def _root():
            dirs = os.listdir(self.root_dir)
            dirs = [d for d in dirs if os.path.isdir(os.path.join(self.root_dir, d))]
            items = []
            for _dir in dirs:
                exp_result = joblib.load(
                    os.path.join(self.root_dir, _dir, "experiment.pkl")
                )
                item = {
                    "run_name": _dir,
                    **exp_result,
                }
                items.append(item)

            t = jinja2.Template(TEMPLATE)
            html_table = pd.DataFrame(items)
            html_table = html_table.to_html(
                index=False, classes="table table-striped table-sm", border=0
            )
            return render_template(t, html_table=html_table)

    def serve(self) -> None:
        app.run(host=self.host, port=self.port)
