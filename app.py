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
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="apple-touch-icon" href="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/512px-X_logo_2023.svg.png">

    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background-color: #000; color: #fff; padding: 20px; margin: 0; }
        .card { background: #16181c; border-radius: 16px; padding: 20px; max-width: 450px; margin: 20px auto; border: 1px solid #2f3336; }
        h2 { text-align: center; color: #1d9bf0; }
        input, select, button { width: 100%; padding: 14px; margin: 8px 0; border-radius: 8px; border: 1px solid #333; font-size: 15px; }
        input { background: #000; color: #fff; }
        select { background: #202327; color: #fff; font-weight: bold; }
        button { background-color: #1d9bf0; color: white; font-weight: bold; border: none; cursor: pointer; }
        
        /* สไตล์ Carousel สไลด์ด้านข้าง */
        .carousel-container { display: flex; overflow-x: auto; gap: 10px; padding: 10px 0; scroll-snap-type: x mandatory; }
        .carousel-item { flex: 0 0 85%; scroll-snap-align: center; }
        .carousel-item img { width: 100%; height: 250px; object-fit: contain; background: #000; border-radius: 12px; border: 1px solid #333; }
        
        .result-box { margin-top: 15px; display: none; }
        .dl-btn { display: block; width: 100%; background: #00ba7c; color: #fff; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; text-align: center; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>𝕏 Video Downloader</h2>
        <input type="text" id="url" placeholder="วางลิงก์ X (Twitter)...">
        <button onclick="fetchVideo()" id="fetchBtn">ค้นหาความละเอียดคลิป</button>
        <div class="result-box" id="resultBox">
            <div id="carousel" class="carousel-container"></div>
            <label>เลือกวิดีโอที่ต้องการ:</label>
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
            document.getElementById('resultBox').style.display = 'none';

            try {
                const res = await fetch('/get-video', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ url }) });
                const data = await res.json();
                btn.innerText = 'ค้นหาความละเอียดคลิป'; btn.disabled = false;
                if(data.error) return alert(data.error);

                const carousel = document.getElementById('carousel');
                carousel.innerHTML = '';
                data.media_list.forEach(m => {
                    const div = document.createElement('div'); div.className = 'carousel-item';
                    div.innerHTML = `<img src="${m.url}">`;
                    carousel.appendChild(div);
                });

                const select = document.getElementById('qualitySelect');
                select.innerHTML = '';
                data.videos.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.url;
                    opt.innerText = `คลิปที่ ${v.video_index} | ${v.resolution}`;
                    select.appendChild(opt);
                });
                document.getElementById('resultBox').style.display = 'block';
            } catch (e) { btn.innerText = 'ค้นหา'; btn.disabled = false; alert('error'); }
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
    raw_url = request.json.get('url', '').strip().strip("'").strip('"')
    match = re.search(r'status/(\d+)', raw_url)
    if not match: return jsonify({'error': 'ลิงก์ไม่ถูกต้อง'}), 400
    
    tweet_id = match.group(1)
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=5)
        data = r.json().get('tweet', {})
        media_items = data.get('media', {}).get('videos', []) + data.get('media', {}).get('photos', [])
    except: return jsonify({'error': 'เชื่อมต่อ API ไม่ได้'}), 500

    media_list = []
    video_options = []

    for idx, item in enumerate(media_items, 1):
        media_list.append({'url': item.get('url') or item.get('thumbnail_url')})
        if item.get('type') == 'video':
            for v in item.get('variants', []):
                if v.get('content_type') == 'video/mp4':
                    video_options.append({'video_index': idx, 'url': v['url'], 'resolution': 'HD'})

    if not media_list: return jsonify({'error': 'ไม่พบสื่อในโพสต์นี้'}), 400
    return jsonify({'media_list': media_list, 'videos': video_options})

@app.route('/download-file')
def download_file():
    req = requests.get(request.args.get('url'), headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
    return Response(stream_with_context(req.iter_content(65536)), headers={'Content-Disposition': 'attachment; filename="x_video.mp4"'})

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)

