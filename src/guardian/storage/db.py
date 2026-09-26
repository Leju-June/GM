import sqlite3
import json
from typing import Dict, Any, List

class ScanStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        
    def _get_conn(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Visited pages status
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    status TEXT,
                    depth INTEGER,
                    scanned_at TEXT,
                    error_msg TEXT
                )
            ''')
            
            # Findings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS findings (
                    id TEXT PRIMARY KEY,
                    url TEXT,
                    location TEXT,
                    evidence_text TEXT,
                    technique TEXT,
                    payload TEXT
                )
            ''')
            
            conn.commit()
            
    def set_meta(self, key: str, value: str):
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO scan_meta (key, value) VALUES (?, ?)', (key, value))
            
    def record_page_status(self, url: str, status: str, depth: int, error_msg: str = None):
        with self._get_conn() as conn:
            import datetime
            now = datetime.datetime.now().isoformat()
            conn.execute(
                'INSERT OR REPLACE INTO pages (url, status, depth, scanned_at, error_msg) VALUES (?, ?, ?, ?, ?)',
                (url, status, depth, now, error_msg)
            )
            
    def add_finding(self, finding_id: str, url: str, location: str, evidence_text: str, technique: str, full_payload: dict):
        with self._get_conn() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO findings (id, url, location, evidence_text, technique, payload) VALUES (?, ?, ?, ?, ?, ?)',
                (finding_id, url, location, evidence_text, technique, json.dumps(full_payload, ensure_ascii=False))
            )
            
    def get_all_findings(self) -> List[dict]:
        findings = []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT payload FROM findings')
            for row in cursor.fetchall():
                findings.append(json.loads(row[0]))
        return findings
