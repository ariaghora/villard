import os

import pandas as pd
from villard.io import PandasWriter, PandasReader


def test_pandas_writer():
    writer = PandasWriter()
    writer.write_data("test.csv", pd.DataFrame({"a": [1, 2, 3]}))

    assert os.path.exists("test.csv")

    os.remove("test.csv")


def test_pandas_writer_without_index():
    writer = PandasWriter()
    writer.write_data(
        "test.csv", pd.DataFrame({"a": [1, 2, 3]}, index=["a", "b", "c"]), index=False
    )

    df = pd.read_csv("test.csv")
    assert df.index.equals(pd.RangeIndex(start=0, stop=3, step=1))

    os.remove("test.csv")
