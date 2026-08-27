import os
import json
import re
import uuid
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

DB_FILE = os.path.join(os.path.dirname(__file__), "units_db.json")

# Candidate models for fallback
CANDIDATE_MODELS = [
    'gemini-3.5-flash',
    'gemini-3.6-flash',
    'gemini-flash-latest',
    'gemini-2.0-flash',
    'gemini-2.5-flash-lite',
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
    if api_key:
        genai.configure(api_key=api_key)
    
    last_exception = None
    generation_config = {"response_mime_type": "application/json"} if is_json else None

    for m_name in CANDIDATE_MODELS:
        try:
            model = genai.GenerativeModel(m_name)
            if generation_config:
                res = model.generate_content(prompt, generation_config=generation_config)
            else:
                res = model.generate_content(prompt)
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

def generate_unit_bundle(title, raw_content):
    """
    Analyzes textbook content and automatically generates:
    1. Key learning points (萃取學習重點)
    2. Easy plain-language content (國中生白話整理)
    3. Life & campus cases (生活化案例)
    4. Mermaid concept mind map (心智圖)
    5. Practice questions (小試身手練習題)
    6. Remediation guides (答錯補充說明與避坑指南)
    """
    prompt = f"""
你是一位充滿教學熱忱、深諳國中八年級學生語言的【公民科名師】。
教師剛剛輸入了課本教材（單元名稱：【{title}】），請依據此教材，以「國中生容易理解、生活化、無壓力」為原則，為系統自動產生完整的學習單元包裹。

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
      "title": "🏫 校園生活情境實例1（例如：班代選舉與班規討論）",
      "story": "生動的生活故事敘述（約100字），說明這個公民概念如何出現在學生的日常或校園中。",
      "takeaway": "💡 概念小啟發：一句話總結對應的公民核心觀念。"
    }},
    {{
      "title": "🏪 日常生活情境實例2（例如：超商買東西、網路留言法治觀念）",
      "story": "生動的生活故事敘述（約100字）。",
      "takeaway": "💡 概念小啟發：一句話總結。"
    }}
  ],
  "mindmap_mermaid": "graph TD\\n  A[\"{title}\"] --> B[\"核心概念一\"]\\n  A --> C[\"核心概念二\"]\\n  B --> D[\"生活實例/重點細節\"]\\n  C --> E[\"生活實例/重點細節\"]",
  "practice_questions": [
    {{
      "id": "q1",
      "concept_tag": "核心觀念標籤（如：國家要素、民主政治原則、憲法位階等）",
      "question": "生活情境式的單選練習題（適合小試身手，難度適中）",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 0,
      "explanation": "親切簡短的解析，說明為何選這個答案。"
    }},
    {{
      "id": "q2",
      "concept_tag": "核心觀念標籤",
      "question": "第二題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 1,
      "explanation": "解析說明"
    }},
    {{
      "id": "q3",
      "concept_tag": "核心觀念標籤",
      "question": "第三題題目",
      "options": ["A) 選項一", "B) 選項二", "C) 選項三", "D) 選項四"],
      "correct_index": 2,
      "explanation": "解析說明"
    }},
    {{
      "id": "q4",
      "concept_tag": "核心觀念標籤",
      "question": "第四題題目",
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
            }
        ],
        "mindmap_mermaid": f"""graph TD
  A["{title}"] --> B["核心觀念"]
  A --> C["生活實踐"]
  B --> D["重點理解"]
  C --> E["日常應用"]""",
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
            }
        ],
        "remediation_guides": {
            f"{title}核心觀念": {
                "concept": f"{title}核心觀念",
                "simple_explanation": "公民社會中，每個制度都是為了保障大眾權益與維持社會秩序所建立的。",
                "life_case": "就像班規是由大家共同討論並遵守，以確保每位同學安心學習。",
                "pitfall_tip": "避坑口訣：權利與義務並重，自由以不妨礙他人為界線！"
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
            "easy_content": """### 🌟 3 分鐘白話搞懂「國家與民主」

- **🏛️ 國家就像一間超大超商**：
  - **人民**：顧客與店員（住在這裡的人）。
  - **領土**：店面與倉庫範圍（土地、領海、領空）。
  - **政府**：店長與管理團隊（負責組織與運作）。
  - **主權**：這家店的營業執照與經營決策權（自己做主，隔壁店家不能來指揮！）。

- **🗳️ 民主政治四大原則秒記法**：
  1. **民意政治**：政府做事情要聽老闆（全體人民）的想法。
  2. **責任政治**：店長政策出包造成虧損，必須向大家道歉或請辭下臺！
  3. **法治政治**：大家都要守法，就算總統也不能違法。
  4. **政黨政治**：不同政黨互相競爭與監督，避免單一政黨獨裁。""",
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
                }
            ],
            "mindmap_mermaid": """graph TD
  A["第1課：國家與民主政治"] --> B["國家的四大要素"]
  A --> C["民主政治四大原則"]
  B --> B1["人民 (國民群體)"]
  B --> B2["領土 (領陸/領海/領空)"]
  B --> B3["政府 (行政統治組織)"]
  B --> B4["主權 (對內最高/對外獨立)"]
  C --> C1["民意政治 (主權在民)"]
  C --> C2["責任政治 (失職下臺)"]
  C --> C3["法治政治 (依法行政)"]
  C --> C4["政黨政治 (良性競爭)"]""",
            "practice_questions": [
                {
                    "id": "q1",
                    "concept_tag": "國家要素",
                    "question": "某國在國際上與其他國家建立邦交、簽署條約，且不受鄰近大國的干涉與控制。這最能體現國家組成四要素中的哪一項？",
                    "options": ["A) 人民", "B) 領土", "C) 政府", "D) 主權"],
                    "correct_index": 3,
                    "explanation": "主權是指國家對內擁有最高統治權，對外具有獨立自主性，不受他國干涉。"
                },
                {
                    "id": "q2",
                    "concept_tag": "責任政治",
                    "question": "某部會推動新政策時發生重大疏失，引發社會爭議，該部部長隨即召開記者會向國人致歉並遞出辭呈。這符合民主政治的哪一項核心原則？",
                    "options": ["A) 責任政治", "B) 民意政治", "C) 法治政治", "D) 政黨政治"],
                    "correct_index": 0,
                    "explanation": "政務官對政策成敗負責並主動請辭下臺，是「責任政治」的代表表現。"
                },
                {
                    "id": "q3",
                    "concept_tag": "民意政治",
                    "question": "我國憲法規定「中華民國之主權屬於國民全體」，民眾定期透過投票選出立法委員與縣市長。這主要展現了哪一項原則？",
                    "options": ["A) 司法獨立", "B) 民意政治與主權在民", "C) 地方自治", "D) 權力集中"],
                    "correct_index": 1,
                    "explanation": "透過定期投票選出公職人員以反映多數人民意願，即為民意政治。"
                },
                {
                    "id": "q4",
                    "concept_tag": "法治政治",
                    "question": "行政機關推行各項行政作為時，必須嚴格依循立法院通過的法律，不得任意開罰或侵犯人民權利。這屬於哪一項民主原則？",
                    "options": ["A) 責任政治", "B) 政黨政治", "C) 法治政治 (依法行政)", "D) 利益團體"],
                    "correct_index": 2,
                    "explanation": "政府與人民皆須遵守法律規範，政府施政必須依法有據，稱為「法治政治」。"
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
            "easy_content": """### 🌟 3 分鐘白話搞懂「憲法與人權」

- **🔺 法律三位階金字塔**：
  1. **憲法 (老大)**：根本大法，位階最高！任何規定跟憲法衝突通通無效。
  2. **法律 (老二)**：立法院通過、總統公布（名稱通常為：法、律、條例、通則）。
  3. **命令 (老三)**：行政機關發布的細節規則（名稱通常為：規程、規則、細則、辦法、綱要、標準、準則）。

- **🛡️ 人民基本權利四大法寶**：
  - **平等權**：不分男女、宗教、種族、階級，法律面前一律平等。
  - **自由權**：做自己想做的事（言論自由、人身自由、居住遷徙自由）。
  - **受益權**：向國家要福利或求助（受國民教育、健保、打官司請求救濟）。
  - **參政權**：參與國家大事（去投票選公職、去競選）。""",
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
                }
            ],
            "mindmap_mermaid": """graph TD
  A["第2課：憲法與權利保障"] --> B["法律三位階"]
  A --> C["憲法基本權利"]
  A --> D["基本權利之限制"]
  B --> B1["憲法 (最高位階/根本大法)"]
  B --> B2["法律 (立法院通過/名稱含法律條例通則)"]
  B --> B3["命令 (行政機關發布/下位不得牴觸上位)"]
  C --> C1["平等權 (無差別待遇)"]
  C --> C2["自由權 (人身/言論/秘密通訊等)"]
  C --> C3["受益權 (生存/工作/教育/司法救濟)"]
  C --> C4["參政權 (選舉/罷免/創制/複決)"]
  D --> D1["四大目的 (公益/秩序/防礙他人/緊急危難)"]
  D --> D2["法律保留原則 (須以法律規範)"]
  D --> D3["比例原則 (手段與目的適當)"]""",
            "practice_questions": [
                {
                    "id": "q1",
                    "concept_tag": "法律位階",
                    "question": "某市政府公布之「某自治規則」與立法院三讀通過之「道路交通管理處罰條例」相牴觸時，依據法律位階原則，其效力為何？",
                    "options": ["A) 該自治規則牴觸法律，應屬無效", "B) 地方自治優先，規則有效", "C) 兩者皆有效，民眾可自由選擇遵守", "D) 由警察機關自由判定何者有效"],
                    "correct_index": 0,
                    "explanation": "依據法律位階原則，下位階之法規命令或自治法規不得牴觸上位階之法律與憲法，牴觸者無效。"
                },
                {
                    "id": "q2",
                    "concept_tag": "平等權",
                    "question": "某公司在徵才廣告中明確註明「限男性應聘，女性恕不錄取」，此行為違反了憲法所保障的哪一項基本權利？",
                    "options": ["A) 自由權", "B) 平等權", "C) 受益權", "D) 參政權"],
                    "correct_index": 1,
                    "explanation": "憲法保障人民不因性別、宗教、種族或階級而受不合理的差別待遇，此為平等權。"
                },
                {
                    "id": "q3",
                    "concept_tag": "自由權",
                    "question": "小強在個人社群網站上客觀評論時事與校園公共議題，這是行使憲法第11條保障之哪一項權利？",
                    "options": ["A) 人身自由", "B) 言論自由 (自由權)", "C) 訴訟權", "D) 創制權"],
                    "correct_index": 1,
                    "explanation": "發表言論、表達思想屬於憲法第11條保障之「言論自由」，屬於自由權範疇。"
                },
                {
                    "id": "q4",
                    "concept_tag": "法律保留原則",
                    "question": "政府若要限制人民的人身自由或財產權，依據憲法第23條規定，原則上必須以何種形式為之？",
                    "options": ["A) 由行政長官口頭命令即可", "B) 必須有立法院通過的「法律」明文依據", "C) 由鄰里長投票表決", "D) 由民間團體決議即可"],
                    "correct_index": 1,
                    "explanation": "限制人民基本權利必須以立法院通過之「法律」為依據，此即為憲法上的「法律保留原則」。"
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
