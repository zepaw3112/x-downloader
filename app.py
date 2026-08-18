import re
import requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>𝕏 Glass Downloader</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0d0e12">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        
        body { 
            background-color: #08090c; 
            color: #f5f5f7; 
            margin: 0; 
            padding: 20px 16px; 
            display: flex; 
            justify-content: center; 
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* iOS Ambient Glow Background */
        .ambient-glow-1 {
            position: fixed; top: -100px; left: -80px; width: 320px; height: 320px;
            background: radial-gradient(circle, rgba(29, 155, 240, 0.45) 0%, rgba(0,0,0,0) 70%);
            filter: blur(60px); z-index: -1; pointer-events: none;
        }
        .ambient-glow-2 {
            position: fixed; top: 35%; right: -100px; width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(147, 51, 234, 0.35) 0%, rgba(0,0,0,0) 70%);
            filter: blur(70px); z-index: -1; pointer-events: none;
        }
        .ambient-glow-3 {
            position: fixed; bottom: -50px; left: 10%; width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(0, 186, 124, 0.25) 0%, rgba(0,0,0,0) 70%);
            filter: blur(60px); z-index: -1; pointer-events: none;
        }

        .container { width: 100%; max-width: 460px; z-index: 1; }

        /* Header Style */
        .header { text-align: center; margin-bottom: 24px; padding-top: 8px; }
        .header h1 { 
            font-size: 26px; font-weight: 800; letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff 30%, #70baff 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin: 0 0 6px 0; 
        }
        .header p { font-size: 13px; color: rgba(235, 235, 245, 0.6); margin: 0; font-weight: 400; }

        /* Glass Search Box */
        .search-card {
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(30px) saturate(200%);
            -webkit-backdrop-filter: blur(30px) saturate(200%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15);
            border-radius: 22px;
            padding: 6px;
            display: flex; gap: 8px; margin-bottom: 24px;
            transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
        }
        .search-card:focus-within {
            border-color: rgba(29, 155, 240, 0.5);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(29, 155, 240, 0.3);
        }
        .search-card input {
            flex: 1; background: transparent; border: none; padding: 14px 16px;
            color: #fff; font-size: 14px; outline: none; font-weight: 400;
        }
        .search-card input::placeholder { color: rgba(235, 235, 245, 0.35); }
        .search-card button {
            background: linear-gradient(135deg, #1d9bf0 0%, #0072c6 100%);
            color: #fff; border: none; border-radius: 16px; padding: 0 20px;
            font-weight: 600; font-size: 14px; cursor: pointer;
            box-shadow: 0 4px 15px rgba(29, 155, 240, 0.35);
            transition: all 0.2s ease;
        }
        .search-card button:active { transform: scale(0.95); opacity: 0.9; }

        /* Media Grid Layout */
        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }

        /* iOS Glass Cards */
        .media-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(25px) saturate(190%);
            -webkit-backdrop-filter: blur(25px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            border-radius: 20px; overflow: hidden;
            display: flex; flex-direction: column;
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        .media-card:active { transform: scale(0.98); }

        .preview-wrapper {
            width: 100%; height: 180px; background: rgba(0, 0, 0, 0.4);
            position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden;
        }
        .preview-wrapper img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }
        .media-card:hover .preview-wrapper img { transform: scale(1.05); }

        /* Floating Frosted Badges */
        .badge-glass {
            position: absolute;
            background: rgba(15, 15, 20, 0.6);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 10px; font-weight: 700; letter-spacing: 0.3px;
            padding: 4px 8px; border-radius: 8px;
        }
        .badge-type { top: 10px; left: 10px; }
        .badge-size { top: 10px; right: 10px; color: #70baff; }
        .badge-res { bottom: 10px; left: 10px; }

        .card-action { padding: 10px; }
        .dl-btn {
            display: flex; align-items: center; justify-content: center; gap: 6px;
            width: 100%; background: rgba(255, 255, 255, 0.08);
            color: #34c759; border: 1px solid rgba(52, 199, 89, 0.25);
            padding: 10px 0; border-radius: 12px; font-size: 12px; font-weight: 700;
            text-decoration: none; cursor: pointer; backdrop-filter: blur(10px);
            transition: all 0.2s ease;
        }
        .dl-btn:active { background: #34c759; color: #fff; box-shadow: 0 4px 15px rgba(52, 199, 89, 0.4); }

        .loading-box { text-align: center; padding: 40px 0; color: rgba(235, 235, 245, 0.5); font-size: 14px; display: none; }
    </style>
</head>
<body>
    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>
    <div class="ambient-glow-3"></div>

    <div class="container">
        <div class="header">
            <h1>𝕏 Media Downloader</h1>
            <p>สัมผัสประสบการณ์ดาวน์โหลดระดับ Premium</p>
        </div>

        <div class="search-card">
            <input type="text" id="urlInput" placeholder="วางลิงก์ X (Twitter) ที่นี่...">
            <button onclick="fetchMedia()" id="submitBtn">สแกน</button>
        </div>

        <div class="loading-box" id="loading">✨ กำลังประมวลผลสื่อระดับ HD...</div>
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
                            <span class="badge-glass badge-type">${item.type === 'video' ? '🎥 VIDEO' : '🖼️ PHOTO'}</span>
                            <span class="badge-glass badge-size">${item.size}</span>
                            <span class="badge-glass badge-res">${item.res}</span>
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
        "name": "X Glass Downloader",
        "short_name": "𝕏 Glass",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#08090c",
        "theme_color": "#08090c"
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
            
            # Photos
            photos = media.get('photos', [])
            for idx, p in enumerate(photos, 1):
                p_url = p.get('url', '')
                if p_url:
                    items.append({
                        'type': 'photo',
                        'preview': p_url,
                        'download_url': p_url,
                        'res': f"ภาพที่ {idx}",
                        'size': 'HD'
                    })

            # Videos
            videos = media.get('videos', [])
            for idx, v in enumerate(videos, 1):
                thumb = v.get('thumbnail_url', '')
                variants = v.get('variants', [])
                
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
                        'res': f"คลิป {idx} ({res_label})",
                        'size': size_str
                    })

    except Exception:
        return jsonify({'error': 'ไม่สามารถเชื่อมต่อดึงข้อมูลได้'}), 500

    if not items:
        return jsonify({'error': 'ไม่พบสื่อในลิงก์นี้'}), 400

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

