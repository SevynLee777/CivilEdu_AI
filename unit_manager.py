import os
import io
import json
import re
import uuid
import random
import copy
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv
import docx
import pdfplumber
import struct
import olefile

load_dotenv()

DB_FILE = os.path.join(os.path.dirname(__file__), "units_db.json")

# Candidate models for fallback
CANDIDATE_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.5-flash-lite',
    'gemini-flash-latest',
    'gemini-pro-latest'
]

def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    return key

def call_gemini_api(prompt, is_json=False):
    api_key = get_api_key()
    if not api_key:
        raise ValueError("未設定 GEMINI_API_KEY，無法呼叫 Gemini API。")

    client = genai.Client(api_key=api_key)
    last_exception = None
    config = types.GenerateContentConfig(
        response_mime_type="application/json"
    ) if is_json else None

    for m_name in CANDIDATE_MODELS:
        try:
            res = client.models.generate_content(
                model=m_name,
                contents=prompt,
                config=config
            )
            return res.text
        except Exception as e:
            last_exception = e
            continue

    raise Exception(f"所有 Gemini 模型呼叫失敗: {last_exception}")

def extract_json(text):
    """Extracts and parses JSON from model output safely."""
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try finding markdown code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    # Try finding outermost braces
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None

def extract_text_from_doc_bytes(file_bytes):
    """
    Parses legacy Word 97-2003 (.doc) binary file using pure Python olefile.
    Supports FIB Clx Piece Table parsing with fallback to raw stream extraction.
    """
    bio = io.BytesIO(file_bytes)
    if not olefile.isOleFile(bio):
        try:
            return file_bytes.decode('utf-8')
        except Exception:
            return file_bytes.decode('cp950', errors='ignore')

    try:
        ole = olefile.OleFileIO(bio)
        if not ole.exists('WordDocument'):
            return ""

        word_stream = ole.openstream('WordDocument').read()
        if len(word_stream) < 512:
            return ""

        flags = struct.unpack('<H', word_stream[0x000A:0x000C])[0]
        fWhichTblStm = (flags & 0x0200) != 0
        table_stm_name = '1Table' if fWhichTblStm else '0Table'

        if not ole.exists(table_stm_name):
            return _extract_raw_text_from_stream(word_stream)

        table_stream = ole.openstream(table_stm_name).read()
        fcClx, lcbClx = struct.unpack('<II', word_stream[418:426])

        if fcClx + lcbClx > len(table_stream):
            return _extract_raw_text_from_stream(word_stream)

        clx_data = table_stream[fcClx:fcClx + lcbClx]
        pos = 0
        while pos < len(clx_data) and clx_data[pos] == 1:
            cbGrpprl = struct.unpack('<H', clx_data[pos+1:pos+3])[0]
            pos += 3 + cbGrpprl

        if pos < len(clx_data) and clx_data[pos] == 2:
            lcb = struct.unpack('<I', clx_data[pos+1:pos+5])[0]
            pos += 5
            plcfpcd = clx_data[pos:pos+lcb]
            n = (lcb - 4) // 12
            cps = [struct.unpack('<I', plcfpcd[i*4:(i+1)*4])[0] for i in range(n+1)]
            pcds = plcfpcd[(n+1)*4:]

            full_text = []
            for i in range(n):
                pcd = pcds[i*8:(i+1)*8]
                fc = struct.unpack('<I', pcd[2:6])[0]
                fCompressed = (fc & 0x40000000) != 0
                actual_fc = (fc & ~0x40000000)
                char_count = cps[i+1] - cps[i]

                if fCompressed:
                    actual_fc = actual_fc // 2
                    piece_bytes = word_stream[actual_fc : actual_fc + char_count]
                    try:
                        txt = piece_bytes.decode('cp950')
                    except Exception:
                        txt = piece_bytes.decode('latin1', errors='ignore')
                else:
                    piece_bytes = word_stream[actual_fc : actual_fc + char_count * 2]
                    txt = piece_bytes.decode('utf-16-le', errors='ignore')

                full_text.append(txt)

            result_text = ''.join(full_text)
            result_text = result_text.replace('\r\n', '\n').replace('\r', '\n').replace('\x07', '\t').replace('\x0c', '\n')
            result_text = re.sub(r'[\x00-\x08\x0b\x0e-\x1f]', '', result_text)
            return result_text.strip()
        else:
            return _extract_raw_text_from_stream(word_stream)
    except Exception as e:
        print(f"[Warning] OLE doc 解析異常: {e}")
        return _extract_raw_text_from_stream(word_stream if 'word_stream' in locals() else file_bytes)

def _extract_raw_text_from_stream(stream_bytes):
    """備援：自二進位流中提取連續可讀文字"""
    utf16 = stream_bytes.decode('utf-16-le', errors='ignore')
    clean16 = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]', '', utf16)
    lines16 = [l.strip() for l in clean16.splitlines() if len(l.strip()) > 3]
    if len(lines16) > 5:
        return '\n'.join(lines16)
    cp950 = stream_bytes.decode('cp950', errors='ignore')
    clean950 = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]', '', cp950)
    lines950 = [l.strip() for l in clean950.splitlines() if len(l.strip()) > 3]
    return '\n'.join(lines950)

def extract_text_from_file_upload(file_input, filename=""):
    """
    Extracts text from uploaded file (supports .docx, .doc, .pdf, .txt, .md).
    file_input can be bytes or a file-like buffer (e.g. Streamlit UploadedFile).
    Returns (suggested_title, extracted_text).
    """
    if hasattr(file_input, 'name') and not filename:
        filename = file_input.name
    if hasattr(file_input, 'seek'):
        try:
            file_input.seek(0)
        except Exception:
            pass
    if hasattr(file_input, 'read'):
        file_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        file_bytes = file_input
    else:
        file_bytes = bytes(file_input)
    if hasattr(file_input, 'seek'):
        try:
            file_input.seek(0)
        except Exception:
            pass

    base_name = re.sub(r'\.[^.]+$', '', filename).strip() if filename else "新學習單元"
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    extracted_text = ""
    try:
        if ext == 'docx':
            doc = docx.Document(io.BytesIO(file_bytes))
            extracted_text = '\n'.join([p.text.strip() for p in doc.paragraphs if p.text.strip()])
        elif ext == 'doc':
            extracted_text = extract_text_from_doc_bytes(file_bytes)
        elif ext == 'pdf':
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    ptxt = page.extract_text()
                    if ptxt:
                        pages_text.append(ptxt.strip())
                extracted_text = '\n\n'.join(pages_text)
        elif ext in ['txt', 'md']:
            try:
                extracted_text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                extracted_text = file_bytes.decode('cp950', errors='ignore')
        else:
            try:
                extracted_text = file_bytes.decode('utf-8')
            except Exception:
                extracted_text = file_bytes.decode('cp950', errors='ignore')
    except Exception as e:
        print(f"[Warning] 檔案解析異常: {e}")
        try:
            extracted_text = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            extracted_text = ""

    return base_name, extracted_text.strip()

def randomize_practice_questions(unit, num_questions=8):
    """
    Randomly selects questions from unit question pool, shuffles question order,
    and shuffles option choices (A, B, C, D) while dynamically updating correct_index.
    """
    raw_qs = unit.get("practice_questions", [])
    if not raw_qs:
        return []

    # 1. 隨機選題
    sample_size = min(num_questions, len(raw_qs))
    selected_qs = random.sample(raw_qs, sample_size)

    # 2. 隨機排題序
    random.shuffle(selected_qs)

    # 3. 隨機排選項
    processed_qs = []
    for q in selected_qs:
        q_copy = copy.deepcopy(q)
        original_options = q_copy.get("options", [])
        orig_corr_idx = q_copy.get("correct_index", 0)

        # 乾淨去除既有前綴
        clean_options = []
        for opt in original_options:
            cleaned = re.sub(r'^[A-Da-d]\s*[\)\.\、\:\-]?\s*', '', str(opt)).strip()
            clean_options.append(cleaned)

        if 0 <= orig_corr_idx < len(clean_options):
            correct_content = clean_options[orig_corr_idx]
        else:
            correct_content = clean_options[0] if clean_options else ""

        # 打亂選項
        random.shuffle(clean_options)

        # 重新編寫 A) B) C) D)
        new_options = [f"{chr(65 + idx)}) {opt_text}" for idx, opt_text in enumerate(clean_options)]
        new_corr_idx = clean_options.index(correct_content) if correct_content in clean_options else 0

        q_copy["options"] = new_options
        q_copy["correct_index"] = new_corr_idx
        processed_qs.append(q_copy)

    return processed_qs

