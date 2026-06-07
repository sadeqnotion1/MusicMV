import os
import re
import socket
import sys
import time
import json
import threading
import webbrowser
from datetime import datetime
from flask import Flask, jsonify, request, render_template

import requests
import billboard

app = Flask(__name__, template_folder='templates', static_folder='static')

# Publicly available Tidal Web Client Token
TIDAL_TOKEN = "CzET4vdadNUFQ5JU"
DEFAULT_COUNTRY = "US"

# YT matches history cache file path
YT_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yt_cache.json')
yt_cache_lock = threading.Lock()

def load_yt_cache():
    if not os.path.exists(YT_CACHE_FILE):
        return {}
    try:
        with yt_cache_lock:
            with open(YT_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading YT cache: {e}")
        return {}

def save_yt_cache(cache):
    try:
        with yt_cache_lock:
            with open(YT_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving YT cache: {e}")

def normalize_query(query):
    if not query:
        return ""
    q = query.lower().strip()
    # Keep only alphanumeric characters and spaces, convert to underscores
    q = re.sub(r'[^a-z0-9]', '_', q)
    q = re.sub(r'_+', '_', q)
    return q.strip('_')

def get_from_yt_cache(tidal_id=None, query=None):
    cache = load_yt_cache()
    if tidal_id and not str(tidal_id).startswith('pl_') and not str(tidal_id).startswith('bb_'):
        if str(tidal_id) in cache:
            return cache[str(tidal_id)]
    if query:
        norm = normalize_query(query)
        if norm and norm in cache:
            return cache[norm]
    return None

def update_yt_cache(tidal_id, query, video_id, video_url):
    cache = load_yt_cache()
    entry = {
        'videoId': video_id,
        'videoUrl': video_url,
        'matched_at': datetime.now().isoformat()
    }
    if tidal_id and not str(tidal_id).startswith('pl_') and not str(tidal_id).startswith('bb_'):
        cache[str(tidal_id)] = entry
    if query:
        norm = normalize_query(query)
        if norm:
            cache[norm] = entry
    save_yt_cache(cache)

# Active downloads registry for real-time progress monitoring
active_downloads = {}
downloads_lock = threading.Lock()

def update_download_progress(task_id, data):
    with downloads_lock:
        if task_id not in active_downloads:
            return
            
        dl_info = active_downloads[task_id]
        
        if data.get('status') == 'downloading':
            downloaded = data.get('downloaded_bytes', 0)
            total = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
            if total > 0:
                dl_info['progress'] = int(downloaded / total * 100)
            else:
                dl_info['progress'] = 0
                
            speed = data.get('speed')
            if speed:
                if speed > 1024 * 1024:
                    dl_info['speed'] = f"{speed / (1024*1024):.1f} MB/s"
                else:
                    dl_info['speed'] = f"{speed / 1024:.0f} KB/s"
            else:
                dl_info['speed'] = '---'
                
            eta = data.get('eta')
            if eta:
                mins = eta // 60
                secs = eta % 60
                dl_info['eta'] = f"{mins}:{secs:02d}"
            else:
                dl_info['eta'] = '---'
                
            dl_info['status'] = 'downloading'
            
        elif data.get('status') == 'finished':
            dl_info['progress'] = 100
            dl_info['status'] = 'completed'
            dl_info['speed'] = ''
            dl_info['eta'] = ''
            dl_info['filename'] = data.get('filename', '')

def find_free_port():
    """Find an available port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def format_duration(seconds):
    """Format duration in seconds to MM:SS."""
    if not seconds:
        return "0:00"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

def format_release_date(date_str):
    """Format ISO date string to a human-readable format (Month Day, Year)."""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except Exception:
        return date_str[:10]

def extract_artist_id(input_str, country_code=DEFAULT_COUNTRY):
    """Extract numeric artist ID from artist ID, artist URL, or video URL."""
    input_str = input_str.strip()
    
    if input_str.isdigit():
        return input_str
        
    match_artist = re.search(r'/artist/(\d+)', input_str)
    if match_artist:
        return match_artist.group(1)
        
    match_video = re.search(r'/video/(\d+)', input_str)
    if match_video:
        video_id = match_video.group(1)
        url = f"https://api.tidal.com/v1/videos/{video_id}"
        params = {'countryCode': country_code}
        headers = {
            'x-tidal-token': TIDAL_TOKEN,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                artist = data.get('artist', {})
                if artist.get('id'):
                    return str(artist.get('id'))
        except Exception as e:
            print(f"Error resolving artist from video URL: {e}")
            
    return None

def search_artists(query, country_code=DEFAULT_COUNTRY):
    """Search for artists on Tidal by query string."""
    url = "https://api.tidal.com/v1/search"
    params = {
        'query': query,
        'limit': 5,
        'types': 'ARTISTS',
        'countryCode': country_code
    }
    headers = {
        'x-tidal-token': TIDAL_TOKEN,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('artists', {}).get('items', [])
            results = []
            for item in items:
                pic_id = item.get('picture')
                pic_url = ""
                if pic_id:
                    pic_url = f"https://resources.tidal.com/images/{pic_id.replace('-', '/')}/320x320.jpg"
                results.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'picture': pic_url,
                    'popularity': item.get('popularity', 0)
                })
            return results
    except Exception as e:
        print(f"Artist search error: {e}")
    return []

def fetch_artist_data(artist_id, country_code=DEFAULT_COUNTRY):
    """Fetch artist details and videos from Tidal API."""
    headers = {
        'x-tidal-token': TIDAL_TOKEN,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    params = {'countryCode': country_code}
    
    artist_name = "Unknown Artist"
    artist_pic = ""
    try:
        artist_url = f"https://api.tidal.com/v1/artists/{artist_id}"
        response = requests.get(artist_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            artist_name = data.get('name', 'Unknown Artist')
            pic_id = data.get('picture')
            if pic_id:
                artist_pic = f"https://resources.tidal.com/images/{pic_id.replace('-', '/')}/320x320.jpg"
    except Exception as e:
        print(f"Artist details fetch error: {e}")
        
    videos = []
    try:
        videos_url = f"https://api.tidal.com/v1/artists/{artist_id}/videos"
        v_params = {**params, 'limit': 100}
        response = requests.get(videos_url, params=v_params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            videos = data.get('items', [])
    except Exception as e:
        print(f"Artist videos fetch error: {e}")
        
    return artist_name, artist_pic, videos

def process_and_filter_videos(videos):
    excluded_terms = ["lyric video", "lyric vid", "visualizer", "behind the scenes"]
    
    priority_map = {
        "official video": "Official Video",
        "live from": "Live Session",
        "acoustic": "Acoustic",
        "live session": "Live Session"
    }
    
    priority_list = []
    standard_list = []
    excluded_list = []
    
    for item in videos:
        title = item.get('title', '')
        title_lower = title.lower()
        
        excluded_by = None
        for term in excluded_terms:
            if term in title_lower:
                excluded_by = term
                break
                
        duration_sec = item.get('duration', 0)
        duration_str = format_duration(duration_sec)
        release_date_str = format_release_date(item.get('releaseDate', ''))
        
        image_id = item.get('imageId')
        thumbnail_url = ""
        if image_id:
            thumbnail_url = f"https://resources.tidal.com/images/{image_id.replace('-', '/')}/640x360.jpg"
            
        collaborators = [art.get('name') for art in item.get('artists', []) if art.get('name')]
        
        quality_raw = item.get('quality', '')
        quality_str = "HD"
        if "1080" in quality_raw:
            quality_str = "1080p Full HD"
        elif "720" in quality_raw:
            quality_str = "720p HD"
        elif "2160" in quality_raw or "4K" in quality_raw:
            quality_str = "4K Ultra HD"
            
        video_data = {
            'id': item.get('id'),
            'title': title,
            'thumbnail': thumbnail_url,
            'duration': duration_str,
            'releaseDate': release_date_str,
            'quality': quality_str,
            'explicit': item.get('explicit', False),
            'popularity': item.get('popularity', 0),
            'artists': collaborators,
            'url': f"https://tidal.com/video/{item.get('id')}"
        }
        
        if excluded_by:
            video_data['category'] = "Excluded"
            video_data['exclusion_reason'] = f"Contains '{excluded_by}'"
            excluded_list.append(video_data)
        else:
            matched_priority = None
            for term, category_name in priority_map.items():
                if term in title_lower:
                    matched_priority = category_name
                    break
                    
            if matched_priority:
                video_data['category'] = matched_priority
                priority_list.append(video_data)
            else:
                video_data['category'] = "Standard"
                standard_list.append(video_data)
                
    return {
        'priority': priority_list,
        'standard': standard_list,
        'excluded': excluded_list
    }

# Popular chart presets (Name -> Slug)
CHART_PRESETS = {
    "Hot 100 (Singles)": "hot-100",
    "Billboard 200 (Albums)": "billboard-200",
    "Artist 100": "artist-100",
    "Pop Airplay": "pop-songs",
    "Hot Country Songs": "hot-country-songs",
    "Traditional Jazz Albums": "traditional-jazz-albums",
    "Streaming Songs": "streaming-songs",
    "R&B/Hip-Hop Songs": "r-and-b-hip-hop-songs",
    "Hot Rock Songs": "hot-rock-songs",
    "Alternative Airplay": "alternative-songs",
    "Hot Latin Songs": "hot-latin-songs",
    "Dance/Electronic Songs": "dance-electronic-songs"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    req_data = request.json or {}
    artist_input = req_data.get('input', '').strip()
    country_code = req_data.get('countryCode', DEFAULT_COUNTRY).strip().upper()
    
    if not artist_input:
        return jsonify({'status': 'error', 'message': 'Input cannot be empty'}), 400
        
    artist_id = extract_artist_id(artist_input, country_code)
    
    if not artist_id:
        artists = search_artists(artist_input, country_code)
        if not artists:
            return jsonify({
                'status': 'error', 
                'message': f"Could not find artist with input '{artist_input}'. Please check the name, URL, or ID."
            }), 404
        return jsonify({
            'status': 'search_results',
            'data': artists
        })
        
    try:
        name, pic, videos = fetch_artist_data(artist_id, country_code)
        
        if not videos and name == "Unknown Artist":
            return jsonify({
                'status': 'error',
                'message': f"No artist or video data found for ID '{artist_id}'."
            }), 404
            
        classified = process_and_filter_videos(videos)
        
        try:
            for cat in ['priority', 'standard', 'excluded']:
                for video in classified[cat]:
                    t_id = str(video['id'])
                    artists_str = ", ".join(video.get('artists', [])) if video.get('artists') else name
                    v_query = f"{artists_str} - {video['title']}"
                    cached_entry = get_from_yt_cache(t_id, v_query)
                    if cached_entry:
                        video['youtubeId'] = cached_entry['videoId']
                        video['youtubeUrl'] = cached_entry['videoUrl']
        except Exception as e:
            print(f"Error injecting YT cache: {e}")
        
        return jsonify({
            'status': 'success',
            'data': {
                'artist': {
                    'id': artist_id,
                    'name': name,
                    'picture': pic
                },
                'videos': classified,
                'stats': {
                    'total': len(videos),
                    'priority': len(classified['priority']),
                    'standard': len(classified['standard']),
                    'excluded': len(classified['excluded'])
                }
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/playlist/match', methods=['POST'])
def api_playlist_match():
    req_data = request.json or {}
    playlist_text = req_data.get('playlist', '').strip()
    country_code = req_data.get('countryCode', DEFAULT_COUNTRY).strip().upper()
    
    if not playlist_text:
        return jsonify({'status': 'error', 'message': 'Playlist cannot be empty'}), 400
        
    lines = [line.strip() for line in playlist_text.split('\n') if line.strip()]
    
    headers = {
        'x-tidal-token': TIDAL_TOKEN,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    import urllib.parse
    from concurrent.futures import ThreadPoolExecutor
    
    def process_playlist_line(idx, line):
        parts = line.split('-', 1)
        if len(parts) == 2:
            artist_part = parts[0].strip()
            song_part = parts[1].strip()
        else:
            artist_part = ""
            song_part = line.strip()
            
        query = line
        url = f"https://api.tidal.com/v1/search?query={urllib.parse.quote(query)}&limit=5&types=VIDEOS&countryCode={country_code}"
        
        video_data = None
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                search_data = response.json()
                items = search_data.get('videos', {}).get('items', [])
                if items:
                    item = items[0]
                    duration_sec = item.get('duration', 0)
                    duration_str = format_duration(duration_sec)
                    release_date_str = format_release_date(item.get('releaseDate', ''))
                    
                    image_id = item.get('imageId')
                    thumbnail_url = ""
                    if image_id:
                        thumbnail_url = f"https://resources.tidal.com/images/{image_id.replace('-', '/')}/640x360.jpg"
                        
                    collaborators = [art.get('name') for art in item.get('artists', []) if art.get('name')]
                    
                    quality_raw = item.get('quality', '')
                    quality_str = "HD"
                    if "1080" in quality_raw:
                        quality_str = "1080p Full HD"
                    elif "720" in quality_raw:
                        quality_str = "720p HD"
                    elif "2160" in quality_raw or "4K" in quality_raw:
                        quality_str = "4K Ultra HD"
                        
                    video_data = {
                        'id': item.get('id'),
                        'title': item.get('title', ''),
                        'thumbnail': thumbnail_url,
                        'duration': duration_str,
                        'releaseDate': release_date_str,
                        'quality': quality_str,
                        'explicit': item.get('explicit', False),
                        'popularity': item.get('popularity', 0),
                        'artists': collaborators,
                        'url': f"https://tidal.com/video/{item.get('id')}",
                        'category': 'Priority'
                    }
        except Exception as e:
            print(f"Error matching playlist line '{line}' on Tidal: {e}")
            
        if not video_data:
            video_data = {
                'id': f"pl_{idx}",
                'title': song_part,
                'thumbnail': '',
                'duration': '0:00',
                'releaseDate': 'Unknown',
                'quality': 'HD',
                'explicit': False,
                'popularity': 0,
                'artists': [artist_part] if artist_part else [],
                'url': 'https://youtube.com',
                'category': 'Priority'
            }
            
        t_id = str(video_data['id'])
        artists_str = ", ".join(video_data['artists']) if video_data['artists'] else ""
        v_query = f"{artists_str} - {video_data['title']}" if artists_str else video_data['title']
        cached_entry = get_from_yt_cache(t_id, v_query)
        if cached_entry:
            video_data['youtubeId'] = cached_entry['videoId']
            video_data['youtubeUrl'] = cached_entry['videoUrl']
            
        return video_data

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_playlist_line, idx, line) for idx, line in enumerate(lines)]
        matched_videos = [f.result() for f in futures]
        
    return jsonify({
        'status': 'success',
        'data': {
            'artist': {
                'id': 'playlist',
                'name': 'Custom Song Playlist',
                'picture': ''
            },
            'videos': {
                'priority': matched_videos,
                'standard': [],
                'excluded': []
            },
            'stats': {
                'total': len(matched_videos),
                'priority': len(matched_videos),
                'standard': 0,
                'excluded': 0
            }
        }
    })

@app.route('/api/export', methods=['POST'])
def api_export():
    req_data = request.json or {}
    artist_name = req_data.get('artistName', 'unknown_artist').strip()
    videos = req_data.get('videos', {})
    
    text_content = f"TIDAL MUSIC VIDEOS - {artist_name.upper()}\n"
    text_content += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text_content += f"======================================================================\n\n"
    
    categories = ['priority', 'standard', 'excluded']
    titles = {
        'priority': 'PRIORITY MUSIC VIDEOS (OFFICIAL / LIVE / ACOUSTIC)',
        'standard': 'STANDARD MUSIC VIDEOS',
        'excluded': 'FILTERED OUT VIDEOS (LYRIC VIDEOS / VISUALIZERS / BEHIND THE SCENES)'
    }
    
    total_exported = 0
    for cat in categories:
        cat_list = videos.get(cat, [])
        if cat_list:
            text_content += f"======================================================================\n"
            text_content += f"{titles[cat]} ({len(cat_list)} items)\n"
            text_content += f"======================================================================\n\n"
            
            for idx, video in enumerate(cat_list):
                artists_list = ", ".join(video.get('artists', [])) if video.get('artists') else artist_name
                text_content += f"{idx + 1}. {video.get('title')}\n"
                text_content += f"   Artist(s): {artists_list}\n"
                text_content += f"   Duration: {video.get('duration')} | Quality: {video.get('quality')}\n"
                text_content += f"   Released: {video.get('releaseDate')}\n"
                if cat == 'excluded':
                    text_content += f"   Filter Reason: {video.get('exclusion_reason')}\n"
                else:
                    text_content += f"   URL: {video.get('url')}\n"
                text_content += f"\n"
            total_exported += len(cat_list)
            
    if total_exported == 0:
        return jsonify({'status': 'error', 'message': 'No video data to export'}), 400
        
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', artist_name).lower()
    filename = f"{safe_name}_tidal_videos.txt"
    filepath = os.path.join(exports_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        return jsonify({
            'status': 'success',
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Could not write file: {str(e)}"}), 500

@app.route('/api/youtube/search', methods=['POST'])
def api_youtube_search():
    import urllib.parse
    req_data = request.json or {}
    query = req_data.get('query', '').strip()
    tidal_id = req_data.get('tidalId', '').strip()
    
    if not query:
        return jsonify({'status': 'error', 'message': 'Query cannot be empty'}), 400
        
    cached_entry = get_from_yt_cache(tidal_id, query)
    if cached_entry:
        return jsonify({
            'status': 'success',
            'videoId': cached_entry['videoId'],
            'videoUrl': cached_entry['videoUrl'],
            'cached': True
        })
            
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            match = re.search(r'/watch\?v=([a-zA-Z0-9_-]{11})', response.text)
            if not match:
                match = re.search(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', response.text)
                
            if match:
                video_id = match.group(1)
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                try:
                    update_yt_cache(tidal_id, query, video_id, video_url)
                except Exception as e:
                    print(f"Error saving to cache: {e}")
                        
                return jsonify({
                    'status': 'success',
                    'videoId': video_id,
                    'videoUrl': video_url
                })
        return jsonify({'status': 'error', 'message': 'Could not find any videos on YouTube'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/youtube/download', methods=['POST'])
def api_youtube_download():
    req_data = request.json or {}
    video_id = req_data.get('videoId', '').strip()
    video_title = req_data.get('title', 'video').strip()
    quality = req_data.get('quality', 'best').strip().lower()
    
    if not video_id:
        return jsonify({'status': 'error', 'message': 'Video ID cannot be empty'}), 400
        
    import uuid
    task_id = f"yt_dl_{video_id}_{uuid.uuid4().hex[:6]}"
    
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', video_title)
    
    import shutil
    ffmpeg_available = shutil.which('ffmpeg') is not None

    if ffmpeg_available:
        formats = {
            'best': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            '1080p': 'bestvideo[vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best',
            '720p': 'bestvideo[vcodec^=avc1][height<=720]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best',
            '480p': 'bestvideo[vcodec^=avc1][height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best',
            'audio': 'bestaudio[ext=m4a]/bestaudio/best'
        }
    else:
        formats = {
            'best': 'best',
            '1080p': 'best[height<=1080]/best',
            '720p': 'best[height<=720]/best',
            '480p': 'best[height<=480]/best',
            'audio': 'bestaudio/best'
        }
    
    quality_format = formats.get(quality, formats['best'])
    
    if quality == 'audio':
        output_template = os.path.join(exports_dir, f"{safe_title}.%(ext)s")
    else:
        output_template = os.path.join(exports_dir, f"{safe_title}_{quality}.%(ext)s")
        
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with downloads_lock:
        active_downloads[task_id] = {
            'id': task_id,
            'title': video_title,
            'progress': 0,
            'status': 'queued',
            'speed': '---',
            'eta': '---',
            'filename': '',
            'error': '',
            'type': 'audio' if quality == 'audio' else 'video',
            'quality': 'Audio' if quality == 'audio' else quality.upper()
        }
        if not ffmpeg_available and quality != 'audio':
            active_downloads[task_id]['error'] = 'FFmpeg not found. Downloading pre-merged video (max 720p).'
        
    def run_ytdlp_download():
        import yt_dlp
        
        def ytdlp_hook(d):
            update_download_progress(task_id, d)
            
        ydl_opts = {
            'format': quality_format,
            'outtmpl': output_template,
            'progress_hooks': [ytdlp_hook],
            'quiet': True,
            'no_warnings': True
        }
        
        if ffmpeg_available and quality != 'audio':
            ydl_opts['merge_output_format'] = 'mp4'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(video_url, download=False)
                    with downloads_lock:
                        if task_id in active_downloads:
                            active_downloads[task_id]['title'] = info.get('title', active_downloads[task_id]['title'])
                except Exception:
                    pass
                
                ydl.download([video_url])
                
                with downloads_lock:
                    if task_id in active_downloads:
                        active_downloads[task_id]['status'] = 'completed'
                        active_downloads[task_id]['progress'] = 100
        except Exception as e:
            print(f"yt-dlp thread error: {e}")
            with downloads_lock:
                if task_id in active_downloads:
                    active_downloads[task_id]['status'] = 'failed'
                    active_downloads[task_id]['error'] = str(e)
                    
    threading.Thread(target=run_ytdlp_download, daemon=True).start()
    
    return jsonify({
        'status': 'success',
        'taskId': task_id,
        'message': 'Download started successfully.'
    })

@app.route('/api/downloads/status', methods=['GET'])
def api_downloads_status():
    with downloads_lock:
        return jsonify(list(active_downloads.values()))

@app.route('/api/downloads/clear', methods=['POST'])
def api_downloads_clear():
    global active_downloads
    with downloads_lock:
        active_downloads = {
            tid: info for tid, info in active_downloads.items() 
            if info['status'] in ['queued', 'downloading']
        }
    return jsonify({'status': 'success'})

@app.route('/api/downloads/open_folder', methods=['POST'])
def api_downloads_open_folder():
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    try:
        os.startfile(exports_dir)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('query', '').strip()
    country_code = request.args.get('countryCode', DEFAULT_COUNTRY).strip().upper()
    if not query:
        return jsonify([])
    artists = search_artists(query, country_code)
    return jsonify(artists)


# ======================================================================
# BILLBOARD CHARTS INTEGRATION ENDPOINTS
# ======================================================================

@app.route('/api/billboard/presets', methods=['GET'])
def api_billboard_presets():
    return jsonify(CHART_PRESETS)

@app.route('/api/billboard/chart', methods=['POST'])
def api_billboard_chart():
    req_data = request.json or {}
    chart_name = req_data.get('chart', 'hot-100').strip()
    date_val = req_data.get('date', '').strip()
    year_val = req_data.get('year', '').strip()
    
    if not date_val:
        date_val = None
    if not year_val:
        year_val = None
        
    try:
        if date_val and year_val:
            return jsonify({'status': 'error', 'message': 'Cannot query by both date and year'}), 400
            
        chart = billboard.ChartData(chart_name, date=date_val, year=year_val)
        
        entries_list = []
        for entry in chart.entries:
            query_str = f"{entry.artist} - {entry.title}"
            
            # YearEndChartEntry doesn't have peakPos, lastPos, weeks, or isNew attributes
            peak_pos = getattr(entry, 'peakPos', None)
            last_pos = getattr(entry, 'lastPos', None)
            weeks_on_chart = getattr(entry, 'weeks', None)
            is_new = getattr(entry, 'isNew', False)
            
            entry_data = {
                'rank': entry.rank,
                'title': entry.title,
                'artist': entry.artist,
                'image': entry.image or "",
                'peakPos': peak_pos if peak_pos is not None else 0,
                'lastPos': last_pos if last_pos is not None else 0,
                'weeks': weeks_on_chart if weeks_on_chart is not None else 0,
                'isNew': is_new
            }
            
            # Check YT cache by query string
            cached_entry = get_from_yt_cache(None, query_str)
            if cached_entry:
                entry_data['youtubeId'] = cached_entry['videoId']
                entry_data['youtubeUrl'] = cached_entry['videoUrl']
                
            entries_list.append(entry_data)
            
        return jsonify({
            'status': 'success',
            'data': {
                'title': chart.title or chart_name,
                'date': chart.date or year_val or "Current",
                'entries': entries_list
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/billboard/artist', methods=['POST'])
def api_billboard_artist():
    req_data = request.json or {}
    artist_name = req_data.get('artist', '').strip()
    
    if not artist_name:
        return jsonify({'status': 'error', 'message': 'Artist name cannot be empty'}), 400
        
    try:
        history = billboard.get_artist_history(artist_name)
        
        entries_list = []
        for entry in history.entries:
            query_str = f"{entry.artist} - {entry.title}"
            entry_data = {
                'title': entry.title,
                'artist': entry.artist,
                'debutDate': entry.debut_date,
                'peakPos': entry.peak_pos,
                'peakWeeks': entry.peak_weeks,
                'peakDate': entry.peak_date,
                'weeksOnChart': entry.weeks_on_chart
            }
            
            cached_entry = get_from_yt_cache(None, query_str)
            if cached_entry:
                entry_data['youtubeId'] = cached_entry['videoId']
                entry_data['youtubeUrl'] = cached_entry['videoUrl']
                
            entries_list.append(entry_data)
            
        return jsonify({
            'status': 'success',
            'data': {
                'artist': history.artist_slug,
                'stats': history.stats,
                'entries': entries_list
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/billboard/export', methods=['POST'])
def api_billboard_export():
    req_data = request.json or {}
    chart_title = req_data.get('title', 'billboard_chart').strip()
    chart_date = req_data.get('date', 'current').strip()
    entries = req_data.get('entries', [])
    
    if not entries:
        return jsonify({'status': 'error', 'message': 'No entries to export'}), 400
        
    text_content = ""
    for entry in entries:
        text_content += f"{entry.get('artist')} - {entry.get('title')}\n"
        
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', chart_title).lower()
    filename = f"billboard_{safe_title}_{chart_date.replace('-', '_')}.txt"
    filepath = os.path.join(exports_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        return jsonify({
            'status': 'success',
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/billboard/export_artist', methods=['POST'])
def api_billboard_export_artist():
    req_data = request.json or {}
    artist_name = req_data.get('artist', 'artist').strip()
    stats = req_data.get('stats', {})
    entries = req_data.get('entries', [])
    
    if not entries:
        return jsonify({'status': 'error', 'message': 'No entries to export'}), 400
        
    text_content = ""
    for entry in entries:
        text_content += f"{entry.get('artist')} - {entry.get('title')}\n"
        
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', artist_name).lower()
    filename = f"billboard_history_{safe_name}.txt"
    filepath = os.path.join(exports_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        return jsonify({
            'status': 'success',
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def run_flask(port):
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    
    # Start Flask Server in background thread
    server_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    server_thread.start()
    
    time.sleep(0.5)
    
    try:
        import webview
        print(f"Launching GUI window pointing to {url}...")
        webview.create_window(
            title="TIDAL & Billboard Charts Media Intel Center",
            url=url,
            width=1280,
            height=850,
            min_size=(1000, 700),
            background_color="#fcfaf7"  # Match parchment background
        )
        webview.start()
    except Exception as e:
        print(f"\n[INFO] pywebview wrapper could not be initialized ({e}).")
        print(f"[STATUS] Falling back to default web browser.")
        print(f"[STATUS] Web application server is running at: {url}")
        print("Press Ctrl+C in this terminal to exit.\n")
        
        webbrowser.open(url)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down server...")
