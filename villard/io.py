import os
import pickle

import pandas as pd
from termcolor import colored

"""===================
Writer classes
==================="""


class BaseDataWriter:
    def write_data(self, path: str, data: object, *args, **kwargs) -> None:
        dirname = os.path.dirname(path)
        if (not os.path.exists(dirname)) and (dirname != ""):
            os.makedirs(dirname)


class PickleWriter(BaseDataWriter):
    def write_data(self, path: str, data: object, *args, **kwargs) -> None:
        super().write_data(path, data)
        with open(path, "wb") as f:
            pickle.dump(data, f, *args, **kwargs)


class PandasWriter(BaseDataWriter):
    def write_data(self, path: str, data: object, *args, **kwargs) -> None:
        super().write_data(path, data)
        data.to_csv(path, *args, **kwargs)


"""===================
Reader classes
==================="""


class BaseDataReader:
    def read_data(self, path: str, *args, **kwargs) -> object:
        pass


class PickleReader(BaseDataReader):
    def read_data(self, path: str, *args, **kwargs) -> object:
        super().read_data(path, *args, **kwargs)
        with open(path, "rb") as f:
            return pickle.load(f, *args, **kwargs)


class PandasReader(BaseDataReader):
    def read_data(self, path: str, *args, **kwargs) -> pd.DataFrame:
        super().read_data(path, *args, **kwargs)
        return pd.read_csv(path, *args, **kwargs)
