import os
import re
import json
import requests
import html
from urllib.parse import unquote
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context

app = Flask(__name__)

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
MOBILE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>𝕏 / IG Downloader</title>
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
        .tag { font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 8px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: #ccc; }
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
        .badge-index { bottom: 10px; left: 10px; background: rgba(255, 255, 255, 0.2); color: #fff; }
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
            <h1>𝕏 / IG Downloader</h1>
            <p>วางลิงก์ X หรือ Instagram เพื่อดาวน์โหลดรูปและวิดีโอ</p>
            <div class="platform-tags">
                <span class="tag">𝕏 Twitter</span>
                <span class="tag">📸 Instagram</span>
            </div>
        </div>
        <div class="search-card">
            <input type="text" id="urlInput" placeholder="วางลิงก์ X หรือ IG ที่นี่...">
            <button onclick="fetchMedia()" id="submitBtn">สแกน</button>
        </div>
        <div class="loading-box" id="loading">✨ กำลังค้นหาไฟล์สื่อทั้งหมดในโพสต์...</div>
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
                            <span class="badge-glass badge-platform">${item.platform}</span>
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
    bad_keywords = ['profile_images', 'profile_banners', 'default_profile', 'avatar', 'favicon', 'logo', '150x150', '320x320']
    return any(k in u for k in bad_keywords)

def detect_platform(url):
    u = url.lower()
    if 'twitter.com' in u or 'x.com' in u or 't.co' in u: return '𝕏'
    if 'instagram.com' in u or 'instagr.am' in u: return 'Instagram'
    return 'Media'

def resolve_url(raw_url):
    headers = {'User-Agent': BROWSER_UA}
    try:
        r = requests.get(raw_url, headers=headers, allow_redirects=True, timeout=8)
        return r.url, r.text
    except Exception:
        return raw_url, ""

def extract_x_media(final_url):
    match = re.search(r'status/(\d+)', final_url)
    if not match: return None
    tweet_id = match.group(1)
    headers = {'User-Agent': BROWSER_UA}
    
    api_urls = [
        f"https://api.fxtwitter.com/status/{tweet_id}",
        f"https://api.vxtwitter.com/Twitter/status/{tweet_id}"
    ]
    
    for api_url in api_urls:
        try:
            r = requests.get(api_url, headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json()
                tweet = data.get('tweet') or data
                media = tweet.get('media', {})
                items = []
                
                # ดึงวิดีโอทั้งหมด
                videos = media.get('videos', []) or tweet.get('media_extended', [])
                for v in videos:
                    if v.get('type') == 'video' or 'duration' in v or 'variants' in v:
                        thumb = v.get('thumbnail_url') or v.get('url')
                        dur_raw = v.get('duration') or v.get('duration_millis') or v.get('duration_seconds')
                        dur = format_sec(dur_raw)
                        
                        variants = [var for var in v.get('variants', []) if var.get('url', '').split('?')[0].endswith('.mp4')]
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
                
                # ดึงรูปภาพทั้งหมดในโพสต์
                photos = media.get('photos', [])
                for p in photos:
                    p_url = p.get('url')
                    if p_url and not is_profile_image(p_url):
                        items.append({'type': 'photo', 'platform': '𝕏', 'preview': p_url, 'options': [{'label': 'HD Photo', 'url': p_url}]})
                
                if items: return items
        except Exception:
            continue

    return None

# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------
IG_CODE_RE = re.compile(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]{5,})')
# สัญญาณว่าโพสต์เป็นอัลบั้ม (ต้องมีข้อมูลจริง ไม่ใช่ null)
IG_CAROUSEL_RE = re.compile(
    r'edge_sidecar_to_children\\*"\s*:\s*\{|carousel_media\\*"\s*:\s*\[\s*\{|(?:XDT)?GraphSidecar'
)


def get_ig_shortcode(*urls):
    """หา shortcode จากลิงก์ที่ให้มา (ข้ามลิงก์ /share/ เพราะ id ในนั้นไม่ใช่ shortcode จริง)"""
    for u in urls:
        if not u:
            continue
        u = unquote(u)
        low = u.lower()
        if 'instagram.com' not in low and 'instagr.am' not in low:
            continue
        if '/share/' in low:
            continue
        m = IG_CODE_RE.search(u)
        if m:
            return m.group(1)
    return None


def _ig_unescape(s):
    if not s:
        return ''
    s = (s.replace('\\\\/', '/').replace('\\/', '/')
          .replace('\\\\u0026', '&').replace('\\u0026', '&'))
    return html.unescape(s)


def _ig_find(obj, key):
    """หา dict ตัวแรกที่มี key นี้ และมีค่าจริง (ไม่ใช่ null/ว่าง) เดินลงไปทุกชั้น"""
    if isinstance(obj, dict):
        if obj.get(key):
            return obj
        for v in obj.values():
            r = _ig_find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _ig_find(v, key)
            if r is not None:
                return r
    return None


def _ig_node_to_item(node):
    """แปลง node หนึ่งชิ้น (รองรับทั้งโครงสร้าง GraphQL และ API v1) เป็น item ของแอป"""
    if not isinstance(node, dict):
        return None

    img = node.get('display_url')
    if not img:
        cands = (node.get('image_versions2') or {}).get('candidates') or []
        if cands and isinstance(cands[0], dict):
            img = cands[0].get('url')

    opts = []
    seen = set()
    versions = [v for v in (node.get('video_versions') or []) if isinstance(v, dict) and v.get('url')]
    versions.sort(key=lambda v: (v.get('height') or 0), reverse=True)
    for v in versions:
        w, h = v.get('width'), v.get('height')
        res = min(w, h) if (w and h) else h
        label = f"{res}p" if res else "HD Video"
        if label not in seen:
            seen.add(label)
            opts.append({'label': label, 'url': v['url']})
    if not opts and node.get('video_url'):
        opts.append({'label': 'HD Video', 'url': node['video_url']})

    if opts:
        return {
            'type': 'video',
            'platform': 'Instagram',
            'preview': img or opts[0]['url'],
            'duration': format_sec(node.get('video_duration')),
            'options': opts,
        }
    if img:
        return {
            'type': 'photo',
            'platform': 'Instagram',
            'preview': img,
            'options': [{'label': 'HD Photo', 'url': img}],
        }
    return None


def _ig_items_from_json(blob):
    """ดึงรายการสื่อจาก JSON ทั้งก้อน: อัลบั้มก่อน ถ้าไม่ใช่อัลบั้มค่อยมองเป็นโพสต์เดี่ยว"""
    children = None

    holder = _ig_find(blob, 'edge_sidecar_to_children')
    if holder:
        edges = (holder['edge_sidecar_to_children'] or {}).get('edges') or []
        children = [e.get('node') for e in edges if isinstance(e, dict)]
    else:
        holder = _ig_find(blob, 'carousel_media')
        if holder:
            children = holder['carousel_media']

    if children is None:
        holder = _ig_find(blob, 'display_url') or _ig_find(blob, 'image_versions2')
        children = [holder] if holder else []

    items = []
    for node in children:
        it = _ig_node_to_item(node)
        if it:
            items.append(it)
    return items


def _ig_json_blobs(text):
    """ขุด JSON ออกจากหน้า embed หลายวิธี (ไม่ใช้ regex ตัดวงเล็บอีกต่อไป)"""
    blobs = []

    # (1) JSON ที่ถูกห่อเป็น string อีกชั้น เช่น "contextJSON":"{\"gql_data\":...}"
    for m in re.finditer(r'"contextJSON"\s*:\s*("(?:[^"\\]|\\.)*")', text):
        try:
            blobs.append(json.loads(json.loads(m.group(1))))
        except Exception:
            continue

    # (2) JSON ปกติที่ฝังอยู่ในหน้า: ให้ raw_decode นับวงเล็บซ้อนให้ถูกต้อง
    dec = json.JSONDecoder()
    for key in ('edge_sidecar_to_children', 'carousel_media', 'shortcode_media'):
        for m in re.finditer(r'"%s"\s*:\s*' % key, text):
            try:
                obj, _ = dec.raw_decode(text, m.end())
                blobs.append({key: obj})
            except Exception:
                continue
    return blobs


def _ig_items_from_regex(text):
    """สำรองสุดท้าย: กวาด display_url / video_url ตามลำดับที่ปรากฏ (รองรับทั้งแบบปกติและแบบ escape)
    รูปกับวิดีโอในอัลบั้มเดียวกันจะไม่ทับกันอีก"""
    def scan(key):
        pat = r'\\*"%s\\*"\s*:\s*\\*"(.*?)\\*"' % key
        return [(m.start(), _ig_unescape(m.group(1))) for m in re.finditer(pat, text)]

    events = [(pos, 'img', u) for pos, u in scan('display_url')]
    events += [(pos, 'vid', u) for pos, u in scan('video_url')]
    events.sort(key=lambda e: e[0])

    seq = []
    for _, kind, u in events:
        if not u.startswith('http'):
            continue
        if kind == 'img':
            seq.append({'img': u, 'vid': None})
        elif seq and seq[-1]['vid'] is None:
            seq[-1]['vid'] = u
        else:
            seq.append({'img': None, 'vid': u})

    def key(u):
        return u.split('?')[0]

    poster_keys = {key(s['img']) for s in seq if s['vid'] and s['img']}
    items, seen = [], set()
    for s in seq:
        k = key(s['vid'] or s['img'])
        if k in seen:
            continue
        if not s['vid'] and key(s['img']) in poster_keys:
            continue  # เป็นแค่ภาพปกของวิดีโอ ไม่ใช่รูปแยก
        seen.add(k)
        if s['vid']:
            items.append({
                'type': 'video', 'platform': 'Instagram',
                'preview': s['img'] or s['vid'], 'duration': None,
                'options': [{'label': 'HD Video', 'url': s['vid']}],
            })
        elif not is_profile_image(s['img']):
            items.append({
                'type': 'photo', 'platform': 'Instagram',
                'preview': s['img'],
                'options': [{'label': 'HD Photo', 'url': s['img']}],
            })
    return items


def _ig_parse_embed(text):
    """คืน (items, is_carousel) จากหน้า embed หนึ่งหน้า"""
    is_carousel = bool(IG_CAROUSEL_RE.search(text))

    best = []
    for blob in _ig_json_blobs(text):
        cur = _ig_items_from_json(blob)
        if len(cur) > len(best):
            best = cur
        if len(best) > 1:
            break

    if len(best) < 2:
        rx = _ig_items_from_regex(text)
        if len(rx) > len(best):
            best = rx
    return best, is_carousel


def _ig_from_mirror(shortcode, headers):
    """สำรองผ่าน Public Mirror API กรณี Embed โดนบล็อก IP (โครงสร้าง JSON เป็นการคาดเดา)"""
    items = []
    try:
        api_res = requests.get(f"https://api.ddinstagram.com/post/{shortcode}", headers=headers, timeout=6)
        if api_res.status_code != 200:
            return []
        data = api_res.json()
        media_list = data.get('item', {}).get('media_list', []) or data.get('media', [])
        if not media_list and data.get('post'):
            media_list = [data.get('post')]

        for m in media_list:
            m_type = m.get('type')
            if m_type == 'video' or m.get('video_url'):
                items.append({
                    'type': 'video',
                    'platform': 'Instagram',
                    'preview': m.get('thumbnail_url') or m.get('url'),
                    'duration': format_sec(m.get('duration')),
                    'options': [{'label': 'HD Video', 'url': m.get('video_url') or m.get('url')}]
                })
            else:
                img = m.get('url') or m.get('image_url')
                if img and not is_profile_image(img):
                    items.append({
                        'type': 'photo',
                        'platform': 'Instagram',
                        'preview': img,
                        'options': [{'label': 'HD Photo', 'url': img}]
                    })
    except Exception:
        return []
    return items


def extract_ig_media(final_url, raw_url=None):
    """คืน (items, incomplete)
    incomplete=True หมายถึงโพสต์เป็นอัลบั้ม แต่ดึงได้ไม่ครบ (น้อยกว่า 2 ชิ้น) ให้ผู้เรียกลองแหล่งอื่นต่อ"""
    shortcode = get_ig_shortcode(raw_url, final_url)
    if not shortcode:
        return [], False

    headers = {
        'User-Agent': MOBILE_UA,
        'Accept-Language': 'en-US,en;q=0.9',
    }

    best = []
    is_carousel = False

    def consider(items):
        nonlocal best
        if items and len(items) > len(best):
            best = items

    # วิธีที่ 1: แกะจาก Instagram Embed Page (ลองทั้งสองหน้าจนกว่าจะได้ข้อมูล)
    embed_urls = [
        f"https://www.instagram.com/p/{shortcode}/embed/captioned/",
        f"https://www.instagram.com/p/{shortcode}/embed/",
    ]
    for e_url in embed_urls:
        try:
            r = requests.get(e_url, headers=headers, timeout=7)
        except Exception:
            continue
        if r.status_code != 200 or len(r.text) <= 500:
            continue

        items, car = _ig_parse_embed(r.text)
        is_carousel = is_carousel or car
        consider(items)

        if len(best) > 1:
            return best, False          # ได้อัลบั้มครบแล้ว
        if best and not is_carousel:
            return best, False          # โพสต์เดี่ยว ได้ครบแล้ว

    # วิธีที่ 2: ยังไม่ได้อะไร หรือเป็นอัลบั้มแต่ได้ไม่ครบ -> ลอง mirror API
    if not best or is_carousel:
        consider(_ig_from_mirror(shortcode, headers))
        if len(best) > 1:
            return best, False

    return best, (is_carousel and len(best) < 2)


def extract_ytdlp_media(final_url, platform_name):
    """Fallback ด้วย yt-dlp (ย้ายออกมาจาก get_media เพื่อเรียกใช้ซ้ำได้)"""
    items = []
    if not HAS_YTDLP:
        return items
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'socket_timeout': 10,
            'user_agent': BROWSER_UA
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(final_url, download=False)
            entries = info.get('entries') or [info]

            for entry in entries:
                if not entry:
                    continue
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

                video_opts.sort(key=lambda x: int(x['label'].replace('p', '')) if 'p' in x['label'] else 0, reverse=True)

                if video_opts and entry.get('vcodec') != 'none':
                    items.append({'type': 'video', 'platform': platform_name, 'preview': preview, 'duration': duration_str, 'options': video_opts})
                else:
                    img_url = entry.get('url')
                    if not img_url or img_url.endswith('.mp4'):
                        thumbs = entry.get('thumbnails', [])
                        if thumbs:
                            img_url = thumbs[-1].get('url')
                        else:
                            img_url = preview
                    if img_url and not is_profile_image(img_url):
                        items.append({'type': 'photo', 'platform': platform_name, 'preview': img_url, 'options': [{'label': 'HD Photo', 'url': img_url}]})
    except Exception:
        pass
    return items


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
    try:
        raw_url = request.json.get('url', '').strip() if request.json else ''
        if not raw_url:
            return jsonify({'error': 'กรุณาใส่ลิงก์'}), 400

        final_url, page_html = resolve_url(raw_url)
        platform_name = detect_platform(final_url)

        items = []  # ผลลัพธ์ที่ดีที่สุดที่ได้จนถึงตอนนี้ (เผื่อ IG ได้ไม่ครบ)

        # 1. ลองดึงข้อมูลตามแพลตฟอร์ม
        if platform_name == '𝕏':
            x_items = extract_x_media(final_url)
            if x_items: return jsonify({'items': x_items})

        elif platform_name == 'Instagram':
            ig_items, incomplete = extract_ig_media(final_url, raw_url)
            if ig_items and not incomplete: return jsonify({'items': ig_items})
            items = ig_items  # อาจได้ไม่ครบ เก็บไว้เทียบกับ yt-dlp

        else:
            # 2. ไม่รู้แพลตฟอร์ม ให้ลองทั้งสองตัว
            ig_items, incomplete = extract_ig_media(final_url, raw_url)
            if ig_items and not incomplete: return jsonify({'items': ig_items})
            items = ig_items

            x_items = extract_x_media(final_url)
            if x_items: return jsonify({'items': x_items})

        # 3. Fallback สุดท้ายด้วย yt-dlp (ใช้ผลนี้ถ้าได้มากกว่าที่มีอยู่)
        yt_items = extract_ytdlp_media(final_url, platform_name)
        if len(yt_items) > len(items):
            items = yt_items

        if items:
            return jsonify({'items': items})

        return jsonify({'error': 'ไม่พบสื่อในลิงก์นี้ หรือโพสต์อาจเป็นบัญชีส่วนตัว (Private)'}), 400

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
            headers={'Content-Disposition': f'attachment; filename="media_download.{ext}"'}
        )
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
          
