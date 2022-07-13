import os
import sys
from datetime import datetime
from typing import Any, Optional

import joblib


class ExperimentTracker:
    def __init__(self, run_name: str, experiment_dir: Optional[str] = None):
        self.run_name = run_name
        self.experiment_dir = experiment_dir

        self.experiment_dict = dict()

    def commit(self) -> None:
        # Write experiment dict to file only if it is not empty.
        if self.experiment_dict:
            if not self.run_name:
                self.run_name = datetime.now().strftime("run-%Y-%m-%d-%H-%M-%S")
            if not self.experiment_dir:
                self.experiment_dir = os.path.join(
                    os.path.expanduser("~"),
                    ".villard",
                    "experiments",
                )
                print(f"Using default experiment directory: {self.experiment_dir}")

            try:
                os.makedirs(os.path.join(self.experiment_dir, self.run_name))
            except FileExistsError:
                print(f"Experiment run with name {self.run_name} already exists.")
                sys.exit(1)

            joblib.dump(
                self.experiment_dict,
                os.path.join(self.experiment_dir, self.run_name, "experiment.pkl"),
            )

    def track(self, key: str, value: Any) -> None:
        # TODO: validity checking of key and value
        self.experiment_dict[key] = value
