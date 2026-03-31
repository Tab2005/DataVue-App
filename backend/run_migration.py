# run_migration.py
import os
import sys
from alembic.config import Config
from alembic import command

# Add backend to sys.path to allow alembic to import models etc.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def run_upgrade():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migration upgrade successful.")

if __name__ == "__main__":
    try:
        run_upgrade()
    except Exception as e:
        print(f"Error running migration: {e}")
        sys.exit(1)
