# 25fa-dsc180a-team1
Paper reproduction team 1

## Getting Started (with Pixi)

### Prerequisites
- Git
- Pixi (one-time installation)

**macOS/Linux:**
```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

### Setup Instructions

1) **Clone the repository**
```bash
git clone <REPO_URL>
cd 25fa-dsc180a-team1
```

2) **Create the environment**
```bash
pixi install
```
- Pixi reads `pixi.toml` + `pixi.lock`, installs Python 3.11 and all dependencies
- Installs the local package `mimiciii-db` in editable mode

3) **Set up database connection**
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```
- Replace with your actual database connection string
- This environment variable is required for the `mimiciii_db` package to work

4) **Sanity check**
```bash
pixi run python -V
pixi run python -c "import mimiciii_db, sys; print('ok from', mimiciii_db.__file__); print(sys.executable)"
```

5) **Notebooks (optional)**
```bash
pixi run jupyter lab
```

Or create a named kernel:
```bash
pixi run python -m ipykernel install --user --name mimiciii-db
```
Then select `mimiciii-db` in VS Code/Jupyter.

6) **Common tasks**
```bash
pixi run test      # pytest -q
pixi run lint      # ruff check .
pixi run fmt       # black .
```

7) **Day-to-day usage**
```bash
pixi shell                 # open a shell in the environment
pixi add <pkg>             # add a conda-forge dependency
pixi add --pypi <pkg>      # add a PyPI dependency
pixi install               # re-solve after changes
pixi reinstall --locked    # CI / clean rebuild from lockfile
```

## Project Structure

```
25fa-dsc180a-team1/
├── src/
│   └── mimiciii_db/
│       ├── __init__.py
│       ├── db.py
│       ├── config.py
│       └── queries/
├── notebooks/
│   └── jason_test.ipynb
├── assets/
├── data/
├── dev_container/
├── logs/
├── pyproject.toml             # build config (Setuptools)
├── pixi.toml                  # project env/tasks config
├── pixi.lock                  # lockfile for reproducibility
└── README.md
```

## Usage

See the [mimiciii_db package documentation](src/mimiciii_db/README.md) for detailed usage examples and API reference.

## Troubleshooting

- **ImportError: mimiciii_db**: Make sure the folder is `src/mimiciii_db/` (three i's) and `pixi install` succeeded.
- **Version conflict (Python 3.10 vs 3.11)**: Align `requires-python` in `pyproject.toml` with the Python version pinned in `pixi.toml`, then `pixi install`.
- **Build error when adding editable**: Ensure `pyproject.toml` is present and uses Setuptools with `package-dir` + `packages.find` shown above; remove any stale `*.egg-info`, then `pixi install`.
