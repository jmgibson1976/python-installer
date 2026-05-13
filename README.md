# Installer - Python Project Creator

Installer is a CLI tool for quickly generating the base structure for a new python project.


## Installation
```bash
git clone https://github.com/<username>/installer.git
cd installer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy and fill in credentials
cp .env.example .env
```