def generate_unit_bundle(title, raw_content):
    """
    Analyzes textbook content and automatically generates:
    1. Key learning points (萃取學習重點 4 條)
    2. Easy plain-language content (國中生白話整理)
    3. Life & campus cases (生活化案例 4 個：校園、日常、網路、社區/社會)
    4. Mermaid concept mind map (直式樹狀心智圖，以 graph LR 展開)
    5. Practice questions (小試身手題庫池，請出滿 16 道素養單選題，供系統隨機抽題)
    6. Remediation guides (答錯補充說明與避坑指南)
    """
    prompt = f"""
你是一位充滿教學熱忱、深諳國中八年級學生語言的【公民科名師】。
教師剛剛輸入了課本教材（單元名稱：【{title}】），請依據此教材，以「國中生容易理解、生活化、無壓力」為原則，為系統自動產生完整的學習單元包裹。
【核心要求】：
1. 生活案例請出滿 4 個生動實例（包含校園生活、日常生活、網路社群、社區公共生活）。
2. 小試身手題庫池請出滿 16 道生活情境單選題（q1 至 q16），讓系統每次可動態隨機抽取 8 題測驗，題題精彩。

【課本教材原文】：
{raw_content[:12000]}

請輸出結構嚴謹的純 JSON，包含以下所有欄位（請嚴格使用繁體中文）：
{{
  "key_points": [
    "學習重點1（20~40字，國中生白話易懂，清楚點出核心觀念）",
    "學習重點2（20~40字）",
    "學習重點3（20~40字）",
    "學習重點4（20~40字）"
  ],
  "easy_content": "### 🌟 輕鬆看懂這堂課\\n\\n這裡使用生動活潑、多用條列、粗體與emoji的白話文，將教材核心概念完整拆解給國中生，約300-500字。包含重點觀念拆解與記憶口訣。",
  "life_cases": [
    {{
      "title": "🏫 校園生活情境實例1（例如：班級自治與幹部選舉）",
      "story": "生動的生活故事敘述（約100字），說明這個公民概念如何出現在學生的校園生活中。",
      "takeaway": "💡 思辨焦點：一句話總結對應的公民核心觀念。"
    }},
    {{
      "title": "🏪 日常生活情境實例2（例如：超商消費與法治常識）",
      "story": "生動的生活故事敘述（約100字）。",
      "takeaway": "💡 思辨焦點：一句話總結。"
    }},
    {{
      "title": "📱 網路社群情境實例3（例如：網路言論自律與個資保護）",
      "story": "生動的生活故事敘述（約100字）。",
      "takeaway": "💡 思辨焦點：一句話總結。"
    }},
    {{
      "title": "🚌 社區公共情境實例4（例如：里民大會與公民參與）",
      "story": "生動的生活故事敘述（約100字）。",
      "takeaway": "💡 思辨焦點：一句話總結。"
    }}
  ],
  "mindmap_mermaid": "graph LR\\n  A[\"{title}\"] --> B[\"核心概念一\"]\\n  A --> C[\"核心概念二\"]\\n  B --> D[\"生活實例/重點細節\"]\\n  C --> E[\"生活實例/重點細節\"]",
  "practice_questions": [
    {{
      "id": "q1",
      "concept_tag": "核心觀念標籤（如：國家要素、民主政治原則、憲法位階等）",
      "question": "第1題生活情境單選練習題",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 0,
      "explanation": "親切簡短的解析，說明為何選這個答案。"
    }},
    {{
      "id": "q2",
      "concept_tag": "核心觀念標籤",
      "question": "第2題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 1,
      "explanation": "解析說明"
    }},
    {{
      "id": "q3",
      "concept_tag": "核心觀念標籤",
      "question": "第3題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 2,
      "explanation": "解析說明"
    }},
    {{
      "id": "q4",
      "concept_tag": "核心觀念標籤",
      "question": "第4題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 3,
      "explanation": "解析說明"
    }},
    {{
      "id": "q5",
      "concept_tag": "核心觀念標籤",
      "question": "第5題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 0,
      "explanation": "解析說明"
    }},
    {{
      "id": "q6",
      "concept_tag": "核心觀念標籤",
      "question": "第6題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 1,
      "explanation": "解析說明"
    }},
    {{
      "id": "q7",
      "concept_tag": "核心觀念標籤",
      "question": "第7題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 2,
      "explanation": "解析說明"
    }},
    {{
      "id": "q8",
      "concept_tag": "核心觀念標籤",
      "question": "第8題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 3,
      "explanation": "解析說明"
    }},
    {{
      "id": "q9",
      "concept_tag": "核心觀念標籤",
      "question": "第9題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 0,
      "explanation": "解析說明"
    }},
    {{
      "id": "q10",
      "concept_tag": "核心觀念標籤",
      "question": "第10題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 1,
      "explanation": "解析說明"
    }},
    {{
      "id": "q11",
      "concept_tag": "核心觀念標籤",
      "question": "第11題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 2,
      "explanation": "解析說明"
    }},
    {{
      "id": "q12",
      "concept_tag": "核心觀念標籤",
      "question": "第12題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 3,
      "explanation": "解析說明"
    }},
    {{
      "id": "q13",
      "concept_tag": "核心觀念標籤",
      "question": "第13題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 0,
      "explanation": "解析說明"
    }},
    {{
      "id": "q14",
      "concept_tag": "核心觀念標籤",
      "question": "第14題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 1,
      "explanation": "解析說明"
    }},
    {{
      "id": "q15",
      "concept_tag": "核心觀念標籤",
      "question": "第15題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 2,
      "explanation": "解析說明"
    }},
    {{
      "id": "q16",
      "concept_tag": "核心觀念標籤",
      "question": "第16題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 3,
      "explanation": "解析說明"
    }}
  ],
  "remediation_guides": {{
    "核心觀念標籤1": {{
      "concept": "核心觀念標籤1",
      "simple_explanation": "答錯時給學生的極簡白話說明與比喻（約50-80字）",
      "life_case": "超貼切的生活比喻",
      "pitfall_tip": "避坑判斷口訣（一句話秒懂，例如：XXX是...不是...）"
    }},
    "核心觀念標籤2": {{
      "concept": "核心觀念標籤2",
      "simple_explanation": "答錯時給學生的極簡白話說明與比喻",
      "life_case": "生活比喻",
      "pitfall_tip": "避坑判斷口訣"
    }}
  }}
}}
"""
    try:
        raw_output = call_gemini_api(prompt, is_json=True)
        data = extract_json(raw_output)
        if data and "key_points" in data and "practice_questions" in data:
            return data
    except Exception as e:
        print(f"[Warning] AI Bundle generation exception: {e}")

    # Safe fallback if AI parsing fails
    return get_default_fallback_bundle(title, raw_content)

