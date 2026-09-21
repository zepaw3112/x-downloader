import re
import html
import requests
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

        <div class="loading-box" id="loading">✨ กำลังประมวลผลลิงก์...</div>
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
                            selectHtml += `<option value="${optIdx}">${opt.label} ${opt.size ? '· ' + opt.size : ''}</option>`;
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

# --- Engine: Instagram Scraper ---
def parse_instagram(url):
    match = re.search(r'/(p|reel|reels|tv)/([A-Za-z0-9_-]+)', url)
    if not match:
        return None, "ลิงก์ Instagram ไม่ถูกต้อง"
    
    shortcode = match.group(2)
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        r = requests.get(embed_url, headers=headers, timeout=7)
        if r.status_code == 200:
            raw_html = html.unescape(r.text.replace('\\/', '/').replace('\\u0026', '&'))
            
            # Extract Video
            v_match = re.search(r'video_url["\']\s*:\s*["\']([^"']+)["\']', raw_html) or \
                      re.search(r'<meta property="og:video"\s+content="([^"]+)"', raw_html) or \
                      re.search(r'class="EmbeddedMediaVideo"[^>]*src="([^"]+)"', raw_html)
            
            # Extract Image
            i_match = re.search(r'display_url["\']\s*:\s*["\']([^"']+)["\']', raw_html) or \
                      re.search(r'<meta property="og:image"\s+content="([^"]+)"', raw_html) or \
                      re.search(r'class="EmbeddedMediaImage"[^>]*src="([^"]+)"', raw_html)

            video_url = v_match.group(1) if v_match else None
            img_url = i_match.group(1) if i_match else None

            if video_url:
                return [{
                    'type': 'video',
                    'platform': 'Instagram',
                    'preview': img_url or video_url,
                    'options': [{'label': 'HD Reel / Video', 'url': video_url, 'size': 'MP4'}]
                }], None
            elif img_url:
                return [{
                    'type': 'photo',
                    'platform': 'Instagram',
                    'preview': img_url,
                    'options': [{'label': 'HD Photo', 'url': img_url, 'size': 'JPG'}]
                }], None
    except Exception as e:
        pass

    return None, "ไม่สามารถดึงข้อมูลจาก Instagram ได้ (โปรดตรวจสอบว่าโพสต์ตั้งค่าเป็นสาธารณะหรือไม่)"

# --- Engine: Facebook Scraper ---
def parse_facebook(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        clean_url = url.split('?')[0]
        r = requests.get(clean_url, headers=headers, timeout=7)
        if r.status_code == 200:
            raw_html = r.text.replace('\\/', '/')
            options = []
            
            hd_match = re.search(r'browser_native_hd_url["\']\s*:\s*["\']([^"']+)["\']', raw_html) or \
                       re.search(r'hd_src["\']\s*:\s*["\']([^"']+)["\']', raw_html)
            sd_match = re.search(r'browser_native_sd_url["\']\s*:\s*["\']([^"']+)["\']', raw_html) or \
                       re.search(r'sd_src["\']\s*:\s*["\']([^"']+)["\']', raw_html)
            
            if hd_match:
                options.append({'label': 'HD Quality', 'url': hd_match.group(1).encode().decode('unicode-escape'), 'size': ''})
            if sd_match:
                options.append({'label': 'SD Quality', 'url': sd_match.group(1).encode().decode('unicode-escape'), 'size': ''})

            if options:
                return [{
                    'type': 'video',
                    'platform': 'Facebook',
                    'preview': options[0]['url'],
                    'options': options
                }], None
    except Exception:
        pass

    return None, "ไม่สามารถดึงข้อมูลคลิปจาก Facebook ได้"

@app.route('/get-media', methods=['POST'])
def get_media():
    raw_url = request.json.get('url', '').strip()
    if not raw_url:
        return jsonify({'error': 'กรุณาใส่ลิงก์'}), 400

    # 1. X (Twitter)
    if 'twitter.com' in raw_url or 'x.com' in raw_url:
        match = re.search(r'status/(\d+)', raw_url)
        if not match:
            return jsonify({'error': 'ลิงก์ X ไม่ถูกต้อง'}), 400
        
        tweet_id = match.group(1)
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
        items = []

        try:
            r = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers=headers, timeout=6)
            if r.status_code == 200:
                tweet = r.json().get('tweet', {})
                media = tweet.get('media', {})

                for idx, p in enumerate(media.get('photos', []), 1):
                    p_url = p.get('url', '')
                    if p_url:
                        items.append({
                            'type': 'photo', 'platform': '𝕏', 'preview': p_url,
                            'options': [{'label': f'ภาพที่ {idx} (HD)', 'url': p_url, 'size': ''}]
                        })

                for idx, v in enumerate(media.get('videos', []), 1):
                    thumb = v.get('thumbnail_url', '')
                    variants = [item for item in v.get('variants', []) if item.get('url', '').split('?')[0].endswith('.mp4')]
                    variants.sort(key=lambda x: x.get('bitrate', 0), reverse=True)

                    video_options = []
                    for var in variants:
                        v_url = var.get('url', '')
                        res_match = re.search(r'/(\d+)x(\d+)/', v_url)
                        res_label = f"{min(int(res_match.group(1)), int(res_match.group(2)))}p" if res_match else "HD"
                        video_options.append({'label': res_label, 'url': v_url, 'size': ''})

                    if video_options:
                        items.append({'type': 'video', 'platform': '𝕏', 'preview': thumb, 'options': video_options})
                
                return jsonify({'items': items})
        except Exception:
            return jsonify({'error': 'ไม่สามารถเชื่อมต่อระบบ X ได้'}), 500

    # 2. Instagram
    elif 'instagram.com' in raw_url or 'instagr.am' in raw_url:
        items, err = parse_instagram(raw_url)
        if err: return jsonify({'error': err}), 400
        return jsonify({'items': items})

    # 3. Facebook
    elif 'facebook.com' in raw_url or 'fb.watch' in raw_url or 'fb.gg' in raw_url:
        items, err = parse_facebook(raw_url)
        if err: return jsonify({'error': err}), 400
        return jsonify({'items': items})

    else:
        return jsonify({'error': 'รองรับเฉพาะลิงก์ X, Instagram และ Facebook เท่านั้น'}), 400

@app.route('/download-file')
def download_file():
    media_url = request.args.get('url')
    media_type = request.args.get('type', 'video')
    
    if not media_url: return "Missing URL", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = requests.get(media_url, headers=headers, stream=True)
    
    ext = "jpg" if media_type == 'photo' else "mp4"
    filename = f"downloaded_media.{ext}"

    return Response(
        stream_with_context(req.iter_content(chunk_size=1024 * 64)),
        content_type=req.headers.get('content-type', 'application/octet-stream'),
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

