import re
import requests
import yt_dlp
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>𝕏 / IG / FB Universal Downloader</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#08090c">
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

        .ambient-glow-1 {
            position: fixed; top: -100px; left: -80px; width: 320px; height: 320px;
            background: radial-gradient(circle, rgba(29, 155, 240, 0.4) 0%, rgba(0,0,0,0) 70%);
            filter: blur(65px); z-index: -1; pointer-events: none;
        }
        .ambient-glow-2 {
            position: fixed; top: 40%; right: -100px; width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(225, 48, 108, 0.35) 0%, rgba(0,0,0,0) 70%);
            filter: blur(75px); z-index: -1; pointer-events: none;
        }

        .container { width: 100%; max-width: 460px; z-index: 1; }

        .header { text-align: center; margin-bottom: 24px; }
        .header h1 { 
            font-size: 24px; font-weight: 800; letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff 20%, #70baff 60%, #e1306c 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin: 0 0 6px 0; 
        }
        .header p { font-size: 13px; color: rgba(235, 235, 245, 0.6); margin: 0; font-weight: 400; }

        .platform-tags { display: flex; justify-content: center; gap: 8px; margin-top: 10px; }
        .tag { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: #aaa; }

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

        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }

        .media-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(25px) saturate(190%);
            -webkit-backdrop-filter: blur(25px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.12);
            border-radius: 20px; overflow: hidden;
            display: flex; flex-direction: column;
        }

        .preview-wrapper {
            width: 100%; height: 170px; background: rgba(0, 0, 0, 0.4);
            position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden;
        }
        .preview-wrapper img { width: 100%; height: 100%; object-fit: cover; }

        .badge-glass {
            position: absolute;
            background: rgba(15, 15, 20, 0.65);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff; font-size: 10px; font-weight: 700;
            padding: 4px 8px; border-radius: 8px;
        }
        .badge-type { top: 10px; left: 10px; }
        .badge-platform { top: 10px; right: 10px; color: #70baff; text-transform: uppercase; }

        .card-action { padding: 10px; display: flex; flex-direction: column; gap: 8px; }

        .glass-select {
            width: 100%;
            background: rgba(255, 255, 255, 0.08);
            color: #f5f5f7;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 8px 10px;
            border-radius: 10px;
            font-size: 12px; font-weight: 600;
            outline: none;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }
        .glass-select option { background: #1c1c1e; color: #fff; }

        .dl-btn {
            display: flex; align-items: center; justify-content: center; gap: 6px;
            width: 100%; background: rgba(52, 199, 89, 0.15);
            color: #34c759; border: 1px solid rgba(52, 199, 89, 0.3);
            padding: 10px 0; border-radius: 10px; font-size: 12px; font-weight: 700;
            text-decoration: none; cursor: pointer; transition: all 0.2s ease;
        }
        .dl-btn:active { background: #34c759; color: #fff; box-shadow: 0 4px 15px rgba(52, 199, 89, 0.4); }

        .loading-box { text-align: center; padding: 40px 0; color: rgba(235, 235, 245, 0.5); font-size: 14px; display: none; }
    </style>
</head>
<body>
    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>

    <div class="container">
        <div class="header">
            <h1>𝕏 Universal Downloader</h1>
            <p>วางลิงก์ X, Instagram หรือ Facebook เพื่อดาวน์โหลด</p>
            <div class="platform-tags">
                <span class="tag">𝕏 Twitter</span>
                <span class="tag">📸 Instagram</span>
                <span class="tag">📘 Facebook</span>
            </div>
        </div>

        <div class="search-card">
            <input type="text" id="urlInput" placeholder="วางลิงก์ที่นี่...">
            <button onclick="fetchMedia()" id="submitBtn">สแกน</button>
        </div>

        <div class="loading-box" id="loading">✨ กำลังถอดรหัสสื่อด้วย yt-dlp...</div>
        <div class="grid-container" id="mediaGrid"></div>
    </div>

    <script>
        let fetchedItems = [];

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

                fetchedItems = data.items;

                fetchedItems.forEach((item, index) => {
                    const card = document.createElement('div');
                    card.className = 'media-card';
                    
                    let selectHtml = '';
                    if(item.options && item.options.length > 1) {
                        selectHtml = `<select class="glass-select" id="select-${index}">`;
                        item.options.forEach((opt, optIdx) => {
                            selectHtml += `<option value="${optIdx}">${opt.label}</option>`;
                        });
                        selectHtml += `</select>`;
                    } else if (item.options && item.options.length === 1) {
                        selectHtml = `<div style="font-size: 11px; color: #8e8e93; text-align: center;">${item.options[0].label}</div>`;
                    }

                    card.innerHTML = `
                        <div class="preview-wrapper">
                            <img src="${item.preview}" alt="preview" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=300'">
                            <span class="badge-glass badge-type">${item.type === 'video' ? '🎥 VIDEO' : '🖼️ PHOTO'}</span>
                            <span class="badge-glass badge-platform">${item.platform}</span>
                        </div>
                        <div class="card-action">
                            ${selectHtml}
                            <button onclick="downloadItem(${index})" class="dl-btn">
                                ⬇️ ดาวน์โหลด
                            </button>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (e) {
                btn.disabled = false;
                loading.style.display = 'none';
                alert('เกิดข้อผิดพลาดในการดึงข้อมูล');
            }
        }

        function downloadItem(index) {
            const item = fetchedItems[index];
            if(!item) return;

            let targetUrl = item.options[0].url;
            const selectElem = document.getElementById(`select-${index}`);
            if(selectElem) {
                const selectedOptIndex = selectElem.value;
                targetUrl = item.options[selectedOptIndex].url;
            }

            window.location.href = `/download-file?url=${encodeURIComponent(targetUrl)}&type=${item.type}`;
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
        "name": "Universal Downloader",
        "short_name": "Downloader",
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
    if not raw_url:
        return jsonify({'error': 'กรุณาใส่ลิงก์'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': 'best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    }

    items = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(raw_url, download=False)
            
            extractor = info.get('extractor_key', '').lower()
            if 'twitter' in extractor: platform = '𝕏'
            elif 'instagram' in extractor: platform = 'Instagram'
            elif 'facebook' in extractor: platform = 'Facebook'
            else: platform = 'Media'

            entries = info.get('entries')
            raw_list = list(entries) if entries else [info]

            for entry in raw_list:
                preview = entry.get('thumbnail') or entry.get('url')
                formats = entry.get('formats', [])
                
                video_opts = []
                seen_res = set()
                
                # กรองวิดีโอเรียงจากความชัดสูงไปต่ำ
                valid_formats = [f for f in formats if f.get('url') and f.get('vcodec') != 'none']
                valid_formats.sort(key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                
                for f in valid_formats:
                    h = f.get('height')
                    label = f"{h}p" if h else "HD Video"
                    if label not in seen_res:
                        seen_res.add(label)
                        video_opts.append({'label': label, 'url': f.get('url')})

                # กรณีลิงก์ตรงไม่มี formats
                if not video_opts and (entry.get('url') or entry.get('direct')):
                    direct_url = entry.get('url')
                    if direct_url:
                        video_opts.append({'label': 'HD Video', 'url': direct_url})

                if video_opts and entry.get('vcodec') != 'none':
                    items.append({
                        'type': 'video',
                        'platform': platform,
                        'preview': preview,
                        'options': video_opts
                    })
                else:
                    img_url = entry.get('url') or preview
                    items.append({
                        'type': 'photo',
                        'platform': platform,
                        'preview': img_url,
                        'options': [{'label': 'HD Photo', 'url': img_url}]
                    })

    except Exception as e:
        return jsonify({'error': 'ไม่สามารถดึงข้อมูลสื่อจากลิงก์นี้ได้ (โปรดตรวจสอบว่าโพสต์เป็นสาธารณะหรือไม่)'}), 400

    if not items:
        return jsonify({'error': 'ไม่พบสื่อในลิงก์นี้'}), 400

    return jsonify({'items': items})

@app.route('/download-file')
def download_file():
    media_url = request.args.get('url')
    media_type = request.args.get('type', 'video')
    
    if not media_url: return "Missing URL", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = requests.get(media_url, headers=headers, stream=True)
    
    ext = "jpg" if media_type == 'photo' else "mp4"
    filename = f"media_download.{ext}"

    return Response(
        stream_with_context(req.iter_content(chunk_size=1024 * 64)),
        content_type=req.headers.get('content-type', 'application/octet-stream'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