def get_default_fallback_bundle(title, raw_content):
    """Fallback generator ensuring the unit is never lost if API has temporary timeout."""
    return {
        "key_points": [
            f"掌握【{title}】的核心定義與概念。",
            "理解公民生活中的相關規範與權利義務。",
            "能夠將所學觀念運用於日常校園生活情境。",
            "分辨常見的易混淆概念與核心精神。"
        ],
        "easy_content": f"### 🌟 【{title}】重點速覽\n\n本單元帶領大家認識**{title}**的核心觀念。請仔細閱讀課本內容，掌握與我們日常生活息息相關的公民素養與社會運作原則！",
        "life_cases": [
            {
                "title": "🏫 校園生活情境實例",
                "story": f"在學校班級自治與同儕互動中，{title}所提及的原則能幫助我們做出更公平、更具同理心的決定。",
                "takeaway": "💡 觀念落實於生活中，就是最好的公民實踐！"
            },
            {
                "title": "🏪 日常生活情境實例",
                "story": f"走入生活周遭的超商、公共場所，{title}的規範隨處可見，維持社會井然有序。",
                "takeaway": "💡 規則守護每位公民的安全與自由！"
            },
            {
                "title": "📱 網路社群情境實例",
                "story": f"在網路虛擬世界中發表言論與交流，同樣要落實{title}的理性溝通與法治觀念。",
                "takeaway": "💡 數位時代更需要優質公民自律素養！"
            },
            {
                "title": "🚌 社區公共情境實例",
                "story": f"參與社區或公共活動時，透過理性溝通與互助合作，實現{title}的公益精神。",
                "takeaway": "💡 公共參與由基層開始，共創美好生活！"
            }
        ],
        "mindmap_mermaid": f"""graph LR\n  A["{title}"] --> B["核心觀念"]\n  A --> C["生活實踐"]\n  B --> D["重點理解"]\n  C --> E["日常應用"]""",
        "practice_questions": [
            {
                "id": "q1",
                "concept_tag": f"{title}核心觀念",
                "question": f"下列關於【{title}】的敘述，何者最符合現代公民的基本素養與民主法治精神？",
                "options": [
                    "A) 尊重多元意見並依法遵循制度",
                    "B) 僅依個人喜好決定，無需受規範約束",
                    "C) 完全依賴少數權力者代為決定所有事務",
                    "D) 遇到爭議時以爭吵取代溝通討論"
                ],
                "correct_index": 0,
                "explanation": "現代民主法治的核心即為尊重多元意見、遵守共同規範，並透過溝通達成共識。"
            },
            {
                "id": "q2",
                "concept_tag": f"{title}核心觀念",
                "question": f"在探討【{title}】時，我們若要在團體生活中達成共識，最適當的做法為何？",
                "options": [
                    "A) 強制所有人接受單一意見",
                    "B) 透過理性對話與少數服從多數原則",
                    "C) 逃避問題不進行任何討論",
                    "D) 由身分地位最高者直接指定"
                ],
                "correct_index": 1,
                "explanation": "民主社會透過理性溝通討論與少數服從多數、多數尊重少數原則達成共識。"
            },
            {
                "id": "q3",
                "concept_tag": f"{title}生活實踐",
                "question": f"下列哪一種校園情境，最能具體落實【{title}】所強調的公民自律與合作精神？",
                "options": [
                    "A) 共同訂定班規並切實遵守執行",
                    "B) 私下違反校規只要沒被抓到就好",
                    "C) 將公共環境清潔責任全推給值日生",
                    "D) 選出幹部後便不再關心班級公共事務"
                ],
                "correct_index": 0,
                "explanation": "公民自治的基礎在於共同制定規範、共同參與並以自律精神維護團體秩序。"
            },
            {
                "id": "q4",
                "concept_tag": f"{title}生活實踐",
                "question": f"遇到公共議題看法不同時，具備【{title}】素養的同學通常會採取何種態度？",
                "options": [
                    "A) 在網路上使用情緒化文字互相謾罵",
                    "B) 傾聽對方的論據並以客觀事實論證",
                    "C) 聯合其他朋友排擠意見不同者",
                    "D) 拒絕接受任何不同的觀點"
                ],
                "correct_index": 1,
                "explanation": "面對不同觀點，理性傾聽、尊重包容並依據事實溝通是優質公民的必備素養。"
            },
            {
                "id": "q5",
                "concept_tag": f"{title}核心觀念",
                "question": f"下列何者最能說明【{title}】中「權利與義務」之間的關係？",
                "options": [
                    "A) 只要享受權利，不需要承擔任何義務",
                    "B) 權利與義務互為表裡，享受權利同時應盡相應責任",
                    "C) 義務是給弱勢群體承擔，強者享有完全自由",
                    "D) 權利可以無限擴張，不受任何法律限制"
                ],
                "correct_index": 1,
                "explanation": "現代公民社會強調權利與義務相對等，個人的自由以不妨礙他人之自由為界線。"
            },
            {
                "id": "q6",
                "concept_tag": f"{title}生活實踐",
                "question": f"在民主法治架構下，若發現既有規範有未盡完善之處，最適當的解決途徑為何？",
                "options": [
                    "A) 直接聚眾鬧事破壞現有體制",
                    "B) 依正當合法管道提出建言與修改討論",
                    "C) 假裝沒看見並放棄自己的權益",
                    "D) 私下私了不遵循法律途徑"
                ],
                "correct_index": 1,
                "explanation": "法治精神在於遵循正當法律程序，若制度有不足應透過法定救濟或修法管道反映。"
            },
            {
                "id": "q7",
                "concept_tag": f"{title}核心觀念",
                "question": f"在【{title}】的原則中，關於「公平正義」的體現，下列何者敘述最正確？",
                "options": [
                    "A) 給予所有人完全一模一樣的待遇，不論個別需求",
                    "B) 在合理條件下兼顧實質平等，保障弱勢基本需求",
                    "C) 優勝劣汰，完全不提供任何社會救助",
                    "D) 只照顧特定族群，忽視多數人權益"
                ],
                "correct_index": 1,
                "explanation": "公平正義不僅強調形式平等，更重視實質平等，給予弱勢群體適當保障以實現社會公平。"
            },
            {
                "id": "q8",
                "concept_tag": f"{title}生活實踐",
                "question": f"落實【{title}】之核心素養，最重要的日常實踐起點為何？",
                "options": [
                    "A) 從身邊的校園與家庭生活中的尊重與守法做起",
                    "B) 等到長大成年後才需要關心公共事務",
                    "C) 只要考試得高分，生活行徑無需受到規範",
                    "D) 將所有責任託付給政府，個人不必參與"
                ],
                "correct_index": 0,
                "explanation": "公民素養是由內而外、從日常生活做起的實踐歷程，每位同學都能從生活同儕互動中展現公民精神。"
            },
            {
                "id": "q9",
                "concept_tag": f"{title}核心觀念",
                "question": f"關於【{title}】的法治規範，下列何者最符合依法行政的要求？",
                "options": [
                    "A) 政府任何公權力施政皆須有明確法規依據",
                    "B) 行政長官可任意依個人喜好制定命令裁罰",
                    "C) 只要出發點良好，違反法律程序也無妨",
                    "D) 法律僅用於約束平民，公職人員免受約束"
                ],
                "correct_index": 0,
                "explanation": "法治國家的核心精神即為依法行政，公權力行使必須嚴格遵循法律規範。"
            },
            {
                "id": "q10",
                "concept_tag": f"{title}生活實踐",
                "question": f"在處理團體內部的公共爭端時，下列何種溝通方式最能展現【{title}】的精神？",
                "options": [
                    "A) 理性陳述事實並兼顧對方正當權益",
                    "B) 透過網路霸凌逼迫對方退讓",
                    "C) 拒絕聆聽直接單方面終止溝通",
                    "D) 動用私力救濟採取肢體衝突"
                ],
                "correct_index": 0,
                "explanation": "理性客觀、尊重包容是化解爭端與實踐公民民主素養的最佳途徑。"
            },
            {
                "id": "q11",
                "concept_tag": f"{title}核心觀念",
                "question": f"在【{title}】中，關於自由權利的界線，下列名言何者最為貼切？",
                "options": [
                    "A) 個人自由的界限，就是他人自由的起點",
                    "B) 只要我想做，沒有什麼不可以",
                    "C) 強者的自由就是唯一的真理",
                    "D) 自由意味著不受任何社會道德拘束"
                ],
                "correct_index": 0,
                "explanation": "個人的自由並非漫無限制，以不妨礙他人的權利與社會公共秩序為界線。"
            },
            {
                "id": "q12",
                "concept_tag": f"{title}生活實踐",
                "question": f"下列哪一項行為最能體現公民對【{title}】中公共利益的積極貢獻？",
                "options": [
                    "A) 主動參與校園環保志工與公共事務討論",
                    "B) 將垃圾隨手丟在鄰居家門口",
                    "C) 為了自身方便任意佔用公用走道",
                    "D) 破壞公物以宣洩個人負面情緒"
                ],
                "correct_index": 0,
                "explanation": "關心公共事務、積極參與公共志工服務，是促進公共利益與公民社會成長的重要力量。"
            },
            {
                "id": "q13",
                "concept_tag": f"{title}核心觀念",
                "question": f"下列關於【{title}】中多數決原則的運用，何者最為健全？",
                "options": [
                    "A) 多數決應建立在充分討論、資訊公開與保障少數權益的前提下",
                    "B) 多數決可以直接投票剝奪少數人的生存權益",
                    "C) 只要多數贊成，任何決議皆不受法律與憲法限制",
                    "D) 多數決意味著少數人完全沒有發言權"
                ],
                "correct_index": 0,
                "explanation": "健全的民主多數決必須以保護少數基本權益與充分理性溝通為基礎。"
            },
            {
                "id": "q14",
                "concept_tag": f"{title}生活實踐",
                "question": f"遇到網路未經證實的重大公共謠言時，具備【{title}】思辨素養的同學應當如何應對？",
                "options": [
                    "A) 先行查證事實真偽，不盲目轉發散布",
                    "B) 立即轉發給所有群組引發恐慌",
                    "C) 添油加醋改寫故事吸引流量",
                    "D) 留言謾罵被報導之當事人"
                ],
                "correct_index": 0,
                "explanation": "數位公民具備媒體識讀與查證能力，不輕信轉傳假訊息，共同維護優質網路環境。"
            },
            {
                "id": "q15",
                "concept_tag": f"{title}核心觀念",
                "question": f"在【{title}】所建立的制度架構下，權力分立與監督制衡的核心目的為何？",
                "options": [
                    "A) 防止權力集中導致濫權腐敗，保障人民權利",
                    "B) 讓各機關互相拖延使得政府無所作為",
                    "C) 增加公務人員編制以提高行政成本",
                    "D) 讓司法機關聽從行政長官指派"
                ],
                "correct_index": 0,
                "explanation": "權力分立與制衡機制是為了防範公權力集中與濫權，保障人民基本人權不受侵害。"
            },
            {
                "id": "q16",
                "concept_tag": f"{title}生活實踐",
                "question": f"當個人權益受到公權力或他人不法侵害時，依據【{title}】之原則，最適當之應對方式為何？",
                "options": [
                    "A) 依循正當法律管道與程序尋求救濟與協調",
                    "B) 糾眾私刑報復破壞社會秩序",
                    "C) 隱忍承受不尋求任何協助",
                    "D) 在社群媒體以不實言論誹謗反擊"
                ],
                "correct_index": 0,
                "explanation": "現代法治社會禁止私力救濟，遇爭議與侵害應遵循法定程序請求司法或行政救濟。"
            }
        ],
        "remediation_guides": {
            f"{title}核心觀念": {
                "concept": f"{title}核心觀念",
                "simple_explanation": "公民社會中，每個制度都是為了保障大眾權益與維持社會秩序所建立的。",
                "life_case": "就像班規是由大家共同討論並遵守，以確保每位同學安心學習。",
                "pitfall_tip": "避坑口訣：權利與義務並重，自由以不妨礙他人為界線！"
            },
            f"{title}生活實踐": {
                "concept": f"{title}生活實踐",
                "simple_explanation": "在日常生活中尊重多元、遵守程序、理性表達，就是最好的公民素養展現。",
                "life_case": "就像分組討論時專心聆聽同學發言，再客觀提出自己的建議。",
                "pitfall_tip": "避坑口訣：理性溝通、尊重包容、依法行事！"
            }
        }
    }

