import re
import requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Video Downloader</title>
    <style>
        * { box-sizing: border-box; font-family: sans-serif; }
        body { background-color: #000; color: #fff; padding: 20px; margin: 0; }
        .card { background: #16181c; border-radius: 16px; padding: 20px; max-width: 450px; margin: 20px auto; border: 1px solid #2f3336; }
        h2 { text-align: center; color: #1d9bf0; }
        input, select, button { width: 100%; padding: 14px; margin: 8px 0; border-radius: 8px; border: 1px solid #333; font-size: 15px; }
        input { background: #000; color: #fff; }
        select { background: #202327; color: #fff; font-weight: bold; }
        button { background-color: #1d9bf0; color: white; font-weight: bold; border: none; cursor: pointer; }
        .carousel-container { display: flex; overflow-x: auto; gap: 10px; padding: 10px 0; }
        .carousel-item { flex: 0 0 100%; }
        .carousel-item img { width: 100%; height: 250px; object-fit: contain; background: #000; border-radius: 12px; }
        .result-box { margin-top: 15px; display: none; }
        .dl-btn { display: block; width: 100%; background: #00ba7c; color: #fff; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>𝕏 Video Downloader</h2>
        <input type="text" id="url" placeholder="วางลิงก์ X (Twitter)...">
        <button onclick="fetchVideo()" id="fetchBtn">ค้นหาความละเอียด</button>
        <div class="result-box" id="resultBox">
            <div id="carousel" class="carousel-container"></div>
            <select id="qualitySelect"></select>
            <button onclick="startDownload()" class="dl-btn">⬇️ ดาวน์โหลดวิดีโอ</button>
        </div>
    </div>
    <script>
        async function fetchVideo() {
            const url = document.getElementById('url').value.trim();
            if(!url) return alert('กรุณาวางลิงก์');
            const btn = document.getElementById('fetchBtn');
            btn.innerText = 'กำลังสแกน...'; btn.disabled = true;
            try {
                const res = await fetch('/get-video', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ url }) });
                const data = await res.json();
                btn.innerText = 'ค้นหาความละเอียด'; btn.disabled = false;
                if(data.error) return alert(data.error);
                const carousel = document.getElementById('carousel');
                carousel.innerHTML = '';
                data.media_list.forEach(m => {
                    carousel.innerHTML += `<div class="carousel-item"><img src="${m.url}"></div>`;
                });
                const select = document.getElementById('qualitySelect');
                select.innerHTML = '';
                data.videos.forEach(v => {
                    select.innerHTML += `<option value="${v.url}">คลิปที่ ${v.index} | ${v.res}</option>`;
                });
                document.getElementById('resultBox').style.display = 'block';
            } catch (e) { btn.innerText = 'ค้นหา'; btn.disabled = false; alert('เกิดข้อผิดพลาด'); }
        }
        function startDownload() { window.location.href = `/download-file?url=${encodeURIComponent(document.getElementById('qualitySelect').value)}`; }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/get-video', methods=['POST'])
def get_video():
    raw_url = request.json.get('url', '')
    match = re.search(r'status/(\d+)', raw_url)
    if not match: return jsonify({'error': 'ลิงก์ไม่ถูกต้อง'}), 400
    
    try:
        r = requests.get(f"https://api.fxtwitter.com/status/{match.group(1)}", timeout=5)
        data = r.json().get('tweet', {})
        media_items = data.get('media', {}).get('videos', []) + data.get('media', {}).get('photos', [])
    except: return jsonify({'error': 'เชื่อมต่อ API ไม่ได้'}), 500

    media_list = []
    video_options = []
    
    for idx, item in enumerate(media_items, 1):
        # แก้ไข: ดึงรูปที่ถูกต้อง
        m_url = item.get('media_url_https') or item.get('thumbnail_url') or item.get('url')
        if m_url: media_list.append({'url': m_url})
        
        if item.get('type') == 'video':
            for v in item.get('variants', []):
                v_url = v.get('url', '')
                if v.get('content_type') == 'video/mp4':
                    # แก้ไข: ดึง Resolution จาก URL
                    res_match = re.search(r'/(\d+)x(\d+)/', v_url)
                    res = f"{min(int(res_match.group(1)), int(res_match.group(2)))}p" if res_match else "High Quality"
                    video_options.append({'index': idx, 'url': v_url, 'res': res, 'bitrate': v.get('bitrate', 0)})

    # กรองเอาเฉพาะตัวที่ชัดที่สุดในแต่ละคลิป
    filtered_videos = []
    seen = set()
    for v in sorted(video_options, key=lambda x: x['bitrate'], reverse=True):
        key = f"{v['index']}-{v['res']}"
        if key not in seen:
            filtered_videos.append(v)
            seen.add(key)

    if not media_list: return jsonify({'error': 'ไม่พบสื่อในโพสต์'}), 400
    return jsonify({'media_list': media_list, 'videos': filtered_videos})

@app.route('/download-file')
def download_file():
    req = requests.get(request.args.get('url'), headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
    return Response(stream_with_context(req.iter_content(65536)), headers={'Content-Disposition': 'attachment; filename="video.mp4"'})

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)

