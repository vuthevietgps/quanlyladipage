from typing import List, Optional, Dict, Any
from .db import get_db

FIELDS = [
    'id','subdomain','agent','global_site_tag',
    'phone_tracking','zalo_tracking','form_tracking',
    'hotline_phone','zalo_phone','google_form_link',
    'status','original_filename','created_at','updated_at'
]


def row_to_dict(row) -> Dict[str, Any]:
    return {k: row[k] for k in FIELDS}


def create_landing(data: Dict[str, Any]) -> int:
    db = get_db()
    cols = [c for c in FIELDS if c not in ('id','created_at','updated_at') and c in data]
    placeholders = ','.join(['?']*len(cols))
    sql = f"INSERT INTO landing_pages ({','.join(cols)}) VALUES ({placeholders})"
    cur = db.execute(sql, [data[c] for c in cols])
    db.commit()
    return cur.lastrowid


def update_landing(landing_id: int, data: Dict[str, Any]):
    db = get_db()
    cols = [c for c in data.keys() if c in FIELDS and c not in ('id','created_at')]
    if not cols:
        return
    set_clause = ', '.join([f"{c}=?" for c in cols] + ["updated_at=CURRENT_TIMESTAMP"])
    sql = f"UPDATE landing_pages SET {set_clause} WHERE id=?"
    db.execute(sql, [data[c] for c in cols] + [landing_id])
    db.commit()


def get_landing(landing_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute("SELECT * FROM landing_pages WHERE id=?", (landing_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_by_subdomain(subdomain: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute("SELECT * FROM landing_pages WHERE subdomain=?", (subdomain,)).fetchone()
    return row_to_dict(row) if row else None


def list_landings(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    db = get_db()
    clauses = []
    params = []
    if 'agent' in filters and filters['agent']:
        clauses.append('agent LIKE ?')
        params.append(f"%{filters['agent']}%")
    if 'status' in filters and filters['status']:
        clauses.append('status=?')
        params.append(filters['status'])
    if 'q' in filters and filters['q']:
        clauses.append('subdomain LIKE ?')
        params.append(f"%{filters['q']}%")
    where = ('WHERE ' + ' AND '.join(clauses)) if clauses else ''
    sql = f"SELECT * FROM landing_pages {where} ORDER BY created_at DESC"
    rows = db.execute(sql, params).fetchall()
    return [row_to_dict(r) for r in rows]


def delete_landing(landing_id: int):
    db = get_db()
    db.execute("DELETE FROM landing_pages WHERE id=?", (landing_id,))
    db.commit()