def get_builtin_default_units():
    """Returns rich pre-configured default units for Chapter 1 and Chapter 2."""
    return [
    {
        "id": "unit_l1",
        "title": "第1課：國家與民主政治",
        "created_at": "2026-08-20 09:00:00",
        "updated_at": "2026-08-20 09:00:00",
        "raw_content": "國家組成四大要素為人民、領土、政府、主權。主權對內最高、對外獨立自主。民主政治的核心原則包含民意政治、責任政治、法治政治、政黨政治。政務官政策失誤須下臺負責體現責任政治；人民投票決定公職人員體現民意政治與主權在民。",
        "key_points": [
            "國家的四大要素：人民、領土、政府、主權。缺一不可！",
            "主權的特質：對內具有「最高性」，對外具有「獨立自主性」。",
            "民主政治四大核心原則：民意政治（聽人民的）、責任政治（做不好下臺）、法治政治（依法辦事）、政黨政治（良性競爭）。",
            "公民的政治參與：投票是主權在民最直接的展現方式。"
        ],
        "easy_content": "### 🌟 3 分鐘白話搞懂「國家與民主」\n\n- **🏛️ 國家就像一間超大超商**：\n  - **人民**：顧客與店員（住在這裡的人）。\n  - **領土**：店面與倉庫範圍（土地、領海、領空）。\n  - **政府**：店長與管理團隊（負責組織與運作）。\n  - **主權**：這家店的營業執照與經營決策權（自己做主，隔壁店家不能來指揮！）。\n\n- **🗳️ 民主政治四大原則秒記法**：\n  1. **民意政治**：政府做事情要聽老闆（全體人民）的想法。\n  2. **責任政治**：店長政策出包造成虧損，必須向大家道歉或請辭下臺！\n  3. **法治政治**：大家都要守法，就算總統也不能違法。\n  4. **政黨政治**：不同政黨互相競爭與監督，避免單一政黨獨裁。",
        "life_cases": [
            {
                "title": "🏫 校園生活：班會選幹部與制定班規",
                "story": "小明班上每學期初都會透過不記名投票選出班長，並共同投票表決班規。如果班長沒有盡責服務，大家可以在班會提出改選。",
                "takeaway": "💡 這就是「民意政治」與「責任政治」在班級生活的具體縮影！"
            },
            {
                "title": "🏪 日常生活：出國護照與主權象徵",
                "story": "小華拿著中華民國護照出國旅遊，在海關順利通關。護照代表了國家主權對國民的保護與身分確認。",
                "takeaway": "💡 主權對外獨立，讓國民在國際上擁有明確的法律地位與保護。"
            },
            {
                "title": "📱 網路社群：學生會粉專留言與網路公民權",
                "story": "小萱在學生會粉專對校園手機使用規範提出具體建議，並獲得許多同學按讚討論，學生會因此召開座談會邀請學校行政主管聆聽學生想法。",
                "takeaway": "💡 透過理性多元的管道參與公共事務、表達公民意見，正是「民意政治」在校園的蓬勃實踐！"
            },
            {
                "title": "🚌 社區生活：里民大會參與與公共設施公聽會",
                "story": "阿豪和家人一起參加里民大會，大家對公園遊樂設施整修及人行道拓寬踴躍發言投票，里長認真記錄並向區公所反映爭取經費。",
                "takeaway": "💡 地方自治與基層公民參與，讓民主政治不再只是選舉，而是落實在每個人的日常生活周遭！"
            }
        ],
        "mindmap_mermaid": "graph LR\n  A[\"第1課：國家與民主政治\"] --> B[\"國家的四大要素\"]\n  A --> C[\"民主政治四大原則\"]\n  B --> B1[\"人民 (國民群體)\"]\n  B --> B2[\"領土 (領陸/領海/領空)\"]\n  B --> B3[\"政府 (行政統治組織)\"]\n  B --> B4[\"主權 (對內最高/對外獨立)\"]\n  C --> C1[\"民意政治 (主權在民)\"]\n  C --> C2[\"責任政治 (失職下臺)\"]\n  C --> C3[\"法治政治 (依法行政)\"]\n  C --> C4[\"政黨政治 (良性競爭)\"]",
        "practice_questions": [
            {
                "id": "q1",
                "concept_tag": "國家要素",
                "question": "某國在國際上與其他國家建立邦交、簽署條約，且不受鄰近大國的干涉與控制。這最能體現國家組成四要素中的哪一項？",
                "options": [
                    "A) 人民",
                    "B) 領土",
                    "C) 政府",
                    "D) 主權"
                ],
                "correct_index": 3,
                "explanation": "主權是指國家對內擁有最高統治權，對外具有獨立自主性，不受他國干涉。"
            },
            {
                "id": "q2",
                "concept_tag": "責任政治",
                "question": "某部會推動新政策時發生重大疏失，引發社會爭議，該部部長隨即召開記者會向國人致歉並遞出辭呈。這符合民主政治的哪一項核心原則？",
                "options": [
                    "A) 責任政治",
                    "B) 民意政治",
                    "C) 法治政治",
                    "D) 政黨政治"
                ],
                "correct_index": 0,
                "explanation": "政務官對政策成敗負責並主動請辭下臺，是「責任政治」的代表表現。"
            },
            {
                "id": "q3",
                "concept_tag": "民意政治",
                "question": "我國憲法規定「中華民國之主權屬於國民全體」，民眾定期透過投票選出立法委員與縣市長。這主要展現了哪一項原則？",
                "options": [
                    "A) 司法獨立",
                    "B) 民意政治與主權在民",
                    "C) 地方自治",
                    "D) 權力集中"
                ],
                "correct_index": 1,
                "explanation": "透過定期投票選出公職人員以反映多數人民意願，即為民意政治。"
            },
            {
                "id": "q4",
                "concept_tag": "法治政治",
                "question": "行政機關推行各項行政作為時，必須嚴格依循立法院通過的法律，不得任意開罰或侵犯人民權利。這屬於哪一項民主原則？",
                "options": [
                    "A) 責任政治",
                    "B) 政黨政治",
                    "C) 法治政治 (依法行政)",
                    "D) 利益團體"
                ],
                "correct_index": 2,
                "explanation": "政府與人民皆須遵守法律規範，政府施政必須依法有據，稱為「法治政治」。"
            },
            {
                "id": "q5",
                "concept_tag": "政黨政治",
                "question": "民主國家中通常有多個政黨並存，各黨提出不同政見爭取選民支持，執政黨若施政不當，在野黨可強力監督與競爭。這項機制最能體現下列何種民主政治原則？",
                "options": [
                    "A) 政黨政治 (良性競爭與政權輪替)",
                    "B) 神權政治",
                    "C) 寡頭政治",
                    "D) 專制政治"
                ],
                "correct_index": 0,
                "explanation": "民主政治鼓勵多黨良性競爭，在野黨監督執政黨並透過和平選舉進行政權輪替，此為「政黨政治」的核心精神。"
            },
            {
                "id": "q6",
                "concept_tag": "國家要素",
                "question": "關於國家組成要素中「領土」的範圍，下列何者的敘述最為完整且正確？",
                "options": [
                    "A) 僅包含陸地表面（領陸）",
                    "B) 包含領陸、領海（通常為沿海12浬）及其垂直上空的領空",
                    "C) 只要本國軍艦開得到的所有公海海域",
                    "D) 包含所有與我國簽署貿易協定的國家土地"
                ],
                "correct_index": 1,
                "explanation": "國家領土包括領陸、領海（主權及於領海及其底土）以及領陸與領海之垂直上空（領空）。"
            },
            {
                "id": "q7",
                "concept_tag": "主權在民",
                "question": "我國國民年滿規定年齡依法享有選舉投票權，能以「頭家」身分共同決定國家領導人與民意代表。這種權力來源的理念被稱為何者？",
                "options": [
                    "A) 君權神授",
                    "B) 主權在民 (民意政治根基)",
                    "C) 寡頭政治",
                    "D) 貴族世襲"
                ],
                "correct_index": 1,
                "explanation": "「主權在民」主張國家的最高權力屬於全體國民，人民是國家真正的主人，政府的統治正當性來自人民授權。"
            },
            {
                "id": "q8",
                "concept_tag": "責任政治",
                "question": "在民主國家中，政務官與事務官（常任文官）在責任承擔上有何不同？下列敘述何者正確？",
                "options": [
                    "A) 政務官負責政策制定，政策成敗須負政治責任（如辭職下臺）",
                    "B) 事務官必須隨政黨輪替而集體進退辭職",
                    "C) 政策出錯時一律由基層公務員負起所有的政治責任",
                    "D) 兩者皆享有終身職保障，不必承擔任何責任"
                ],
                "correct_index": 0,
                "explanation": "政務官隨政黨進退，負責承擔「政治責任」（如請辭下臺）；事務官則受公務員法保障，依法行政承擔行政與法律責任。"
            },
            {
                "id": "q9",
                "concept_tag": "國家要素",
                "question": "關於國家組成要素中「人民」的定義與內涵，下列敘述何者最為正確？",
                "options": [
                    "A) 只要居住在該國領土內的所有人，不論國籍皆為該國國民",
                    "B) 國籍是判定是否為該國國民的法定標準，國民享有憲法保障之權利與義務",
                    "C) 人民要素僅包含成年具備投票權的公民，未成年人不屬於國家人民",
                    "D) 外籍觀光客在該國旅遊期間，自動取得該國國民身分"
                ],
                "correct_index": 1,
                "explanation": "人民是指具有該國國籍的個人所組成的群體。國籍是判斷國民身分的法律依據，國民依法享有權利並負擔相應義務。"
            },
            {
                "id": "q10",
                "concept_tag": "法治政治",
                "question": "民主國家的政府行使統治權力時，必須嚴格遵守「依法行政」原則，此一精神的主要目的為何？",
                "options": [
                    "A) 方便行政首長隨時修改法律以配合施政便利",
                    "B) 防止政府公權力濫用，以切實保障人民的基本權利",
                    "C) 消除所有司法審判機關的獨立性",
                    "D) 讓少數掌權者可以凌駕於憲法之上"
                ],
                "correct_index": 1,
                "explanation": "法治政治的核心在於「法律保留」與「依法行政」，藉由法律規範公權力，防止政府恣意妄為，確保人民權利不受侵害。"
            },
            {
                "id": "q11",
                "concept_tag": "政黨政治",
                "question": "下列哪一種情境最符合現代健全「政黨政治」良性競爭的民主常態？",
                "options": [
                    "A) 執政黨修法解散所有在野反對黨，實現單一政黨長期執政",
                    "B) 在野黨在國會全面癱瘓所有預算審查，拒絕任何理性協商",
                    "C) 各政黨提出政策主張爭取選民認同，在野黨監督施政並循和平選舉爭取執政",
                    "D) 選舉結束後失敗的政黨拒絕承認開票結果並發動武裝衝突"
                ],
                "correct_index": 2,
                "explanation": "政黨政治的精髓在於多黨公平競爭、在野黨理性監督制衡，並透過定期與和平的選舉實現政權輪替。"
            },
            {
                "id": "q12",
                "concept_tag": "主權在民",
                "question": "公民老師介紹「代議民主」與「直接民主」時，指出下列何者是人民直接行使國家主權、實踐「直接民主」的最典型機制？",
                "options": [
                    "A) 公民投票（公投）對重大公共政策或法律原則行使複決或創制",
                    "B) 投票選出立法委員代表人民審查國家法案",
                    "C) 收看電視政論節目關心各黨時事評論",
                    "D) 向地方民意代表服務處陳情報案"
                ],
                "correct_index": 0,
                "explanation": "選舉民意代表代為立法屬於「代議民主」；而由人民親自透過公投創制政策或複決法律，則是「直接民主」的展現。"
            },
            {
                "id": "q13",
                "concept_tag": "民意政治",
                "question": "某市市民對於興建焚化爐方案意見分歧，市政府隨即舉辦多場公聽會廣納市民建言，並調整選址規劃。這最能體現下列哪一項民主政治特徵？",
                "options": [
                    "A) 專制統治",
                    "B) 民意政治",
                    "C) 司法獨立",
                    "D) 神權政治"
                ],
                "correct_index": 1,
                "explanation": "政府施政主動傾聽人民心聲、反映大眾民意並據以修正決策，即為「民意政治」的體現。"
            },
            {
                "id": "q14",
                "concept_tag": "國家要素",
                "question": "關於國家主權之「對內最高性」與「對外獨立性」，下列敘述何者完全正確？",
                "options": [
                    "A) 對內最高性是指國內任何團體與個人皆須服從國家的統治權威",
                    "B) 對外獨立性代表本國外交政策完全由聯合國或鄰近強權指定",
                    "C) 對內最高性表示政府官員犯罪不需要接受國內法院審判",
                    "D) 國家只要擁有人民與土地，即便沒有獨立自主的外交權益也是完整主權國家"
                ],
                "correct_index": 0,
                "explanation": "主權對內具有最高性，管轄領土內所有人事物；對外具有獨立自主性，代表國家能自主參與國際社會，不受外國強權干涉。"
            },
            {
                "id": "q15",
                "concept_tag": "責任政治",
                "question": "在民主政治體制中，若常任公務人員（事務官）在執行公務時涉嫌違法瀆職，其應承擔何種責任？",
                "options": [
                    "A) 政治責任（主動請辭下臺即可，無需負法律刑責）",
                    "B) 法律責任與行政懲戒責任（移送司法機關或懲戒法院審理）",
                    "C) 宗教道德責任，由所屬教會處分",
                    "D) 免除一切責任，由全國選民共同分攤"
                ],
                "correct_index": 1,
                "explanation": "政務官對政策成敗負「政治責任」（如請辭）；常任事務官受公務員法保障，但違法失職須負「法律責任」（刑事、民事）及「行政懲戒責任」。"
            },
            {
                "id": "q16",
                "concept_tag": "民意政治",
                "question": "班會在討論畢業旅行地點時，多數同學支持到墾丁，少數同學則希望前往花蓮。班長在表決後裁定採納墾丁方案，但同時將花蓮同學喜愛的水上活動元素納入墾丁行程中。這種做法最符合民主決策的何種核心精神？",
                "options": [
                    "A) 少數服從多數，且多數尊重包容少數",
                    "B) 強權即是公理，完全無視落選方意見",
                    "C) 拖延決策直至所有人都無異議",
                    "D) 由班導師一人獨裁專斷"
                ],
                "correct_index": 0,
                "explanation": "民主政治的決策精神為「少數服從多數、多數尊重並包容少數」，使團體決策兼顧效能與多元需求。"
            }
        ],
        "remediation_guides": {
            "國家要素": {
                "concept": "國家要素",
                "simple_explanation": "國家四大要素缺一不可：人民、領土、政府、主權。邦交國不是組成要素！主權是國家對內最高、對外獨立的決定權。",
                "life_case": "就像自己的房間，別人不能未經同意跑進來指揮你要穿什麼衣服，這就是自主決定權。",
                "pitfall_tip": "避坑口訣：邦交國是好朋友，主權才是自己當家的靈魂！"
            },
            "責任政治": {
                "concept": "責任政治",
                "simple_explanation": "握有權力就要承擔責任！政務官制定政策如果嚴重失敗，就必須向民意道歉並下臺負責。",
                "life_case": "就像隊長帶隊比賽如果調度嚴重違規，隊長要向全隊負責檢討。",
                "pitfall_tip": "避坑口訣：官員做錯事下臺 ＝ 責任政治；人民投票選幹部 ＝ 民意政治！"
            },
            "民意政治": {
                "concept": "民意政治",
                "simple_explanation": "政府的權力來自人民，所以施政一定要體察多數民意，受人民監督。",
                "life_case": "學校營養午餐菜單透過全校問卷統計多數人想吃的菜色，這就是反映民意。",
                "pitfall_tip": "避坑口訣：多數決定、定期改選、反映民意 ＝ 民意政治！"
            },
            "法治政治": {
                "concept": "法治政治",
                "simple_explanation": "法律面前人人平等，政府官員手中的權力也是法律給的，不可以隨心所欲想罰就罰。",
                "life_case": "教官或老師要檢查違禁品也必須依照學校規章程序，不能隨意搜書包。",
                "pitfall_tip": "避坑口訣：依法行政、保障人權 ＝ 法治政治（人治政治的相反）！"
            },
            "政黨政治": {
                "concept": "政黨政治",
                "simple_explanation": "政黨政治就是不同隊伍良性競爭！執政黨負責開車，在野黨坐在副駕駛監督並抓違規，做不好就換隊開！",
                "life_case": "就像班上分組競賽，各組提出不同企劃，大家投票選最好的方案，落選的組別也能提供建議監督。",
                "pitfall_tip": "避坑口訣：良性競爭、監督制衡、和平輪替 ＝ 政黨政治！"
            },
            "主權在民": {
                "concept": "主權在民",
                "simple_explanation": "國家真正的大老闆是全體人民！官員和立委只是人民請來的專業經理人，人民有權利透過選票考核他們。",
                "life_case": "全班同學才是班級的主人，班長是大家選出來替全班服務的，而不是班長管全班。",
                "pitfall_tip": "避坑口訣：人民是老闆、公僕受委託 ＝ 主權在民！"
            }
        }
    },
    {
        "id": "unit_l2",
        "title": "第2課：憲法與權利保障",
        "created_at": "2026-08-20 09:10:00",
        "updated_at": "2026-08-20 09:10:00",
        "raw_content": "廣義法律位階分為憲法、法律、命令。憲法效力最高，為國家根本大法。法律位階低於憲法，由立法院三讀通過、總統公布。命令由行政機關發布，位階最低。下位階不得牴觸上位階。憲法保障人民基本權利：平等權、自由權、受益權、參政權。憲法第23條規定，為防止妨礙他人自由、避免緊急危難、維持社會秩序或增進公共利益，得以法律限制基本權利（法律保留原則與比例原則）。",
        "key_points": [
            "法律金字塔三位階：憲法（頂層最高） > 法律（中層立法院通過） > 命令（底層行政機關發布）。",
            "法律牴觸原則：下位階不得牴觸上位階，牴觸者無效！",
            "人民四大基本權利：平等權（無差別待遇）、自由權（言論/人身/居住等）、受益權（請願/訴願/訴訟/教育）、參政權（選舉/罷免/創制/複決）。",
            "權利限制的界線：依憲法第23條，只有在「四大目的」下且必須「依法律（法律保留原則）」並符合「比例原則」才能限制自由！"
        ],
        "easy_content": "### 🌟 3 分鐘白話搞懂「憲法與人權」\n\n- **🔺 法律三位階金字塔**：\n  1. **憲法 (老大)**：根本大法，位階最高！任何規定跟憲法衝突通通無效。\n  2. **法律 (老二)**：立法院通過、總統公布（名稱通常為：法、律、條例、通則）。\n  3. **命令 (老三)**：行政機關發布的細節規則（名稱通常為：規程、規則、細則、辦法、綱要、標準、準則）。\n\n- **🛡️ 人民基本權利四大法寶**：\n  - **平等權**：不分男女、宗教、種族、階級，法律面前一律平等。\n  - **自由權**：做自己想做的事（言論自由、人身自由、居住遷徙自由）。\n  - **受益權**：向國家要福利或求助（受國民教育、健保、打官司請求救濟）。\n  - **參政權**：參與國家大事（去投票選公職、去競選）。",
        "life_cases": [
            {
                "title": "🏫 校園生活：校規若牴觸法律誰有效？",
                "story": "學校訂定服儀規定時，教育部頒布規定不能因服裝儀容對學生進行懲處。若學校校規與上位規範牴觸，依法律位階原則該校規條款無效。",
                "takeaway": "💡 下位階規範不得牴觸上位階規範，保障學生的基本權利！"
            },
            {
                "title": "🏪 日常生活：颱風天停班停課與基本權限制",
                "story": "颱風來襲時，政府依法限制登山民眾進入危險山區。這是為了「避免緊急危難」依法做出的正當限制。",
                "takeaway": "💡 人民自由不是無限大，但政府限制自由必須依法且符合比例原則！"
            },
            {
                "title": "🚶 街頭情境：警察臨檢盤查與人身自由保障",
                "story": "小明在捷運站外遇到警察執行臨檢盤查，員警依法出示證件並清楚說明臨檢客觀事由。小明知道依據正當法律程序，警察不能無故任意搜身或扣留物品。",
                "takeaway": "💡 人身自由是各項自由權利的基石，國家公權力行使必須符合正當法律程序！"
            },
            {
                "title": "🛒 消費生活：消保爭議與定型化契約無效",
                "story": "小華在網路商城購買商品，廠商條款規定「售出概不退換且放棄任何法律救濟」。消保官介入指出該約定違反消費者保護法，依法律優位原則該條款無效。",
                "takeaway": "💡 私人契約與約定不得牴觸國家法律，法律保障弱勢消費者的基本權益！"
            }
        ],
        "mindmap_mermaid": "graph LR\n  A[\"第2課：憲法與權利保障\"] --> B[\"法律三位階\"]\n  A --> C[\"憲法基本權利\"]\n  A --> D[\"基本權利之限制\"]\n  B --> B1[\"憲法 (最高位階/根本大法)\"]\n  B --> B2[\"法律 (立法院通過/名稱含法律條例通則)\"]\n  B --> B3[\"命令 (行政機關發布/下位不得牴觸上位)\"]\n  C --> C1[\"平等權 (無差別待遇)\"]\n  C --> C2[\"自由權 (人身/言論/秘密通訊等)\"]\n  C --> C3[\"受益權 (生存/工作/教育/司法救濟)\"]\n  C --> C4[\"參政權 (選舉/罷免/創制/複決)\"]\n  D --> D1[\"四大目的 (公益/秩序/防礙他人/緊急危難)\"]\n  D --> D2[\"法律保留原則 (須以法律規範)\"]\n  D --> D3[\"比例原則 (手段與目的適當)\"]",
        "practice_questions": [
            {
                "id": "q1",
                "concept_tag": "法律位階",
                "question": "某市政府公布之「某自治規則」與立法院三讀通過之「道路交通管理處罰條例」相牴觸時，依據法律位階原則，其效力為何？",
                "options": [
                    "A) 該自治規則牴觸法律，應屬無效",
                    "B) 地方自治優先，規則有效",
                    "C) 兩者皆有效，民眾可自由選擇遵守",
                    "D) 由警察機關自由判定何者有效"
                ],
                "correct_index": 0,
                "explanation": "依據法律位階原則，下位階之法規命令或自治法規不得牴觸上位階之法律與憲法，牴觸者無效。"
            },
            {
                "id": "q2",
                "concept_tag": "平等權",
                "question": "某公司在徵才廣告中明確註明「限男性應聘，女性恕不錄取」，此行為違反了憲法所保障的哪一項基本權利？",
                "options": [
                    "A) 自由權",
                    "B) 平等權",
                    "C) 受益權",
                    "D) 參政權"
                ],
                "correct_index": 1,
                "explanation": "憲法保障人民不因性別、宗教、種族或階級而受不合理的差別待遇，此為平等權。"
            },
            {
                "id": "q3",
                "concept_tag": "自由權",
                "question": "小強在個人社群網站上客觀評論時事與校園公共議題，這是行使憲法第11條保障之哪一項權利？",
                "options": [
                    "A) 人身自由",
                    "B) 言論自由 (自由權)",
                    "C) 訴訟權",
                    "D) 創制權"
                ],
                "correct_index": 1,
                "explanation": "發表言論、表達思想屬於憲法第11條保障之「言論自由」，屬於自由權範疇。"
            },
            {
                "id": "q4",
                "concept_tag": "法律保留原則",
                "question": "政府若要限制人民的人身自由或財產權，依據憲法第23條規定，原則上必須以何種形式為之？",
                "options": [
                    "A) 由行政長官口頭命令即可",
                    "B) 必須有立法院通過的「法律」明文依據",
                    "C) 由鄰里長投票表決",
                    "D) 由民間團體決議即可"
                ],
                "correct_index": 1,
                "explanation": "限制人民基本權利必須以立法院通過之「法律」為依據，此即為憲法上的「法律保留原則」。"
            },
            {
                "id": "q5",
                "concept_tag": "受益權",
                "question": "現代國家中，國民依法享有接受九年國民義務教育的權利，經濟困難家庭亦可向政府申請社會救助。這些屬於憲法保障的哪一類基本權利？",
                "options": [
                    "A) 受益權 (請求國家提供給付與救濟)",
                    "B) 參政權",
                    "C) 自由權",
                    "D) 平等權"
                ],
                "correct_index": 0,
                "explanation": "受益權是指人民得請求國家提供經濟照顧、受教育或司法救濟等利益之權利，例如受教育權、生存權與請願訴願訴訟權。"
            },
            {
                "id": "q6",
                "concept_tag": "參政權",
                "question": "憲法保障人民參與國家政治運作的權利，下列各項權利中，何者屬於憲法保障之「參政權」？",
                "options": [
                    "A) 言論自由與秘密通訊自由",
                    "B) 選舉、罷免、創制、複決權及應考試服公職權",
                    "C) 居住及遷徙自由",
                    "D) 人身安全不受非法搜索之自由"
                ],
                "correct_index": 1,
                "explanation": "憲法保障人民之參政權包括選舉權、罷免權、創制權、複決權，以及參加公務人員考試與擔任公職的權利。"
            },
            {
                "id": "q7",
                "concept_tag": "比例原則",
                "question": "警察追捕一名僅犯下輕微闖紅燈違規的機車騎士時，若直接開槍射擊導致其重傷，此執法手段明顯違反了下列何項憲法原則？",
                "options": [
                    "A) 比例原則 (手段過當，危害與目的不相當)",
                    "B) 誠實信用原則",
                    "C) 政黨政治原則",
                    "D) 罪刑法定原則"
                ],
                "correct_index": 0,
                "explanation": "比例原則要求政府行使權力時，所採取的手段必須適當且為侵害最小者，手段與目的間更必須維持均衡，不得「用大砲打小鳥」。"
            },
            {
                "id": "q8",
                "concept_tag": "法律位階",
                "question": "某行政機關發布之「施行細則」（命令）若牴觸立法院通過之「法律」，依據法律位階原則，其法律效力為何？",
                "options": [
                    "A) 依然有效，行政命令效力高於法律",
                    "B) 自始牴觸無效，下位法規不得牴觸上位法規",
                    "C) 由地方政府自行投票決定是否遵守",
                    "D) 僅在直轄市範圍內無效，其他縣市有效"
                ],
                "correct_index": 1,
                "explanation": "依據法律位階原則（法律優位原則），命令不得牴觸憲法與法律，牴觸者無效。"
            },
            {
                "id": "q9",
                "concept_tag": "自由權",
                "question": "學校老師或同學未經當事人許可，擅自翻閱其書包內的私人日記或偷看手機通訊軟體對話紀錄，最主要是侵犯了憲法保障的哪一項權利？",
                "options": [
                    "A) 參政權",
                    "B) 秘密通訊自由與隱私權（自由權）",
                    "C) 受益權",
                    "D) 平等權"
                ],
                "correct_index": 1,
                "explanation": "憲法第12條保障人民有秘密通訊自由，個人私人日記、信件與通訊內容皆受隱私權保護，未經同意不得擅自窺探。"
            },
            {
                "id": "q10",
                "concept_tag": "受益權",
                "question": "小珍的父親因工傷事故導致生活陷入困頓，依法向社會局申請急難救助金，並依勞保條例領取醫療給付。這屬於憲法保障人民之哪一項基本權利？",
                "options": [
                    "A) 參政權",
                    "B) 受益權（生存權與社會安全給付）",
                    "C) 人身自由權",
                    "D) 信仰宗教之自由"
                ],
                "correct_index": 1,
                "explanation": "受益權是指人民有權請求國家提供生活照顧、教育設施或司法救濟等給付利益，包含生存權、工作權、受教育權與請願訴願訴訟權。"
            },
            {
                "id": "q11",
                "concept_tag": "參政權",
                "question": "我國公民除了可以透過投票「選舉」公職人員外，若認為某位民選首長施政嚴重違背民意且不適任，依法可以發動何種權利將其提前解職？",
                "options": [
                    "A) 複決權",
                    "B) 創制權",
                    "C) 罷免權",
                    "D) 請願權"
                ],
                "correct_index": 2,
                "explanation": "參政權中的「罷免權」是人民對民選公職人員行使考核與監督的工具，可透過法定連署與投票將不適任者提前解職。"
            },
            {
                "id": "q12",
                "concept_tag": "比例原則",
                "question": "行政法上的「比例原則」要求政府手段與目的之間必須相當，下列何者「不屬於」比例原則的三大子原則？",
                "options": [
                    "A) 適當性原則（採取的手段有助於目的之達成）",
                    "B) 必要性原則（在所有有效手段中選擇侵害最小者）",
                    "C) 狹義比例原則 / 衡平性原則（手段所造成的損害不得與欲達成目的之利益顯失均衡）",
                    "D) 利益最大化原則（只要政府稅收增加即可不擇手段）"
                ],
                "correct_index": 3,
                "explanation": "比例原則包含適當性、必要性（侵害最小）與狹義比例性（衡平性）三大內涵，俗稱「不可用大砲打小鳥」，絕非以利益最大化為考量。"
            },
            {
                "id": "q13",
                "concept_tag": "法律保留原則",
                "question": "某直轄市政府交通局僅憑局長召開內部會議的一張公文便函，便宣布自明日起全面查扣市民的私人微型電動二輪車。此處分最明顯違反何項憲法原則？",
                "options": [
                    "A) 法律保留原則（限制人民財產與行動自由須有法律明確授權）",
                    "B) 政黨政治原則",
                    "C) 司法獨立原則",
                    "D) 誠信履約原則"
                ],
                "correct_index": 0,
                "explanation": "憲法第23條明定，限制人民自由權利必須「以法律定之」，行政機關無上位法律授權不得逕以內部公文便函侵害人民財產權。"
            },
            {
                "id": "q14",
                "concept_tag": "平等權",
                "question": "國家在高中與大學多元入學管道中，針對原住民族學生及身心障礙學生提供適度的外加名額與輔導措施。這項做法最符合下列哪一種憲法精神？",
                "options": [
                    "A) 形式上的機械平等，忽視弱勢個別差異",
                    "B) 實質上的合理平等，保障弱勢並促進實質機會均等",
                    "C) 侵犯了一般學生的自由權",
                    "D) 專制特權優待"
                ],
                "correct_index": 1,
                "explanation": "憲法上的平等權要求「實質平等」而非齊頭式平等。針對處於不利地位之群體提供合理的優惠或扶助措施，正是實質平等的具體實踐。"
            },
            {
                "id": "q15",
                "concept_tag": "法律位階",
                "question": "憲法被尊稱為國家的「最高根本大法」，也是一切法律與命令的母法。下列哪一項制度最能體現維護憲法最高性、防止違憲法律侵犯人權的精神？",
                "options": [
                    "A) 憲法法庭大法官之違憲審查制度",
                    "B) 警察巡邏臨檢制度",
                    "C) 立法委員質詢制度",
                    "D) 交通監理所驗車制度"
                ],
                "correct_index": 0,
                "explanation": "憲法法庭大法官行使憲法審查權，宣告違憲之法律或裁判無效，以確保憲法最高法效性與人權保障。"
            },
            {
                "id": "q16",
                "concept_tag": "自由權",
                "question": "勞工團體或環保團地位依法向主管機關報備後，在總統府前凱達格蘭大道舉辦和平遊行並發表訴求演說。這是行使憲法所保障的哪項權利？",
                "options": [
                    "A) 集會結社自由與表現自由（自由權）",
                    "B) 受益權",
                    "C) 應考試服公職之權",
                    "D) 人格權"
                ],
                "correct_index": 0,
                "explanation": "和平集會遊行是憲法保障人民透過群體力量表達意見的重要基本自由，屬於自由權的範疇。"
            }
        ],
        "remediation_guides": {
            "法律位階": {
                "concept": "法律位階",
                "simple_explanation": "法律金字塔中：憲法效力最高，法律次之，命令最低。下層碰到上層相衝突，下層一律無效！",
                "life_case": "就像班規不能違反校規，校規不能違反國家法律。",
                "pitfall_tip": "避坑口訣：憲法老大、法律老二、命令小弟；小弟頂撞老大通通無效！"
            },
            "平等權": {
                "concept": "平等權",
                "simple_explanation": "沒有合理的正當理由，不能因為性別、種族、宗教或家庭背景給予差別待遇。",
                "life_case": "班級幹部選舉，男女同學享有相同的被提名與投票資格。",
                "pitfall_tip": "避坑口訣：非合理差別待遇 ＝ 侵犯平等權！"
            },
            "自由權": {
                "concept": "自由權",
                "simple_explanation": "人民可以自由做自己想做的事（言論、出版、結社、居住、信仰），免於國家不法干預。",
                "life_case": "你可以自由選擇自己想閱讀的書籍或參加感興趣的社團。",
                "pitfall_tip": "避坑口訣：自由不是無法無天，但國家要限制自由必須有法律依據！"
            },
            "法律保留原則": {
                "concept": "法律保留原則",
                "simple_explanation": "凡是涉及限制人民生命、人身自由、財產等重要權利的事項，必須由人民選出的立法院制定「法律」來規定，不能只靠行政官員一張紙下令。",
                "life_case": "警察不能隨意開罰單，開罰單必須有立法院通過的交通處罰條例做依據。",
                "pitfall_tip": "避坑口訣：限制人民重要人權，一定要有「法律」依據！"
            },
            "受益權": {
                "concept": "受益權",
                "simple_explanation": "受益權就是向國家『伸手要好處或求救』！例如生病看健保、上學受國教、發生糾紛上法院打官司請求救濟。",
                "life_case": "小明家裡遭小偷，報警並向法院提告請求賠償，這就是在行使司法上的受益權。",
                "pitfall_tip": "避坑口訣：請求國家給予給付、保護或救濟 ＝ 受益權！"
            },
            "參政權": {
                "concept": "參政權",
                "simple_explanation": "參政權就是『當國家的主人親自參與管事』！包括投票選立委、提案公投，或是去考公務員為民服務。",
                "life_case": "班級開班會時大家舉手表決班長，這就是校園版的參政權！",
                "pitfall_tip": "避坑口訣：選幹部、投公投、考公務員 ＝ 參政權！"
            },
            "比例原則": {
                "concept": "比例原則",
                "simple_explanation": "手段不能太誇張！俗稱『不能用大砲打小鳥』。政府要達成目的，必須用侵害最小、最合理的方法。",
                "life_case": "同學上課打瞌睡，老師提醒即可，不能直接罰他退學，這就是合乎比例原則。",
                "pitfall_tip": "避坑口訣：手段合宜、侵害最小、不可用大砲打小鳥 ＝ 比例原則！"
            }
        }
    }
]

