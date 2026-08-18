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
    <title>𝕏 Media Downloader</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#000000">
    <meta name="mobile-web-app-capable" content="yes">
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background-color: #000; color: #f7f9f9; margin: 0; padding: 16px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 480px; }
        
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { font-size: 22px; font-weight: 800; color: #1d9bf0; margin: 0 0 6px 0; }
        .header p { font-size: 13px; color: #71767b; margin: 0; }

        .search-box { background: #16181c; border: 1px solid #2f3336; border-radius: 16px; padding: 6px; display: flex; gap: 8px; margin-bottom: 20px; }
        .search-box input { flex: 1; background: transparent; border: none; padding: 12px 14px; color: #fff; font-size: 14px; outline: none; }
        .search-box button { background: #1d9bf0; color: #fff; border: none; border-radius: 12px; padding: 0 18px; font-weight: 700; font-size: 14px; cursor: pointer; transition: 0.2s; }
        .search-box button:active { transform: scale(0.96); opacity: 0.9; }

        /* Media Grid Layout */
        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 10px; }
        
        .media-card { background: #16181c; border: 1px solid #2f3336; border-radius: 14px; overflow: hidden; position: relative; display: flex; flex-direction: column; }
        .preview-wrapper { width: 100%; height: 170px; background: #000; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .preview-wrapper img { width: 100%; height: 100%; object-fit: cover; }
        
        /* Badges Overlays */
        .badge-type { position: absolute; top: 8px; left: 8px; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px); color: #fff; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; border: 1px solid rgba(255, 255, 255, 0.1); }
        .badge-size { position: absolute; top: 8px; right: 8px; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px); color: #1d9bf0; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(29, 155, 240, 0.2); }
        .badge-res { position: absolute; bottom: 8px; left: 8px; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(4px); color: #fff; font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }

        .card-action { padding: 8px; background: #16181c; }
        .dl-btn { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; background: #202327; color: #00ba7c; border: 1px solid #2f3336; padding: 8px 0; border-radius: 8px; font-size: 12px; font-weight: 700; text-decoration: none; cursor: pointer; transition: 0.2s; }
        .dl-btn:active { background: #00ba7c; color: #fff; }

        .loading-box { text-align: center; padding: 30px 0; color: #71767b; font-size: 14px; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>𝕏 Media Downloader</h1>
            <p>เลือกดาวน์โหลดรูปภาพและวิดีโอคุณภาพสูง</p>
        </div>

        <div class="search-box">
            <input type="text" id="urlInput" placeholder="วางลิงก์ X (Twitter)...">
            <button onclick="fetchMedia()" id="submitBtn">สแกน</button>
        </div>

        <div class="loading-box" id="loading">กำลังดึงข้อมูลสื่อทั้งหมด...</div>
        <div class="grid-container" id="mediaGrid"></div>
    </div>

    <script>
        async function fetchMedia() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return alert('กรุณาใส่ลิงก์ก่อนครับ');

            const btn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const grid = document.getElementById('mediaGrid');

            btn.disabled = true;
            loading.style.display = 'block';
            grid.innerHTML = '';

            try {
                const res = await fetch('/get-media', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url })
                });
                const data = await res.json();

                btn.disabled = false;
                loading.style.display = 'none';

                if(data.error) return alert(data.error);

                data.items.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'media-card';
                    card.innerHTML = `
                        <div class="preview-wrapper">
                            <img src="${item.preview}" alt="preview" loading="lazy">
                            <span class="badge-type">${item.type === 'video' ? '🎥 VIDEO' : '🖼️ PHOTO'}</span>
                            <span class="badge-size">${item.size}</span>
                            <span class="badge-res">${item.res}</span>
                        </div>
                        <div class="card-action">
                            <a href="/download-file?url=${encodeURIComponent(item.download_url)}&type=${item.type}" class="dl-btn">
                                ⬇️ ดาวน์โหลด
                            </a>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (e) {
                btn.disabled = false;
                loading.style.display = 'none';
                alert('เกิดข้อผิดพลาดในการโหลดข้อมูล');
            }
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
        "name": "X Media Downloader",
        "short_name": "𝕏 Downloader",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#000000",
        "theme_color": "#000000"
    })

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('fetch', function(e) {});", mimetype='application/javascript')

@app.route('/get-media', methods=['POST'])
def get_media():
    raw_url = request.json.get('url', '').strip()
    match = re.search(r'status/(\d+)', raw_url)
    if not match:
        return jsonify({'error': 'ลิงก์ไม่ถูกต้อง'}), 400
    
    tweet_id = match.group(1)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://x.com/'}
    
    items = []
    
    try:
        r = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=6)
        if r.status_code == 200:
            tweet = r.json().get('tweet', {})
            media = tweet.get('media', {})
            
            # 1. จัดการรูปภาพ (Photos)
            photos = media.get('photos', [])
            for idx, p in enumerate(photos, 1):
                p_url = p.get('url', '')
                if p_url:
                    items.append({
                        'type': 'photo',
                        'preview': p_url,
                        'download_url': p_url,
                        'res': f"รูปที่ {idx}",
                        'size': 'HD'
                    })

            # 2. จัดการวิดีโอ (Videos)
            videos = media.get('videos', [])
            for idx, v in enumerate(videos, 1):
                thumb = v.get('thumbnail_url', '')
                variants = v.get('variants', [])
                
                # เรียงลำดับความคมชัดสูงสุดขึ้นก่อน
                valid_variants = [item for item in variants if item.get('url', '').split('?')[0].endswith('.mp4')]
                valid_variants.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                
                for var in valid_variants:
                    v_url = var.get('url', '')
                    res_match = re.search(r'/(\d+)x(\d+)/', v_url)
                    if res_match:
                        min_dim = min(int(res_match.group(1)), int(res_match.group(2)))
                        res_label = f"{min_dim}p"
                    else:
                        res_label = "HD Video"

                    size_str = "MP4"
                    try:
                        h_res = requests.head(v_url, headers=headers, timeout=2)
                        cl = h_res.headers.get('content-length')
                        if cl and cl.isdigit():
                            size_str = f"{round(int(cl) / (1024 * 1024), 1)} MB"
                    except Exception:
                        pass

                    items.append({
                        'type': 'video',
                        'preview': thumb,
                        'download_url': v_url,
                        'res': f"คลิปที่ {idx} ({res_label})",
                        'size': size_str
                    })

    except Exception:
        return jsonify({'error': 'ไม่สามารถเชื่อมต่อดึงข้อมูลได้'}), 500

    if not items:
        return jsonify({'error': 'ไม่พบภาพหรือวิดีโอในลิงก์นี้'}), 400

    return jsonify({'items': items})

@app.route('/download-file')
def download_file():
    media_url = request.args.get('url')
    media_type = request.args.get('type', 'video')
    
    if not media_url:
        return "Missing URL", 400

    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    req = requests.get(media_url, headers=headers, stream=True)
    
    ext = "jpg" if media_type == 'photo' else "mp4"
    filename = f"x_download.{ext}"

    return Response(
        stream_with_context(req.iter_content(chunk_size=1024 * 64)),
        content_type=req.headers.get('content-type', 'application/octet-stream'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

