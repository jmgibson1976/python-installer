# python-installer - Python Project Creator

python-installer is a CLI tool for quickly generating the base structure for a new python project.


## Installation
```bash
git clone https://github.com/<username>/python-installer.git
cd python-installer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy and fill in credentials
cp .env.example .env
```