def load_all_units():
    """Loads all units from units_db.json or initializes default units."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                units = json.load(f)
                if units and isinstance(units, list):
                    return units
        except Exception as e:
            print(f"[Error] Failed to read units db: {e}")

    # Initialize default units
    default_units = get_builtin_default_units()
    save_all_units(default_units)
    return default_units

def save_all_units(units):
    """Saves unit list to units_db.json."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(units, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Error] Failed to save units db: {e}")
        return False

def get_unit(unit_id):
    """Gets a specific unit by its id."""
    units = load_all_units()
    for u in units:
        if u.get("id") == unit_id or u.get("title") == unit_id:
            return u
    return None

def create_unit(title, raw_content):
    """
    Teacher creates a new unit:
    1. AI analyzes content and generates the complete bundle automatically.
    2. Stores in units_db.json.
    """
    units = load_all_units()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    unit_id = f"unit_{uuid.uuid4().hex[:8]}"

    # Call AI bundle generator
    bundle = generate_unit_bundle(title, raw_content)

    new_unit = {
        "id": unit_id,
        "title": title.strip(),
        "created_at": now_str,
        "updated_at": now_str,
        "raw_content": raw_content.strip(),
        "key_points": bundle.get("key_points", []),
        "easy_content": bundle.get("easy_content", ""),
        "life_cases": bundle.get("life_cases", []),
        "mindmap_mermaid": bundle.get("mindmap_mermaid", ""),
        "practice_questions": bundle.get("practice_questions", []),
        "remediation_guides": bundle.get("remediation_guides", {})
    }

    units.append(new_unit)
    save_all_units(units)
    return new_unit

