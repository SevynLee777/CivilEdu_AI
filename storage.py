"""
資料持久層：有設定 SUPABASE_URL 與 SUPABASE_KEY 時，資料存到 Supabase（PostgreSQL）；
未設定時由呼叫端改用本地 JSON 檔案。

Streamlit Community Cloud 的檔案系統在重新啟動或重新部署後會還原，
因此部署到雲端時必須使用 Supabase，教材與學生歷程才不會遺失。
資料表結構請見 docs/supabase_setup.sql。
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

UNITS_TABLE = "units"
STUDENT_TABLE = "student_records"
REQUEST_TIMEOUT = 15


class StorageError(Exception):
    """遠端資料庫讀寫失敗。"""


def _get_setting(name):
    value = os.getenv(name)
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(name)
        except Exception:
            pass
    return value


def is_remote():
    """是否已設定 Supabase 連線資訊。"""
    return bool(_get_setting("SUPABASE_URL") and _get_setting("SUPABASE_KEY"))


def backend_name():
    return "Supabase" if is_remote() else "本地 JSON"


def _endpoint(table):
    return f"{_get_setting('SUPABASE_URL').rstrip('/')}/rest/v1/{table}"


def _headers(prefer=None):
    key = _get_setting("SUPABASE_KEY")
    headers = {"apikey": key, "Content-Type": "application/json"}
    # 舊版 JWT 金鑰（eyJ 開頭）需同時放在 Authorization；新版 sb_secret_ 金鑰只需 apikey
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _request(method, table, **kwargs):
    try:
        res = requests.request(method, _endpoint(table), timeout=REQUEST_TIMEOUT, **kwargs)
    except requests.RequestException as e:
        raise StorageError(f"無法連線到 Supabase：{e}") from e
    if res.status_code >= 400:
        raise StorageError(f"Supabase {method} {table} 失敗（HTTP {res.status_code}）：{res.text[:300]}")
    return res


def fetch_all(table):
    """依 position 排序取回整張表的 data 欄位。"""
    res = _request("GET", table, headers=_headers(),
                   params={"select": "data", "order": "position.asc,id.asc"})
    return [row["data"] for row in res.json()]


def fetch_one(table, row_id):
    res = _request("GET", table, headers=_headers(),
                   params={"select": "data", "id": f"eq.{row_id}"})
    rows = res.json()
    return rows[0]["data"] if rows else None


def upsert(table, rows):
    """rows: [(id, data, position), ...]；id 已存在則覆寫。"""
    if not rows:
        return
    payload = [{"id": rid, "data": data, "position": pos} for rid, data, pos in rows]
    _request("POST", table, headers=_headers("resolution=merge-duplicates,return=minimal"), json=payload)


def delete(table, row_id):
    _request("DELETE", table, headers=_headers("return=minimal"), params={"id": f"eq.{row_id}"})
