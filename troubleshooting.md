# Troubleshooting Log: Zeabur Deployment & Database Schema

## Incident: Super Admin Permissions & 500 Internal Server Errors
**Date:** 2025-12-13
**Environment:** Zeabur (Dev-SaaS)

### 1. Symptoms
- **Frontend**: "Super Admin Dashboard" button missing despite user having `is_super_admin=True` in theory.
- **Network**: 
    - Initial `CORS Error` (Red blocked requests).
    - Followed by `500 Internal Server Error` on `/api/users/me`.
    - Followed by `400 Bad Request` (after putting safety traps).
- **Backend Logs**: `pg8000.dbapi.ProgrammingError: column users.id does not exist`.

### 2. Root Cause Analysis
The issue was **Database Schema Drift**.
1.  **The Mismatch**: The unexpected error `column users.id does not exist` proved that the `users` table in the Zeabur database was **structurally invalid**. It likely had `google_id` or some other field, but lacked the standard `id` primary key expected by the current SQLAlchemy model.
2.  **Why it happened**: 
    - The database might have been created by an older version of the code or a manual script that didn't match the current `alembic` migrations.
    - Alembic's `alembic_version` table claimed "I am up to date", so it refused to "fix" the existing (but broken) table.

### 3. Solution Taken
We applied the **"Nuclear Option"** (Reset & Recreate):
1.  **Diagnosis Endpoint**: Added `/api/debug-db` to inspect schema (though the error message usually tells the story).
2.  **Destruction**: Used a temporary `/api/nuke-db` endpoint to execute `DROP TABLE users CASCADE`.
3.  **Recreation**: Modified `main.py` to call `init_db()` (SQLAlchemy `create_all`) on startup. This acts as a safety net: *If Alembic misses a table, create it anyway.*
4.  **Result**: The server recreated the correctly structured `users` table. The first login triggered the "First User = Super Admin" logic.

### 4. Prevention & Best Practices
To avoid this in the future:

#### A. Strict Migration Policy
- **Never** manually modify the database schema (Reference: `backend/database.py`).
- Always use `alembic revision --autogenerate -m "message"` to create changes.
- Always check migration scripts before applying.

#### B. Schema Verification Probe
- Keep a hidden/admin-only endpoint (like `/api/debug-db`) that can return the current table structure. This is invaluable when you cannot access the cloud database console directly.
- **Action Item**: Consider keeping `/api/debug-db` permanently but securing it with `Depends(get_super_admin)`.

#### C. The "Safety Net" Pattern
The fix we added to `main.py` is a good pattern for Development environments:
```python
# main.py
try:
    alembic.command.upgrade(alembic_cfg, "head")
    # Backup: Double check if tables exist
    init_db() 
except Exception:
    pass
```
*Note: In Production, you might want to rely solely on Alembic to ensure strict version control.*

### 5. Debugging Checklist (For Future Reference)
If Backend returns 500/Crash:
1.  **Check CORS**: Are requests turning red immediately? (Add URL to `main.py`).
2.  **Check DB Connection**: Can a simple script connect?
3.  **Trap the Error**: Wrap key functions (like `get_current_user`) in `try...except` to force the server to print the *real* error message (Traceback) instead of a generic "Internal Server Error".
4.  **Inspect Schema**: If code says "Column not found", believe it. The DB is wrong.

## Incident: 502 Bad Gateway / System Crash on Login
**Date:** 2025-12-13
**Symptoms:** 
- "Super Admin" permissions disappearing occasionally.
- API returning `502 Bad Gateway` and `CORS Error` on `GET /users/me`.
**Root Cause:**
- **Database Locking**: The `last_login` update logic was executing on *every* authenticated request.
- When multiple requests (User, Team, Account) fired simultaneously on page load, they all tried to WRITE to the same user row.
- This caused row-level locking, leading to timeout or connection pool exhaustion.
**Solution:**
- **Disable Write-on-Read**: Permanently commented out the `user.last_login = datetime.now()` line in `dependencies.py`.
- **Trade-off**: We sacrificed the "Last Login Time" feature for system stability.

## Incident: Invite Links Generating as 'localhost'
**Date:** 2025-12-13
**Symptoms:**
- Invite links on Zeabur environment looked like `http://localhost:5173/invite/...`.
**Root Cause:**
- `backend/routers/invites.py` had a hardcoded default URL.
**Solution:**
- **Dynamic Origin Detection**: Updated code to use `request.headers.get("origin")`.
- This ensures links automatically match the user's current domain (whether Localhost or Zeabur).
