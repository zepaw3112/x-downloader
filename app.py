import re
import requests
import html
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>𝕏 / IG / FB Universal Downloader</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#08090c">
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
        body { background-color: #08090c; color: #f5f5f7; margin: 0; padding: 20px 16px; display: flex; justify-content: center; min-height: 100vh; }
        .ambient-glow-1 { position: fixed; top: -100px; left: -80px; width: 320px; height: 320px; background: radial-gradient(circle, rgba(29, 155, 240, 0.4) 0%, rgba(0,0,0,0) 70%); filter: blur(65px); z-index: -1; pointer-events: none; }
        .ambient-glow-2 { position: fixed; top: 40%; right: -100px; width: 350px; height: 350px; background: radial-gradient(circle, rgba(225, 48, 108, 0.35) 0%, rgba(0,0,0,0) 70%); filter: blur(75px); z-index: -1; pointer-events: none; }
        .container { width: 100%; max-width: 460px; z-index: 1; }
        .header { text-align: center; margin-bottom: 24px; }
        .header h1 { font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #ffffff 20%, #70baff 60%, #e1306c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 6px 0; }
        .header p { font-size: 13px; color: rgba(235, 235, 245, 0.6); margin: 0; }
        .platform-tags { display: flex; justify-content: center; gap: 8px; margin-top: 10px; }
        .tag { font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: #aaa; }
        .search-card { background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(30px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 22px; padding: 6px; display: flex; gap: 8px; margin-bottom: 24px; }
        .search-card input { flex: 1; background: transparent; border: none; padding: 14px 16px; color: #fff; font-size: 14px; outline: none; }
        .search-card button { background: linear-gradient(135deg, #1d9bf0 0%, #0072c6 100%); color: #fff; border: none; border-radius: 16px; padding: 0 20px; font-weight: 600; cursor: pointer; }
        .grid-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
        .media-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; position: relative; }
        .preview-wrapper { width: 100%; height: 170px; background: rgba(0, 0, 0, 0.4); position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .preview-wrapper img { width: 100%; height: 100%; object-fit: cover; }
        .badge-glass { position: absolute; background: rgba(15, 15, 20, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; font-size: 10px; font-weight: 700; padding: 4px 8px; border-radius: 8px; }
        .badge-type { top: 10px; left: 10px; }
        .badge-platform { top: 10px; right: 10px; color: #70baff; text-transform: uppercase; }
        .badge-duration { bottom: 10px; right: 10px; background: rgba(0, 0, 0, 0.85); color: #34c759; }
        .card-action { padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .glass-select { width: 100%; background: rgba(255, 255, 255, 0.08); color: #f5f5f7; border: 1px solid rgba(255, 255, 255, 0.15); padding: 8px 10px; border-radius: 10px; font-size: 12px; font-weight: 600; outline: none; }
        .glass-select option { background: #1c1c1e; color: #fff; }
        .dl-btn { display: flex; align-items: center; justify-content: center; width: 100%; background: rgba(52, 199, 89, 0.15); color: #34c759; border: 1px solid rgba(52, 199, 89, 0.3); padding: 10px 0; border-radius: 10px; font-size: 12px; font-weight: 700; cursor: pointer; text-decoration: none; }
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
        <div class="loading-box" id="loading">✨ กำลังแกะลิงก์และประมวลผล...</div>
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
            btn.disabled = true; loading.style.display = 'block'; grid.innerHTML = '';
            try {
                const res = await fetch('/get-media', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url })
                });
                const data = await res.json();
                btn.disabled = false; loading.style.display = 'none';
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
                        selectHtml = `<div style="font-size: 11px; color: #8e8e93; text-align: center; padding: 4px;">${item.options[0].label}</div>`;
                    }
                    
                    let durationHtml = item.duration ? `<span class="badge-glass badge-duration">⏱️ ${item.duration}</span>` : '';
                    
                    card.innerHTML = `
                        <div class="preview-wrapper">
                            <img src="${item.preview}" alt="preview" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=300'">
                            <span class="badge-glass badge-type">${item.type === 'video' ? '🎥 VIDEO' : '🖼️ PHOTO'}</span>
                            <span class="badge-glass badge-platform">${item.platform}</span>
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
                alert('เกิดข้อผิดพลาดในการดึงข้อมูล');
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
        sec = int(float(seconds))
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
    except:
        return None

def detect_platform(url):
    u = url.lower()
    if 'twitter.com' in u or 'x.com' in u: return '𝕏'
    if 'instagram.com' in u or 'instagr.am' in u: return 'Instagram'
    if 'facebook.com' in u or 'fb.watch' in u or 'fb.com' in u: return 'Facebook'
    return 'Media'

def resolve_url(raw_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    try:
        r = requests.get(raw_url, headers=headers, allow_redirects=True, timeout=8)
        return r.url, r.text
    except Exception:
        return raw_url, ""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "Universal Downloader", "short_name": "Downloader", "start_url": "/", "display": "standalone", "background_color": "#08090c", "theme_color": "#08090c"})

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('fetch', function(e) {});", mimetype='application/javascript')

@app.route('/get-media', methods=['POST'])
def get_media():
    raw_url = request.json.get('url', '').strip()
    if not raw_url:
        return jsonify({'error': 'กรุณาใส่ลิงก์'}), 400

    # 1. แปลงลิงก์ย่อ (/share/ หรือ fb.watch) ให้กลายเป็นลิงก์เต็มก่อนเสมอ
    final_url, page_html = resolve_url(raw_url)
    platform_name = detect_platform(final_url)
    items = []

    # 2. ลองดึงข้อมูลด้วย yt-dlp
    if HAS_YTDLP:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(final_url, download=False)
                entries = info.get('entries') or [info]
                
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
                        items.append({'type': 'video', 'platform': platform_name, 'preview': preview, 'duration': duration_str, 'options': video_opts})
                    else:
                        img_url = entry.get('url')
                        if not img_url or img_url.endswith('.mp4'):
                            thumbs = entry.get('thumbnails', [])
                            if thumbs: img_url = thumbs[-1].get('url')
                            else: img_url = preview
                        if img_url:
                            items.append({'type': 'photo', 'platform': platform_name, 'preview': img_url, 'options': [{'label': 'HD Photo', 'url': img_url}]})
        except Exception:
            pass

    if items:
        return jsonify({'items': items})

    # 3. หาก yt-dlp ดึงไม่ได้ (เช่น รูปภาพ FB/IG) ให้สลับมาใช้ระบบ Open Graph Scraping สำรอง
    if page_html:
        def get_meta(prop):
            m = re.search(r'<meta\s+(?:property|name)=["\']' + re.escape(prop) + r'["\']\s+content=["\']([^"\']+)["\']', page_html, re.I) or \
                re.search(r'content=["\']([^"\']+)["\']\s+(?:property|name)=["\']' + re.escape(prop) + r'["\']', page_html, re.I)
            return html.unescape(m.group(1)) if m else None

        og_vid = get_meta('og:video') or get_meta('og:video:secure_url')
        og_img = get_meta('og:image')
        og_dur = format_sec(get_meta('video:duration') or get_meta('og:video:duration'))

        if og_vid:
            items.append({'type': 'video', 'platform': platform_name, 'preview': og_img or og_vid, 'duration': og_dur, 'options': [{'label': 'HD Video', 'url': og_vid}]})
            return jsonify({'items': items})
        elif og_img:
            items.append({'type': 'photo', 'platform': platform_name, 'preview': og_img, 'options': [{'label': 'HD Photo', 'url': og_img}]})
            return jsonify({'items': items})

    # 4. ระบบสำรองกรณี Twitter/X
    if 'twitter.com' in final_url or 'x.com' in final_url:
        match = re.search(r'status/(\d+)', final_url)
        if match:
            tweet_id = match.group(1)
            try:
                r = requests.get(f"https://api.fxtwitter.com/status/{tweet_id}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                if r.status_code == 200:
                    tweet = r.json().get('tweet', {})
                    media = tweet.get('media', {})
                    for p in media.get('photos', []):
                        items.append({'type': 'photo', 'platform': '𝕏', 'preview': p.get('url'), 'options': [{'label': 'HD Photo', 'url': p.get('url')}]})
                    for v in media.get('videos', []):
                        thumb = v.get('thumbnail_url', '')
                        dur_str = format_sec(v.get('duration_ms', 0) / 1000) if v.get('duration_ms') else None
                        variants = [item for item in v.get('variants', []) if item.get('url', '').split('?')[0].endswith('.mp4')]
                        variants.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
                        opts = []
                        for var in variants:
                            v_url = var.get('url', '')
                            res_match = re.search(r'/(\d+)x(\d+)/', v_url)
                            res_label = f"{min(int(res_match.group(1)), int(res_match.group(2)))}p" if res_match else "HD"
                            opts.append({'label': res_label, 'url': v_url})
                        if opts: items.append({'type': 'video', 'platform': '𝕏', 'preview': thumb, 'duration': dur_str, 'options': opts})
                    if items: return jsonify({'items': items})
            except Exception: pass

    return jsonify({'error': 'ไม่สามารถดึงข้อมูลจากลิงก์นี้ได้ โปรดตรวจสอบว่าเป็นโพสต์สาธารณะ'}), 400

@app.route('/download-file')
def download_file():
    media_url = request.args.get('url')
    media_type = request.args.get('type', 'video')
    if not media_url: return "Missing URL", 400
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = requests.get(media_url, headers=headers, stream=True)
    ext = "jpg" if media_type == 'photo' else "mp4"
    return Response(
        stream_with_context(req.iter_content(chunk_size=1024 * 64)),
        content_type=req.headers.get('content-type', 'application/octet-stream'),
        headers={'Content-Disposition': f'attachment; filename="media_download.{ext}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

