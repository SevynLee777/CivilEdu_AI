"""AI 助教回答快取：同一單元的相同問題直接回傳先前的回答，不再呼叫 Gemini。

刻意放在獨立模組：app.py 每次執行都會 importlib.reload(unit_manager)，
快取若放在 unit_manager 裡會一起被清掉；本模組不會被重載，快取可跨 session 共用。
快取只存在記憶體，Streamlit 重新啟動後清空。
"""
import hashlib
import re
import threading
import time
from collections import OrderedDict

TTL_SECONDS = 6 * 60 * 60
MAX_ENTRIES = 500

_lock = threading.Lock()
_entries = OrderedDict()  # key -> (expires_at, answer)

# 去掉空白與常見標點，讓「為什麼主權要獨立？」和「為什麼主權要獨立」視為同一題
_IGNORED_CHARS = re.compile(r"[\s?？!！。，,、.~～…]+")

def _key(unit_title, unit_content, question):
    normalized = _IGNORED_CHARS.sub("", question or "").lower()
    content_hash = hashlib.sha1((unit_content or "").encode("utf-8")).hexdigest()
    return (unit_title, content_hash, normalized)

def get(unit_title, unit_content, question):
    key = _key(unit_title, unit_content, question)
    with _lock:
        entry = _entries.get(key)
        if not entry:
            return None
        expires_at, answer = entry
        if expires_at < time.time():
            del _entries[key]
            return None
        _entries.move_to_end(key)
        return answer

def put(unit_title, unit_content, question, answer):
    key = _key(unit_title, unit_content, question)
    with _lock:
        _entries[key] = (time.time() + TTL_SECONDS, answer)
        _entries.move_to_end(key)
        while len(_entries) > MAX_ENTRIES:
            _entries.popitem(last=False)
