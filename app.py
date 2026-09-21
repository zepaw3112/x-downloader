import os
import re
import json
import requests
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>𝕏 (Twitter) Downloader</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#08090c">
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
        body { background-color: #08090c; color: #f5f5f7; margin: 0; padding: 20px 16px; display: flex; justify-content: center; min-height: 100vh; }
        .ambient-glow { position: fixed; top: -100px; left: 50%; transform: translateX(-50%); width: 450px; height: 450px; background: radial-gradient(circle, rgba(29, 155, 240, 0.35) 0%, rgba(0,0,0,0) 70%); filter: blur(80px); z-index: -1; pointer-events: none; }
        .container { width: 100%; max-width: 460px; z-index: 1; }
        .header { text-align: center; margin-bottom: 24px; }
        .header h1 { font-size: 26px; font-weight: 800; background: linear-gradient(135deg, #ffffff 30%, #1d9bf0 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 6px 0; }
        .header p { font-size: 13px; color: rgba(235, 235, 245, 0.6); margin: 0; }
        .search-card { background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(30px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 22px; padding: 6px; display: flex; gap: 8px; margin-bottom: 24px; }
        .search-card input { flex: 1; background: transparent; border: none; padding: 14px 16px; color: #fff; font-size: 14px; outline: none; }
        .search-card button { background: linear-gradient(135deg, #1d9bf0 0%, #0072c6 100%); color: #fff; border: none; border-radius: 16px; padding: 0 20px; font-weight: 700; cursor: pointer; }
        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
        .media-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; position: relative; }
        .preview-wrapper { width: 100%; height: 170px; background: rgba(0, 0, 0, 0.4); position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .preview-wrapper img { width: 100%; height: 100%; object-fit: cover; }
        .badge-glass { position: absolute; background: rgba(15, 15, 20, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; font-size: 10px; font-weight: 700; padding: 4px 8px; border-radius: 8px; }
        .badge-type { top: 10px; left: 10px; }
        .badge-index { bottom: 10px; left: 10px; background: rgba(29, 155, 240, 0.8); color: #fff; }
        .badge-duration { bottom: 10px; right: 10px; background: rgba(0, 0, 0, 0.85); color: #34c759; }
        .card-action { padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .glass-select { width: 100%; background: rgba(255, 255, 255, 0.08); color: #f5f5f7; border: 1px solid rgba(255, 255, 255, 0.15); padding: 8px 10px; border-radius: 10px; font-size: 12px; font-weight: 600; outline: none; }
        .glass-select option { background: #1c1c1e; color: #fff; }
        .dl-btn { display: flex; align-items: center; justify-content: center; width: 100%; background: rgba(29, 155, 240, 0.2); color: #70baff; border: 1px solid rgba(29, 155, 240, 0.4); padding: 10px 0; border-radius: 10px; font-size: 12px; font-weight: 700; cursor: pointer; text-decoration: none; }
        .loading-box { text-align: center; padding: 40px 0; color: rgba(235, 235, 245, 0.5); font-size: 14px; display: none; }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>
    <div class="container">
        <div class="header">
            <h1>𝕏 (Twitter) Downloader</h1>
            <p>วางลิงก์โพสต์จาก X เพื่อดาวน์โหลดรูปภาพและวิดีโอ HD</p>
        </div>
        <div class="search-card">
            <input type="text" id="urlInput" placeholder="วางลิงก์ X (Twitter) ที่นี่...">
            <button onclick="fetchMedia()" id="submitBtn">สแกน</button>
        </div>
        <div class="loading-box" id="loading">✨ กำลังดึงข้อมูลรูปภาพและวิดีโอจาก 𝕏...</div>
        <div class="grid-container" id="mediaGrid"></div>
    </div>
    <script>
        let fetchedItems = [];
        async function fetchMedia() {
            const url = document.getElementById('urlInput').value.trim();
            if(!url) return alert('กรุณาใส่ลิงก์ X (Twitter) ก่อนครับ');
            const btn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const grid = document.getElementById('mediaGrid');
            btn.disabled = true; loading.style.display = 'block'; grid.innerHTML = '';
            try {
                const res = await fetch('/get-media', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url })
                });
                const data = await res.json();
                btn.disabled = false; loading.style.display = 'none';
                if(!res.ok || data.error) return alert(data.error || 'เกิดข้อผิดพลาดในการดึงข้อมูล');
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
                        selectHtml = `<div style="font-size: 11px; color: #8e8e93; text-align: center; padding: 4px;">${item.options[0].label}</div>`;
                    }
                    
                    let durationHtml = item.duration ? `<span class="badge-glass badge-duration">⏱️ ${item.duration}</span>` : '';
                    let countBadge = fetchedItems.length > 1 ? `<span class="badge-glass badge-index">#${index + 1}</span>` : '';
                    
                    card.innerHTML = `
                        <div class="preview-wrapper">
                            <img src="${item.preview}" alt="preview" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=300'">
                            <span class="badge-glass badge-type">${item.type === 'video' ? '🎥 VIDEO' : '🖼️ PHOTO'}</span>
                            ${countBadge}
                            ${durationHtml}
                        </div>
                        <div class="card-action">
                            ${selectHtml}
                            <button onclick="downloadItem(${index})" class="dl-btn">⬇️ ดาวน์โหลด</button>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (e) {
                btn.disabled = false; loading.style.display = 'none';
                alert('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
            }
        }
        function downloadItem(index) {
            const item = fetchedItems[index];
            if(!item) return;
            let targetUrl = item.options[0].url;
            const selectElem = document.getElementById(`select-${index}`);
            if(selectElem) targetUrl = item.options[selectElem.value].url;
            window.location.href = `/download-file?url=${encodeURIComponent(targetUrl)}&type=${item.type}`;
        }
    </script>
</body>
</html>
"""

def format_sec(seconds):
    if not seconds: return None
    try:
        sec = float(seconds)
        if sec <= 0: return None
        if sec > 1000: sec = sec / 1000
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
    except Exception:
        return None

def is_profile_image(url):
    if not url: return True
    u = url.lower()
    bad_keywords = ['profile_images', 'profile_banners', 'default_profile', 'avatar', 'favicon', 'logo']
    return any(k in u for k in bad_keywords)

def extract_x_media(url):
    match = re.search(r'(?:status|statuses)/(\d+)', url)
    if not match: return None
    tweet_id = match.group(1)
    headers = {'User-Agent': BROWSER_UA}
    
    api_endpoints = [
        f"https://api.fxtwitter.com/status/{tweet_id}",
        f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
    ]
    
    for api_url in api_endpoints:
        try:
            r = requests.get(api_url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                tweet = data.get('tweet') or data
                media = tweet.get('media', {})
                items = []
                
                # 1. ดึงวิดีโอ / GIFs
                videos = media.get('videos', []) or tweet.get('media_extended', [])
                for v in videos:
                    if isinstance(v, dict) and (v.get('type') in ['video', 'gif'] or 'variants' in v or 'duration' in v):
                        thumb = v.get('thumbnail_url') or v.get('url')
                        dur_raw = v.get('duration') or v.get('duration_millis') or v.get('duration_seconds')
                        dur = format_sec(dur_raw)
                        
                        variants = [var for var in v.get('variants', []) if isinstance(var, dict) and var.get('url', '').split('?')[0].endswith('.mp4')]
                        variants.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                        
                        opts = []
                        seen = set()
                        for var in variants:
                            v_url = var.get('url', '')
                            res_m = re.search(r'/(\d+)x(\d+)/', v_url)
                            label = f"{min(int(res_m.group(1)), int(res_m.group(2)))}p" if res_m else "HD Video"
                            if label not in seen:
                                seen.add(label)
                                opts.append({'label': label, 'url': v_url})
                        
                        if not opts and v.get('url'):
                            opts.append({'label': 'HD Video', 'url': v.get('url')})
                            
                        if opts:
                            items.append({'type': 'video', 'platform': '𝕏', 'preview': thumb, 'duration': dur, 'options': opts})
                
                # 2. ดึงรูปภาพทั้งหมดในทวีต (รองรับชุดรูปสูงสุด 4 รูป)
                photos = media.get('photos', [])
                if not photos and isinstance(tweet.get('media_extended'), list):
                    photos = [m for m in tweet['media_extended'] if m.get('type') == 'image']
                    
                for p in photos:
                    p_url = p.get('url') if isinstance(p, dict) else p
                    if p_url and not is_profile_image(p_url):
                        # เปลี่ยน URL ให้เป็นความละเอียดสูงสุด (:orig หรือ ?name=large)
                        orig_url = re.sub(r'name=\w+', 'name=large', p_url)
                        items.append({'type': 'photo', 'platform': '𝕏', 'preview': orig_url, 'options': [{'label': 'HD Photo', 'url': orig_url}]})
                
                if items: return items
        except Exception:
            continue

    return None

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "X Downloader", "short_name": "XDownloader", "start_url": "/", "display": "standalone", "background_color": "#08090c", "theme_color": "#08090c"})

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('fetch', function(e) {});", mimetype='application/javascript')

@app.route('/get-media', methods=['POST'])
def get_media():
    try:
        raw_url = request.json.get('url', '').strip() if request.json else ''
        if not raw_url:
            return jsonify({'error': 'กรุณาใส่ลิงก์'}), 400

        # ตรวจสอบว่าเป็นลิงก์ X/Twitter หรือไม่
        if not any(k in raw_url.lower() for k in ['twitter.com', 'x.com', 't.co', 'fixupx.com', 'fxtwitter.com']):
            return jsonify({'error': 'รองรับเฉพาะลิงก์จาก 𝕏 (Twitter) เท่านั้นครับ'}), 400

        # 1. ดึงข้อมูลรูปภาพ/วิดีโอผ่าน Twitter API Proxy
        items = extract_x_media(raw_url)

        # 2. Fallback ด้วย yt-dlp สำรอง
        if not items and HAS_YTDLP:
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'user_agent': BROWSER_UA
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(raw_url, download=False)
                    entries = info.get('entries') or [info]
                    items = []
                    
                    for entry in entries:
                        if not entry: continue
                        preview = entry.get('thumbnail') or entry.get('url')
                        duration_str = format_sec(entry.get('duration'))

                        formats = entry.get('formats', [])
                        video_opts = []
                        seen_res = set()
                        
                        for f in formats:
                            if f.get('vcodec') != 'none' and f.get('url'):
                                h = f.get('height')
                                label = f"{h}p" if h else "HD Video"
                                if label not in seen_res:
                                    seen_res.add(label)
                                    video_opts.append({'label': label, 'url': f.get('url')})
                                    
                        video_opts.sort(key=lambda x: int(x['label'].replace('p','')) if 'p' in x['label'] else 0, reverse=True)

                        if video_opts and entry.get('vcodec') != 'none':
                            items.append({'type': 'video', 'platform': '𝕏', 'preview': preview, 'duration': duration_str, 'options': video_opts})
                        else:
                            img_url = entry.get('url')
                            if not img_url or img_url.endswith('.mp4'):
                                thumbs = entry.get('thumbnails', [])
                                if thumbs: img_url = thumbs[-1].get('url')
                                else: img_url = preview
                            if img_url and not is_profile_image(img_url):
                                items.append({'type': 'photo', 'platform': '𝕏', 'preview': img_url, 'options': [{'label': 'HD Photo', 'url': img_url}]})
            except Exception:
                pass

        if items:
            return jsonify({'items': items})

        return jsonify({'error': 'ไม่พบสื่อในทวีตนี้ หรือทวีตถูกลบ/ตั้งเป็นส่วนตัว'}), 400

    except Exception as err:
        return jsonify({'error': f'เกิดข้อผิดพลาดจากเซิร์ฟเวอร์: {str(err)}'}), 500

@app.route('/download-file')
def download_file():
    media_url = request.args.get('url')
    media_type = request.args.get('type', 'video')
    if not media_url: return "Missing URL", 400
    headers = {'User-Agent': BROWSER_UA}
    try:
        req = requests.get(media_url, headers=headers, stream=True)
        ext = "jpg" if media_type == 'photo' else "mp4"
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024 * 64)),
            content_type=req.headers.get('content-type', 'application/octet-stream'),
            headers={'Content-Disposition': f'attachment; filename="x_download.{ext}"'}
        )
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

