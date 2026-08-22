import os
import json
from docx import Document

def load_config():
    """Loads configuration settings from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to read config.json: {e}")
    return {
        "subject_name": "國中八年級公民",
        "assistant_role": "國中八年級公民科 AI 助教",
        "materials_dir": "materials"
    }

def format_topic_name_from_file(filename, first_para=""):
    base = os.path.splitext(filename)[0]
    
    # Custom mapping if matching known pattern
    if "08_01_L1" in base or "L1" in base:
        return "第1課：國家與民主政治"
    if "08_01_L2" in base or "L2" in base:
        return "第2課：憲法與權利保障"
        
    # If first paragraph has clear title
    if first_para and len(first_para) < 40:
        return first_para.strip()
        
    return base

def load_materials():
    """
    Dynamically loads all .docx files placed in the 'materials/' directory.
    Teachers can simply drop any textbook .docx file here!
    """
    config = load_config()
    materials = {}
    materials_dir = config.get("materials_dir", "materials")
    materials_path = os.path.abspath(materials_dir)
    
    if os.path.exists(materials_path) and os.path.isdir(materials_path):
        try:
            docx_files = [f for f in os.listdir(materials_path) if f.endswith('.docx') and not f.startswith('~$')]
            if docx_files:
                for filename in sorted(docx_files):
                    filepath = os.path.join(materials_path, filename)
                    doc = Document(filepath)
                    paras = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                    text_content = '\n'.join(paras)
                    
                    first_para = paras[0] if paras else ""
                    topic_name = format_topic_name_from_file(filename, first_para)
                    materials[topic_name] = text_content
                print(f"[Info] Loaded {len(materials)} topics from '{materials_dir}'.")
                return materials
        except Exception as e:
            print(f"[Error] Failed to load materials: {e}")

    return materials

if __name__ == "__main__":
    data = load_materials()
    print(f"Total topics loaded: {len(data)}")
    for key in data:
        print(f"- {key}: {len(data[key])} chars")
