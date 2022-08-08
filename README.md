<p align="center" >
    <img src="assets/logo.png" width=350>
</p>

<p align="center" >
<strong>
A tiny layer to organize your data science project
</strong>
</p>

---

<p align="center" >
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54">
<img src="https://camo.githubusercontent.com/3dbcfa4997505c80ef928681b291d33ecfac2dabf563eb742bb3e269a5af909c/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6963656e73652f496c65726961796f2f6d61726b646f776e2d6261646765733f7374796c653d666f722d7468652d6261646765">
</p>

## About 
Sometimes you only need to accommodate frequent experiment pipeline changes and track everything.
Almost always, your project is not FAANG-scaled and you just need a simple tool to organize your experiment code.
Maybe you will like this.

Villard manages your data science pipelines by splitting a big project into smaller discrete steps.
This encourages maintainable and reproducible workflow.
Perhaps you don't even need to change your existing code too much.

### What would you would expect from Villard:
- An experiment pipeline management framework
- An experiment tracker and explorer


## Installation
    pip install git+https://github.com/ariaghora/villard

## Quick start

For starters, use the following command to create a project:

```
$ villard create example
$ cd example
```

This will give you a directory named `example` with the following structure (and example data):

```
villard-readme
├── config.jsonnet
├── data
│   ├── 01_raw
│   │   ├── employee.csv
│   │   └── position.csv
│   ├── 02_intermediate
│   ├── 03_output
│   └── 04_report
└── steps.py
```

The `steps.py` file contains the following code:

```python
from villard import pipeline


@pipeline.step("merge_data")
def merge_data(df_employee, df_position):
    merged = df_employee.merge(df_position, on="id")
    return merged

@pipeline.step("sort_data")
def sort_data(df_merged, by, ascending):
    merged_and_sorted = df_merged.sort_values(by=by, ascending=ascending)
    pipeline.write_data("merged_and_sorted", merged_and_sorted)
```
The steps are simply to merge two dataframes, sort them, and write them to disk.
We can see how they are glued together by inspecting the `config.jsonnet` file:

```js
...
    pipeline_definition: {
        _default: {
            merge_data: {
                df_employee: "data::employee",
                df_position: "data::position",
            },
            sort_data: {
                df_merged: "ref::merge_data",
                by: "name",
                ascending: true,
            },
        },
    },
...
```

We can run the default pipeline by invoking the following command:
```
$ villard run config.jsonnet
```
You will see following output:
```
No pipeline name specified. Using default pipeline name: _default
  Executing `merge_data`...
⦿ Completed `merge_data`
  Executing `sort_data`...
⦿ Completed `sort_data`
Using default experiment directory: /Users/ghora/.villard/experiments

╒════════════╤════════════════╤══════════════════╕
│ Step       │ Dependencies   │ Execution Time   │
╞════════════╪════════════════╪══════════════════╡
│ merge_data │ []             │ 0:00:00.003964   │
├────────────┼────────────────┼──────────────────┤
│ sort_data  │ ['merge_data'] │ 0:00:00.001557   │
╘════════════╧════════════════╧══════════════════╛
```
and soon we will have a `data/02_intermediate/merged_and_sorted.csv` file.

Please have some time to read the documentation at [https://ariaghora.github.io/villard/](https://ariaghora.github.io/villard/).