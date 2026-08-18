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
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="apple-touch-icon" href="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/512px-X_logo_2023.svg.png">

    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background-color: #000; color: #fff; padding: 20px; margin: 0; user-select: none; }
        .card { background: #16181c; border-radius: 16px; padding: 20px; max-width: 450px; margin: 20px auto; border: 1px solid #2f3336; }
        h2 { text-align: center; margin-top: 0; color: #1d9bf0; }
        input, select, button { width: 100%; padding: 14px; margin: 8px 0; border-radius: 8px; border: 1px solid #333; font-size: 15px; }
        input { background: #000; color: #fff; }
        select { background: #202327; color: #fff; font-weight: bold; }
        button { background-color: #1d9bf0; color: white; font-weight: bold; border: none; cursor: pointer; transition: 0.2s; }
        button:disabled { opacity: 0.5; }
        .result-box { margin-top: 15px; display: none; }
        .preview-img { width: 100%; max-height: 300px; object-fit: contain; background: #000; border-radius: 12px; margin: 10px 0; border: 1px solid #2f3336; display: none; }
        .dl-btn { display: block; width: 100%; background: #00ba7c; color: #fff; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; text-align: center; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>𝕏 Video Downloader</h2>
        <input type="text" id="url" placeholder="วางลิงก์ X (Twitter) ที่นี่...">
        <button onclick="fetchVideo()" id="fetchBtn">ค้นหาความละเอียดคลิป</button>
        <div class="result-box" id="resultBox">
            <img id="previewImg" class="preview-img" alt="Video Preview">
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

                const img = document.getElementById('previewImg');
                if (data.thumbnail) { img.src = data.thumbnail; img.style.display = 'block'; }
                
                const select = document.getElementById('qualitySelect');
                select.innerHTML = '';
                data.videos.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.url;
                    opt.innerText = `คลิปที่ ${v.video_index} | ${v.resolution} | ${v.filesize}`;
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://x.com/'}
    
    # ดึงข้อมูลผ่าน FxTwitter
    try:
        r = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            media_items = data.get('tweet', {}).get('media', {}).get('videos', [])
            if not media_items: media_items = data.get('tweet', {}).get('media', {}).get('photos', [])
    except: return jsonify({'error': 'เชื่อมต่อ API ไม่ได้'}), 500

    results = []
    thumbnail_url = ""
    
    # วนลูปทุก Media ในโพสต์
    for idx, item in enumerate(media_items, 1):
        if not thumbnail_url: thumbnail_url = item.get('thumbnail_url', '')
        variants = item.get('variants', [])
        for v in variants:
            v_url = v.get('url', '')
            if not v_url or not v_url.split('?')[0].endswith('.mp4'): continue
            
            # เช็คความละเอียดและขนาด
            res_match = re.search(r'/(\d+)x(\d+)/', v_url)
            res_label = f"{min(int(res_match.group(1)), int(res_match.group(2)))}p" if res_match else "HD"
            
            size_str = "Unknown"
            try:
                cl = requests.head(v_url, headers=headers, timeout=2).headers.get('content-length')
                if cl: size_str = f"{round(int(cl)/1048576, 1)} MB"
            except: pass

            results.append({'video_index': idx, 'url': v_url, 'resolution': res_label, 'filesize': size_str, 'bitrate': v.get('bitrate', 0)})

    if not results: return jsonify({'error': 'ไม่พบวิดีโอ'}), 400
    return jsonify({'thumbnail': thumbnail_url, 'videos': sorted(results, key=lambda x: x['bitrate'], reverse=True)})

@app.route('/download-file')
def download_file():
    video_url = request.args.get('url')
    req = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}, stream=True)
    return Response(stream_with_context(req.iter_content(65536)), headers={'Content-Disposition': 'attachment; filename="x_video.mp4"'})

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)

