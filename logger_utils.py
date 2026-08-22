import os
import json
from datetime import datetime
import pandas as pd

LOG_DIR = os.path.join(os.path.dirname(__file__), "student_logs")

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

def get_student_file_path(student_info):
    ensure_log_dir()
    class_name = str(student_info.get("class_name", "801")).strip()
    seat_num = str(student_info.get("seat_num", "1")).strip()
    name = str(student_info.get("name", "學生")).strip()
    
    filename = f"{class_name}_{seat_num}_{name}.json"
    return os.path.join(LOG_DIR, filename)

def load_student_record(student_info):
    filepath = get_student_file_path(student_info)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Failed to read student log {filepath}: {e}")
            
    return {
        "student_info": student_info,
        "diagnostic": None,
        "mastery_tests": [],
        "remedial_views": [],
        "ai_chats": [],
        "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def save_student_record(record):
    ensure_log_dir()
    student_info = record.get("student_info", {})
    filepath = get_student_file_path(student_info)
    record["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error] Failed to save student log {filepath}: {e}")

def save_student_profile(student_info, diagnostic_result):
    record = load_student_record(student_info)
    record["student_info"] = student_info
    record["diagnostic"] = {
        "score": diagnostic_result.get("score", 0),
        "level": diagnostic_result.get("level", "Level B"),
        "level_name": diagnostic_result.get("level_name", "🌿 觀念進階型"),
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_student_record(record)

def log_mastery_test(student_info, topic, score, total, pct, mastery_level, weak_tags, sa_responses):
    record = load_student_record(student_info)
    entry = {
        "topic": topic,
        "score": score,
        "total": total,
        "pct": round(pct, 1),
        "mastery_level": mastery_level,  # "🟢 精熟級", "🟡 基礎級", "🔴 待加強"
        "weak_tags": weak_tags,
        "sa_responses": sa_responses,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    record["mastery_tests"].append(entry)
    save_student_record(record)

def log_remedial_view(student_info, topic, level):
    record = load_student_record(student_info)
    entry = {
        "topic": topic,
        "level": level,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    record["remedial_views"].append(entry)
    save_student_record(record)

def log_ai_chat(student_info, question, answer):
    record = load_student_record(student_info)
    entry = {
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    record["ai_chats"].append(entry)
    save_student_record(record)

def get_all_student_records():
    ensure_log_dir()
    records = []
    if not os.path.exists(LOG_DIR):
        return records
        
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(LOG_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records.append(data)
            except Exception as e:
                print(f"[Error] Failed reading {fpath}: {e}")
    return records

def generate_csv_report():
    records = get_all_student_records()
    rows = []
    for r in records:
        info = r.get("student_info", {})
        diag = r.get("diagnostic") or {}
        tests = r.get("mastery_tests", [])
        chats = r.get("ai_chats", [])
        remedials = r.get("remedial_views", [])
        
        latest_test = tests[-1] if tests else {}
        avg_score_pct = round(sum(t.get("pct", 0) for t in tests) / len(tests), 1) if tests else 0
        weak_tags_str = ", ".join(latest_test.get("weak_tags", [])) if latest_test.get("weak_tags") else "無明顯弱點"
        
        rows.append({
            "班級": info.get("class_name", ""),
            "座號": info.get("seat_num", ""),
            "姓名": info.get("name", ""),
            "起點前測得分": diag.get("score", ""),
            "起點評定等級": diag.get("level_name", ""),
            "已自主檢測單元數": len(tests),
            "最新檢測單元": latest_test.get("topic", "尚未檢測"),
            "最新精熟狀態": latest_test.get("mastery_level", "未檢測"),
            "最新選擇題得分": f"{latest_test.get('score', 0)}/{latest_test.get('total', 0)}" if latest_test else "未檢測",
            "平均檢測正確率(%)": avg_score_pct,
            "需補強觀念標籤": weak_tags_str,
            "補強教材閱讀次數": len(remedials),
            "AI隨問隨答次數": len(chats),
            "最後活動時間": r.get("last_active", "")
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["班級", "座號"])
    return df
