from typing import List, Optional, Dict, Any
from .db import get_db

AGENT_FIELDS = ['id','name','phone','created_at']

def row_to_dict(row):
    return {k: row[k] for k in AGENT_FIELDS}

def list_agents() -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute('SELECT * FROM agents ORDER BY created_at DESC').fetchall()
    return [row_to_dict(r) for r in rows]

def create_agent(name: str, phone: str) -> int:
    db = get_db()
    cur = db.execute('INSERT INTO agents (name, phone) VALUES (?, ?)', (name, phone))
    db.commit()
    return cur.lastrowid

def update_agent(agent_id: int, name: str, phone: str):
    db = get_db()
    db.execute('UPDATE agents SET name=?, phone=?, created_at=created_at WHERE id=?', (name, phone, agent_id))
    db.commit()

def delete_agent(agent_id: int):
    db = get_db()
    db.execute('DELETE FROM agents WHERE id=?', (agent_id,))
    db.commit()

def get_agent(agent_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute('SELECT * FROM agents WHERE id=?', (agent_id,)).fetchone()
    return row_to_dict(row) if row else None
