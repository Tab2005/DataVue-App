from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def _check(db_path: Path) -> None:
    full = db_path.resolve()
    if not full.exists():
        print(f"MISSING: {full}")
        return

    con = sqlite3.connect(str(full))
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()]
    finally:
        con.close()

    print(str(full))
    print(f"  users columns: {len(cols)}")
    print(f"  has ga4_access_token: {'ga4_access_token' in cols}")
    print(f"  has ga4_refresh_token: {'ga4_refresh_token' in cols}")
    print(f"  has ga4_expires_at: {'ga4_expires_at' in cols}")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    backend_dir = here.parent

    # Paths we commonly end up with depending on cwd/env
    candidates = [
        backend_dir / "facebook_dashboard.db",
        backend_dir / "backend" / "facebook_dashboard.db",
        Path.cwd() / "facebook_dashboard.db",
        Path.cwd() / "backend" / "facebook_dashboard.db",
    ]

    seen: set[Path] = set()
    for p in candidates:
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        if rp in seen:
            continue
        seen.add(rp)
        _check(p)