def update_unit(unit_id, title, raw_content, regenerate=False):
    """Updates unit title, content, or optionally regenerates AI contents."""
    units = load_all_units()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for i, u in enumerate(units):
        if u.get("id") == unit_id:
            u["title"] = title.strip()
            u["raw_content"] = raw_content.strip()
            u["updated_at"] = now_str
            
            if regenerate:
                bundle = generate_unit_bundle(title, raw_content)
                u["key_points"] = bundle.get("key_points", [])
                u["easy_content"] = bundle.get("easy_content", "")
                u["life_cases"] = bundle.get("life_cases", [])
                u["mindmap_mermaid"] = bundle.get("mindmap_mermaid", "")
                u["practice_questions"] = bundle.get("practice_questions", [])
                u["remediation_guides"] = bundle.get("remediation_guides", {})
                
            units[i] = u
            save_all_units(units)
            return u
    return None

def delete_unit(unit_id):
    """Deletes a unit by id."""
    units = load_all_units()
    new_units = [u for u in units if u.get("id") != unit_id and u.get("title") != unit_id]
    if len(new_units) < len(units):
        save_all_units(new_units)
        return True
    return False

def ask_ai_tutor(question, unit_title, unit_content):
    """Answers student questions using friendly plain analogies."""
    prompt = f"""
你是一位親切、幽默且富有耐心的【國中八年級公民 AI 助教】。
學生正在學習單元【{unit_title}】，提出了以下問題：

【學生提問】：{question}
【單元教材參考】：{unit_content[:4000]}

回答指南：
1. 語氣溫暖鼓勵、親切活潑。
2. 用 1~2 個貼近國中生校園生活或日常生活的超白話生動比喻解惑。
3. 條列清晰，避免生硬死板的法律術語，讓國中生一秒看懂！
"""
    try:
        return call_gemini_api(prompt)
    except Exception as e:
        return f"AI 老師思考中，請稍後再試：{e}"
