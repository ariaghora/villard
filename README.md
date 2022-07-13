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
Villard manages your data science pipelines.
Split a big project into smaller discrete steps for a maintainable and reproducible workflow.
Perhaps you don't even need to your existing code too much.

### What would you would expect from Villard:
- An experiment pipeline management framework
- An experiment tracker and explorer

## Usage example

Suppose we have the following structure:

```
project_root/
    - config.yaml
    - pipeline.py
    - data/
        - input/ 
            - iris.csv
```

In `config.yaml` file:

```yaml
data_catalog:
    iris_data:
        path: "data/input/iris.csv"  # assumed you have it
        type: "DT_PANDAS_DATAFRAME"
    trained_model:
        path: "data/output/trained_model.pkl"
        type: "DT_PICKLE"

node_implementation_modules:
    - "pipeline"

pipeline_definition:
    _default:
        preprocess_data:
            data: "data::iris_data"
            train_size: 0.8
        train_model:
            data: "ref::preprocess_data"
            kernel: "rbf"
        evaluate_model:
            data: "ref::preprocess_data"
            model: "ref::train_model"
```

In `pipeline.py` file:

```python
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from villard import V

@V.node("preprocess_data")
def preprocess(data, train_size):
    X = data.drop("class", axis=1)
    y = data["class"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=train_size
    )
    return X_train, X_test, y_train, y_test


@V.node("train_model")
def train_model(data, kernel):
    # our usual training procedure
    X_train, _, y_train, _ = data
    clf = SVC(kernel=kernel)
    clf.fit(X_train, y_train)

    # Writer helper, to save the model according to
    # the specification of "trained_model" in the data 
    # catalog
    V.write_data("trained_model", clf)
    return clf


@V.node("evaluate_model")
def evaluate_model(data, model):
    _, X_test, _, y_test = data
    y_pred = model.predict(X_test)
    accuracy = model.score(X_test, y_test)
    return accuracy
```

Then run the following command:

```bash
$ villard run config.yaml
```

## Installation
    pip install git+https://github.com/ariaghora/villard