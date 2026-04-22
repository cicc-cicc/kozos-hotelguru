import os
import sys
import runpy

# Ensure we're in project root
ROOT = os.path.dirname(os.path.dirname(__file__))
os.chdir(ROOT)

# Set env and argv as required by seed.py
os.environ["ALLOW_SEED"] = "1"
sys.argv = ["seed.py", "--force", "--no-backup"]

# Monkeypatch input() so seed's interactive confirmation receives CONFIRM
import builtins
builtins_input = builtins.input

def fake_input(prompt=""):
    print(prompt, end="")
    return "CONFIRM"

builtins.input = fake_input

try:
    runpy.run_path(os.path.join(ROOT, "seed.py"), run_name="__main__")
finally:
    builtins.input = builtins_input
