"""
可縮放的心智圖檢視元件：雙指縮放、拖曳移動，並提供放大 / 縮小 / 重設按鈕。

心智圖內容由 AI 生成，而 st.iframe 的內容可執行 JavaScript，因此內容一律以
JSON 字串傳入（不直接組進 HTML），並使用 Mermaid 的 strict 安全模式清理標籤。
"""
import json

MINDMAP_HEIGHT = 540

_TEMPLATE = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; height: 100%; background: #0b172a; }
  body { font-family: "Noto Sans TC", -apple-system, "Microsoft JhengHei", sans-serif; }
  /* 未放大時保留單指上下滑動給頁面捲動，放大後單指改為拖曳心智圖 */
  #stage { position: relative; height: 100%; overflow: hidden; touch-action: pan-y;
           box-sizing: border-box; border: 1px solid rgba(149, 198, 244, 0.32); border-radius: 14px; }
  #stage.zoomed { touch-action: none; cursor: grab; }
  #canvas { position: absolute; left: 0; top: 0; transform-origin: 0 0; }
  #canvas svg { display: block; max-width: none !important; }
  #tools { position: absolute; right: 10px; top: 10px; z-index: 2; display: flex; gap: 6px; }
  #tools button { width: 44px; height: 44px; font-size: 20px; color: #f8fafc; cursor: pointer;
                  background: rgba(23, 48, 89, 0.92); border: 1px solid #7ab8eb; border-radius: 10px; }
  #hint { position: absolute; left: 12px; bottom: 8px; z-index: 2; color: #9fb6cc; font-size: 13px;
          pointer-events: none; }
  #message { display: none; padding: 1.5rem; color: #fde68a; line-height: 1.7; }
</style>
</head>
<body>
<div id="stage">
  <div id="tools">
    <button id="zoom-in" type="button" aria-label="放大">＋</button>
    <button id="zoom-out" type="button" aria-label="縮小">－</button>
    <button id="zoom-reset" type="button" aria-label="重設大小">⟲</button>
  </div>
  <div id="canvas"></div>
  <div id="message"></div>
  <div id="hint">雙指或按鈕縮放，放大後可拖曳</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
const source = __MERMAID_JSON__;
const stage = document.getElementById('stage');
const canvas = document.getElementById('canvas');
const MAX_ZOOM = 8;
let svgWidth = 0, svgHeight = 0, base = 1, scale = 1, x = 0, y = 0, stageWidth = 0;
const pointers = new Map();
let pinch = null;

function showMessage(text) {
  const message = document.getElementById('message');
  message.textContent = text;
  message.style.display = 'block';
  document.getElementById('tools').style.display = 'none';
  document.getElementById('hint').style.display = 'none';
}

function apply() {
  canvas.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
  stage.classList.toggle('zoomed', scale > base * 1.01);
}

function fit() {
  if (!svgWidth) return;
  const width = stage.clientWidth, height = stage.clientHeight;
  base = Math.min(width / svgWidth, height / svgHeight) * 0.96;
  scale = base;
  x = (width - svgWidth * scale) / 2;
  y = (height - svgHeight * scale) / 2;
  apply();
}

function zoomAt(factor, cx, cy) {
  const next = Math.min(base * MAX_ZOOM, Math.max(base, scale * factor));
  x = cx - (cx - x) * next / scale;
  y = cy - (cy - y) * next / scale;
  scale = next;
  if (scale <= base * 1.01) fit(); else apply();
}

function zoomAtCenter(factor) {
  zoomAt(factor, stage.clientWidth / 2, stage.clientHeight / 2);
}

function localPoint(event) {
  const rect = stage.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
}

function pinchState() {
  const [a, b] = [...pointers.values()];
  return { distance: Math.hypot(a.x - b.x, a.y - b.y), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
}

stage.addEventListener('pointerdown', (event) => {
  if (event.target.closest('#tools')) return;
  pointers.set(event.pointerId, localPoint(event));
  stage.setPointerCapture(event.pointerId);
  pinch = pointers.size === 2 ? pinchState() : null;
});

stage.addEventListener('pointermove', (event) => {
  if (!pointers.has(event.pointerId)) return;
  const previous = pointers.get(event.pointerId);
  const point = localPoint(event);
  pointers.set(event.pointerId, point);
  if (pointers.size === 2) {
    const current = pinchState();
    zoomAt(current.distance / pinch.distance, current.cx, current.cy);
    x += current.cx - pinch.cx;
    y += current.cy - pinch.cy;
    pinch = current;
    apply();
  } else if (pointers.size === 1 && scale > base * 1.01) {
    x += point.x - previous.x;
    y += point.y - previous.y;
    apply();
  }
});

function releasePointer(event) {
  pointers.delete(event.pointerId);
  pinch = null;
}
stage.addEventListener('pointerup', releasePointer);
stage.addEventListener('pointercancel', releasePointer);

/* 觸控板雙指縮放與 Ctrl + 滾輪；一般滾輪仍交給頁面捲動 */
stage.addEventListener('wheel', (event) => {
  if (!event.ctrlKey) return;
  event.preventDefault();
  const point = localPoint(event);
  zoomAt(Math.exp(-event.deltaY * 0.01), point.x, point.y);
}, { passive: false });

document.getElementById('zoom-in').onclick = () => zoomAtCenter(1.4);
document.getElementById('zoom-out').onclick = () => zoomAtCenter(1 / 1.4);
document.getElementById('zoom-reset').onclick = fit;

async function render() {
  if (!window.mermaid) {
    showMessage('心智圖元件載入失敗，請確認網路連線後重新整理頁面。');
    return;
  }
  try {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
    const { svg } = await mermaid.render('mindmap-svg', source);
    canvas.innerHTML = svg;
    const element = canvas.querySelector('svg');
    const box = element.viewBox.baseVal;
    svgWidth = box.width;
    svgHeight = box.height;
    element.style.width = `${svgWidth}px`;
    element.style.height = `${svgHeight}px`;
    fit();
  } catch (error) {
    showMessage('這份心智圖的格式有誤，暫時無法顯示。請老師到「修改教材」重新生成。');
  }
}

/* 所在分頁尚未顯示時寬度為 0，要等看得到才繪製，否則版面會算錯 */
new ResizeObserver(() => {
  const width = stage.clientWidth;
  if (!width || width === stageWidth) return;
  const firstShow = stageWidth === 0;
  stageWidth = width;
  if (firstShow) render(); else fit();
}).observe(stage);
</script>
</body>
</html>
"""


def build_mindmap_html(mermaid_text):
    """回傳可放進 st.iframe 的心智圖頁面。"""
    # 跳脫 <，避免內容中的 </script> 提前結束程式區塊
    payload = json.dumps(mermaid_text, ensure_ascii=False).replace("<", "\\u003c")
    return _TEMPLATE.replace("__MERMAID_JSON__", payload)
