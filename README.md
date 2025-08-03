# tic-tac-toe

[Play tic-tac-toe against agent](https://jamesgadoury.github.io/tic-tac-toe/)

Python code and notebooks for using rl to create an optimal tic tac toe agent. 

## setup

[uv is great](https://docs.astral.sh/uv/). install it.
if you don't want to use `uv` (bad call) then you can just use regular python venv.
below instructions assume you installed `uv`.

create a venv
```
uv venv
```

install the env package by itself:
```
uv pip install .
```

if you want to run the scripts or work on the package, recommend running below instead:
```
uv pip install -e ".[dev]"
```

## run

all of below assumes you are in an virtual env created in above setup section.

tests:

```
python -m pytest tests/* -vv --durations=0 --log-cli-level=DEBUG
```
