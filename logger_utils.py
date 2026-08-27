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
    seat_num = str(student_info.get("seat_num", "01")).strip()
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
        "unit_progress": {},
        "practice_history": [],
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

def log_unit_practice(student_info, unit_id, unit_title, score, total, mastered_tags, weak_tags):
    """
    Records a student's practice result in a unit.
    Calculates status:
    - 🌳 已掌握 (pct >= 80%)
    - 🌿 再練習 (50% <= pct < 80%)
    - 🌱 再看看 (pct < 50%)
    """
    record = load_student_record(student_info)
    pct = (score / total * 100) if total > 0 else 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if pct >= 80:
        status = "🌳 已掌握"
    elif pct >= 50:
        status = "🌿 再練習"
    else:
        status = "🌱 再看看"

    if "unit_progress" not in record:
        record["unit_progress"] = {}
        
    prev_progress = record["unit_progress"].get(unit_id, {})
    practice_count = prev_progress.get("practice_count", 0) + 1
    
    record["unit_progress"][unit_id] = {
        "unit_id": unit_id,
        "unit_title": unit_title,
        "status": status,
        "score": score,
        "total": total,
        "score_pct": round(pct, 1),
        "mastered_tags": mastered_tags,
        "weak_tags": weak_tags,
        "practice_count": practice_count,
        "last_updated": now_str
    }
    
    if "practice_history" not in record:
        record["practice_history"] = []
        
    record["practice_history"].append({
        "unit_id": unit_id,
        "unit_title": unit_title,
        "score": score,
        "total": total,
        "pct": round(pct, 1),
        "status": status,
        "weak_tags": weak_tags,
        "timestamp": now_str
    })
    
    save_student_record(record)
    return status

def log_ai_chat(student_info, unit_title, question, answer):
    record = load_student_record(student_info)
    if "ai_chats" not in record:
        record["ai_chats"] = []
    record["ai_chats"].append({
        "unit_title": unit_title,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_student_record(record)

def get_student_footprint(student_info):
    """Returns the student's personal learning footprints without any class rankings."""
    record = load_student_record(student_info)
    unit_progress = record.get("unit_progress", {})
    return list(unit_progress.values())

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

def get_teacher_learning_summary():
    """
    Builds clean, actionable summary for the teacher:
    - Completed today count (今天完成學習的學生數)
    - Need attention count (可能需要老師關心的學生數)
    - Concepts mastered well (學生們學習順利的觀念)
    - Concepts needing improvement (學生們需要加強學習的觀念)
    - Student details list (詳細資料)
    """
    records = get_all_student_records()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    completed_today_students = set()
    students_needing_attention = []
    
    smooth_concept_counts = {}
    weak_concept_counts = {}
    
    student_details = []
    
    for r in records:
        info = r.get("student_info", {})
        unit_prog = r.get("unit_progress", {})
        practice_hist = r.get("practice_history", [])
        last_active = r.get("last_active", "")
        
        # Check if active/practiced today
        practiced_today = False
        for p in practice_hist:
            if p.get("timestamp", "").startswith(today_str):
                practiced_today = True
                break
        if not practiced_today and last_active.startswith(today_str) and unit_prog:
            practiced_today = True
            
        student_key = f"{info.get('class_name','')}_{info.get('seat_num','')}_{info.get('name','')}"
        if practiced_today:
            completed_today_students.add(student_key)
            
        # Collect concepts & check attention need
        student_weak_concepts = set()
        student_has_struggle = False
        total_practices = 0
        
        for uid, prog in unit_prog.items():
            status = prog.get("status", "")
            total_practices += prog.get("practice_count", 1)
            
            if "🌱" in status or "再看看" in status:
                student_has_struggle = True
            for m_tag in prog.get("mastered_tags", []):
                smooth_concept_counts[m_tag] = smooth_concept_counts.get(m_tag, 0) + 1
            for w_tag in prog.get("weak_tags", []):
                weak_concept_counts[w_tag] = weak_concept_counts.get(w_tag, 0) + 1
                student_weak_concepts.add(w_tag)
                
        if student_has_struggle or len(student_weak_concepts) >= 2:
            students_needing_attention.append({
                "info": info,
                "weak_concepts": list(student_weak_concepts),
                "last_active": last_active
            })
            
        student_details.append({
            "class_name": info.get("class_name", ""),
            "seat_num": info.get("seat_num", ""),
            "name": info.get("name", ""),
            "completed_units_count": len(unit_prog),
            "unit_progress": unit_prog,
            "weak_concepts": list(student_weak_concepts),
            "total_practices": total_practices,
            "last_active": last_active
        })
        
    # Sort concept rankings
    sorted_smooth = sorted(smooth_concept_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_weak = sorted(weak_concept_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Sort student details by class and seat
    student_details.sort(key=lambda x: (str(x["class_name"]), str(x["seat_num"]).zfill(2)))
    
    return {
        "total_students": len(records),
        "completed_today_count": len(completed_today_students),
        "need_attention_count": len(students_needing_attention),
        "students_needing_attention": students_needing_attention,
        "smooth_concepts": [tag for tag, cnt in sorted_smooth[:5]],
        "weak_concepts": [tag for tag, cnt in sorted_weak[:5]],
        "student_details": student_details
    }

def generate_csv_report():
    """Exports structured student progress report for teacher."""
    records = get_all_student_records()
    rows = []
    for r in records:
        info = r.get("student_info", {})
        prog = r.get("unit_progress", {})
        chats = r.get("ai_chats", [])
        
        unit_summary_list = []
        all_weaks = []
        for uid, p in prog.items():
            unit_summary_list.append(f"{p.get('unit_title','')}: {p.get('status','')} (練習{p.get('practice_count',1)}次)")
            all_weaks.extend(p.get("weak_tags", []))
            
        rows.append({
            "班級": info.get("class_name", ""),
            "座號": info.get("seat_num", ""),
            "姓名": info.get("name", ""),
            "已完成學習單元數": len(prog),
            "各單元掌握狀態": "；".join(unit_summary_list) if unit_summary_list else "尚未練習",
            "尚未掌握的學習重點": "、".join(set(all_weaks)) if all_weaks else "無（觀念掌握良好）",
            "AI助教提問次數": len(chats),
            "最後活動時間": r.get("last_active", "")
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["班級", "座號"])
    return df
