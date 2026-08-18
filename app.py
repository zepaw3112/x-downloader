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
    
    <!-- PWA Settings (ตั้งค่า Web App) -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="𝕏 Downloader">
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
        
        /* สไตล์สำหรับรูป พรีวิว */
        .preview-img { width: 100%; max-height: 250px; object-fit: cover; border-radius: 12px; margin: 10px 0; border: 1px solid #2f3336; display: none; }
        
        .dl-btn { display: block; width: 100%; background: #00ba7c; color: #fff; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; text-align: center; border: none; cursor: pointer; }
        label { font-size: 13px; color: #71767b; margin-top: 10px; display: block; }
    </style>
</head>
<body>
    <div class="card">
        <h2>𝕏 Video Downloader</h2>
        <input type="text" id="url" placeholder="วางลิงก์ X (Twitter) ที่นี่...">
        <button onclick="fetchVideo()" id="fetchBtn">ค้นหาความละเอียดคลิป</button>

        <div class="result-box" id="resultBox">
            <!-- แสดงภาพพรีวิวคลิป -->
            <img id="previewImg" class="preview-img" alt="Video Preview">

            <label for="qualitySelect">เลือกความละเอียด และขนาดไฟล์:</label>
            <select id="qualitySelect"></select>

            <button onclick="startDownload()" class="dl-btn">⬇️ ดาวน์โหลดวิดีโอ</button>
            <p style="font-size: 12px; color: #71767b; text-align: center; margin-top: 8px;">(ระบบสตรีมตรงผ่าน Chrome)</p>
        </div>
    </div>

    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }

        async function fetchVideo() {
            const url = document.getElementById('url').value.trim();
            if(!url) return alert('กรุณาวางลิงก์ก่อนครับ');

            const btn = document.getElementById('fetchBtn');
            btn.innerText = 'กำลังสแกนคลิปและภาพพรีวิว...';
            btn.disabled = true;
            document.getElementById('resultBox').style.display = 'none';

            try {
                const res = await fetch('/get-video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url })
                });
                const data = await res.json();

                btn.innerText = 'ค้นหาความละเอียดคลิป';
                btn.disabled = false;

                if(data.error) return alert(data.error);

                // แสดงรูปพรีวิว (ถ้ามี)
                const img = document.getElementById('previewImg');
                if (data.thumbnail) {
                    img.src = data.thumbnail;
                    img.style.display = 'block';
                } else {
                    img.style.display = 'none';
                }

                const select = document.getElementById('qualitySelect');
                select.innerHTML = '';
                
                data.videos.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.url;
                    opt.innerText = `${v.resolution}  |  ขนาดไฟล์: ${v.filesize}`;
                    select.appendChild(opt);
                });

                document.getElementById('resultBox').style.display = 'block';
            } catch (e) {
                btn.innerText = 'ค้นหาความละเอียดคลิป';
                btn.disabled = false;
                alert('เกิดข้อผิดพลาดในการเชื่อมต่อ');
            }
        }

        function startDownload() {
            const select = document.getElementById('qualitySelect');
            const videoUrl = select.value;
            if(!videoUrl) return;

            window.location.href = `/download-file?url=${encodeURIComponent(videoUrl)}`;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "X Video Downloader",
        "short_name": "𝕏 Downloader",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#000000",
        "icons": [
            {
                "src": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/512px-X_logo_2023.svg.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    })

@app.route('/sw.js')
def sw():
    sw_code = "self.addEventListener('fetch', function(event) { return; });"
    return Response(sw_code, mimetype='application/javascript')

@app.route('/get-video', methods=['POST'])
def get_video():
    raw_url = request.json.get('url', '').strip().strip("'").strip('"')
    
    match = re.search(r'status/(\d+)', raw_url)
    if not match:
        return jsonify({'error': 'ลิงก์ไม่ถูกต้อง กรุณาใช้ลิงก์จาก X (Twitter)'}), 400
    
    tweet_id = match.group(1)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/'
    }

    raw_variants = []
    thumbnail_url = ""

    # 1. FxTwitter API
    try:
        r1 = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=5)
        if r1.status_code == 200:
            d1 = r1.json()
            videos = d1.get('tweet', {}).get('media', {}).get('videos', [])
            if videos:
                thumbnail_url = videos[0].get('thumbnail_url', '')
                if 'variants' in videos[0]:
                    raw_variants = videos[0]['variants']
    except Exception:
        pass

    # 2. VxTwitter API (สำรอง)
    if not raw_variants:
        try:
            r2 = requests.get(f"https://api.vxtwitter.com/i/status/{tweet_id}", headers=headers, timeout=5)
            if r2.status_code == 200:
                d2 = r2.json()
                media = d2.get('media_extended', [])
                for item in media:
                    if item.get('type') == 'video':
                        thumbnail_url = item.get('thumbnail_url', '')
                        if 'variants' in item:
                            raw_variants = item['variants']
                            break
        except Exception:
            pass

    if not raw_variants:
        return jsonify({'error': 'ไม่พบวิดีโอในโพสต์นี้'}), 400

    results = []
    seen_urls = set()

    for v in raw_variants:
        v_url = v.get('url', '')
        if not v_url or v_url in seen_urls or not v_url.split('?')[0].endswith('.mp4'):
            continue
        seen_urls.add(v_url)

        res_match = re.search(r'/(\d+)x(\d+)/', v_url)
        if res_match:
            w, h = int(res_match.group(1)), int(res_match.group(2))
            min_dim = min(w, h)
            res_label = f"{min_dim}p"
        else:
            bitrate = v.get('bitrate', 0)
            if bitrate > 2000000:
                res_label = "1080p (FHD)"
            elif bitrate > 800000:
                res_label = "720p (HD)"
            elif bitrate > 300000:
                res_label = "480p (SD)"
            else:
                res_label = "360p (Low)"

        size_str = "ไม่ทราบขนาด"
        try:
            head_res = requests.head(v_url, headers=headers, timeout=3)
            cl = head_res.headers.get('content-length')
            if cl and cl.isdigit():
                mb = round(int(cl) / (1024 * 1024), 1)
                size_str = f"{mb} MB"
        except Exception:
            pass

        results.append({
            'url': v_url,
            'resolution': res_label,
            'filesize': size_str,
            'bitrate': v.get('bitrate', 0)
        })

    results.sort(key=lambda x: x['bitrate'], reverse=True)

    if not results:
        return jsonify({'error': 'ไม่สามารถดึงไฟล์วิดีโอได้'}), 400

    return jsonify({
        'thumbnail': thumbnail_url,
        'videos': results
    })

@app.route('/download-file')
def download_file():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/'
    }

    req = requests.get(video_url, headers=headers, stream=True)
    
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024 * 64)),
        content_type=req.headers.get('content-type', 'video/mp4'),
        headers={
            'Content-Disposition': 'attachment; filename="x_video.mp4"',
            'Content-Length': req.headers.get('content-length', '')
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

