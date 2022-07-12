import os
import pickle
import pandas as pd
from termcolor import colored


class DataWriter:
    def write_data(self, path: str, data: object, *args, **kwargs):
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)


class PickleWriter(DataWriter):
    def write_data(self, path: str, data: object, *args, **kwargs):
        super().write_data(path, data)
        with open(path, "wb") as f:
            pickle.dump(data, f, *args, **kwargs)


class PandasWriter(DataWriter):
    def write_data(self, path: str, data: object, *args, **kwargs):
        super().write_data(path, data)
        data.to_csv(path, *args, **kwargs)


class DataReader:
    def read_data(self, path: str, *args, **kwargs):
        if not os.path.exists(path):
            msg = f"Data path `{path}` does not exist."
            print(colored("Error:", "red"), colored(msg, "red"))
            exit(1)


class PickleReader(DataReader):
    def read_data(self, path: str, *args, **kwargs):
        super().read_data(path, *args, **kwargs)
        with open(path, "rb") as f:
            return pickle.load(f, *args, **kwargs)


class PandasReader(DataReader):
    def read_data(self, path: str, *args, **kwargs):
        super().read_data(path, *args, **kwargs)
        return pd.read_csv(path, *args, **kwargs)


class DataReaderByType(DataReader):
    def __init__(self) -> None:
        super().__init__()

    def read_data(self, data_type: str, path: str, *args, **kwargs):
        super().read_data(path, *args, **kwargs)
        if data_type == "DT_PICKLE":
            return PickleReader().read_data(path, *args, **kwargs)
        elif data_type == "DT_PANDAS_DATAFRAME":
            return PandasReader().read_data(path, *args, **kwargs)
        else:
            raise ValueError("Unknown data type: {}".format(data_type))
