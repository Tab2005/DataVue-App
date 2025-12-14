# Database Migration Workflow (How to prevent Deployment Errors)

## The Problem
In local development (SQLite), we often delete the database file to "reset" it, or `Base.metadata.create_all` works because we start fresh.
In Production (PostgreSQL), the data is persistent. If you modify the code (e.g., add a column to `database.py`) but don't tell the production database to add that column, the code crashes (Schema Drift).

## The Solution: Alembic Migrations
Think of **Alembic** as "Git for your Database". It tracks changes and applies them safely.

## Standard Workflow for Database Changes

### 1. Modify the Python Model
Edit `backend/database.py` to add your new column or table.
```python
# Example: Adding a phone number to User
class User(Base):
    # ... existing columns ...
    phone_number = Column(String, nullable=True) # New Column
```

### 2. Generate a Migration Script (Local)
Run this command in your terminal to compare your Code vs Local DB and generate a script.
```bash
# In backend directory
alembic revision --autogenerate -m "Add phone number to users"
```
*This creates a new file in `backend/alembic/versions/` (e.g., `1234abcd_add_phone_number.py`).*

### 3. Review and Commit
Open the generated file. It should look like:
```python
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
```
**CRITICAL**: You MUST commit this file to Git!
```bash
git add backend/alembic/versions/
git commit -m "Add migration for phone number"
```

### 4. Deploy
When you push to GitHub and Zeabur redeploys:
1. Our backend automatically runs `alembic upgrade head` on startup (in `main.py`).
2. It detects the new migration file.
3. It applies the change (`ALTER TABLE ...`) to the production database automatically.

---

## Why it failed before?
1. **Missing Config**: The `alembic.ini` and `env.py` files were missing, so migration commands couldn't run. (I have fixed this).
2. **Missing Revisions**: We changed `database.py` (added `visible_ad_account_ids`) but never ran `alembic revision`.
3. **Drift**: Since no migration script existed, Production didn't know it needed to change.

## Conclusion
Going forward, whenever you change `database.py`, **ALWAYS run `alembic revision --autogenerate`** and commit the result. This ensures your Production Database remains in sync with your Code.
