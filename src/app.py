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
    excluded_terms = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]
    
    priority_map = {
        "official video": "Official Video",
        "official music video": "Official Video",
        "live from": "Live Session",
        "live at": "Live Session",
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
    return render_template('intel.html')

@app.route('/library')
def library():
    return render_template('library.html')

@app.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

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

def resolve_youtube_link(tidal_id, query):
    if tidal_id and str(tidal_id).startswith('local_'):
        tidal_id = None
        
    cached_entry = get_from_yt_cache(tidal_id, query)
    if cached_entry:
        return cached_entry['videoUrl']
        
    import yt_dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = result.get('entries', [])
            
        banned_keywords = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric"]
        priority_keywords = ["official video", "official music video", "live from", "live at", "acoustic", "live session"]
        
        priority_matches = []
        standard_matches = []
        
        for entry in entries:
            title = entry.get('title', '')
            if not title:
                continue
            title_lower = title.lower()
            
            is_banned = False
            for kw in banned_keywords:
                if kw in title_lower:
                    is_banned = True
                    break
            if is_banned:
                continue
                
            is_priority = False
            for kw in priority_keywords:
                if kw in title_lower:
                    is_priority = True
                    break
                    
            if is_priority:
                priority_matches.append(entry)
            else:
                standard_matches.append(entry)
                
        best_match = None
        if priority_matches:
            best_match = priority_matches[0]
        elif standard_matches:
            best_match = standard_matches[0]
            
        if best_match:
            video_id = best_match.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                update_yt_cache(tidal_id, query, video_id, video_url)
            except Exception as e:
                print(f"Error saving to cache: {e}")
            return video_url
            
        if entries:
            first_entry = entries[0]
            video_id = first_entry.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                update_yt_cache(tidal_id, query, video_id, video_url)
            except Exception as e:
                print(f"Error saving to cache: {e}")
            return video_url
    except Exception as e:
        print(f"Error resolving YouTube link: {e}")
    return None

@app.route('/api/youtube/export_all', methods=['POST'])
def api_youtube_export_all():
    req_data = request.json or {}
    artist_name = req_data.get('artistName', 'unknown_artist').strip()
    videos = req_data.get('videos', {})
    
    categories = list(videos.keys())
    all_videos_to_resolve = []
    
    for cat in categories:
        cat_list = videos.get(cat, [])
        for video in cat_list:
            all_videos_to_resolve.append((cat, video))
            
    if not all_videos_to_resolve:
        return jsonify({'status': 'error', 'message': 'No video data to export'}), 400
        
    from concurrent.futures import ThreadPoolExecutor
    
    def resolve_task(item):
        cat, video = item
        artists_list = ", ".join(video.get('artists', [])) if video.get('artists') else artist_name
        query = f"{artists_list} - {video.get('title')}"
        tidal_id = video.get('id')
        yt_url = resolve_youtube_link(tidal_id, query)
        return cat, video, yt_url

    resolved_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(resolve_task, all_videos_to_resolve)
        resolved_results = list(results)
        
    text_content = f"YOUTUBE LINKS FOR TIDAL VIDEOS - {artist_name.upper()}\n"
    text_content += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text_content += f"======================================================================\n\n"
    
    titles = {
        'priority': 'PRIORITY MUSIC VIDEOS (OFFICIAL / LIVE / ACOUSTIC)',
        'standard': 'STANDARD MUSIC VIDEOS',
        'excluded': 'FILTERED OUT VIDEOS (LYRIC VIDEOS / VISUALIZERS / BEHIND THE SCENES)',
        'existing': 'DOWNLOADED VIDEOS IN LIBRARY',
        'waiting': 'AVAILABLE VIDEOS TO DOWNLOAD',
    }
    
    total_exported = 0
    categorized_results = {cat: [] for cat in categories}
    for cat, video, yt_url in resolved_results:
        categorized_results[cat].append((video, yt_url))
        
    for cat in categories:
        cat_list = categorized_results[cat]
        if cat_list:
            cat_title = titles.get(cat, f"{cat.upper()} VIDEOS")
            text_content += f"======================================================================\n"
            text_content += f"{cat_title} ({len(cat_list)} items)\n"
            text_content += f"======================================================================\n\n"
            
            for idx, (video, yt_url) in enumerate(cat_list):
                artists_list = ", ".join(video.get('artists', [])) if video.get('artists') else artist_name
                text_content += f"{idx + 1}. {video.get('title')}\n"
                text_content += f"   Artist(s): {artists_list}\n"
                text_content += f"   Duration: {video.get('duration')} | Quality: {video.get('quality', '—')}\n"
                text_content += f"   Released: {video.get('releaseDate')}\n"
                if video.get('url'):
                    text_content += f"   Tidal URL: {video.get('url')}\n"
                if yt_url:
                    text_content += f"   YouTube URL: {yt_url}\n"
                else:
                    text_content += f"   YouTube URL: Not Found\n"
                if video.get('localFile'):
                    text_content += f"   Local File: {video.get('localFile')}\n"
                text_content += f"\n"
            total_exported += len(cat_list)
            
    if total_exported == 0:
        return jsonify({'status': 'error', 'message': 'No video data to export'}), 400
        
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    os.makedirs(exports_dir, exist_ok=True)
    
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', artist_name).lower()
    filename = f"{safe_name}_youtube_links.txt"
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
            
    import yt_dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = result.get('entries', [])
            
        banned_keywords = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric"]
        priority_keywords = ["official video", "official music video", "live from", "live at", "acoustic", "live session"]
        
        priority_matches = []
        standard_matches = []
        
        for entry in entries:
            title = entry.get('title', '')
            if not title:
                continue
            title_lower = title.lower()
            
            is_banned = False
            for kw in banned_keywords:
                if kw in title_lower:
                    is_banned = True
                    break
            if is_banned:
                continue
                
            is_priority = False
            for kw in priority_keywords:
                if kw in title_lower:
                    is_priority = True
                    break
                    
            if is_priority:
                priority_matches.append(entry)
            else:
                standard_matches.append(entry)
                
        best_match = None
        if priority_matches:
            best_match = priority_matches[0]
        elif standard_matches:
            best_match = standard_matches[0]
            
        if best_match:
            video_id = best_match.get('id')
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
            
        # Fallback if all matches were banned: return the first result
        if entries:
            first_entry = entries[0]
            video_id = first_entry.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return jsonify({
                'status': 'success',
                'videoId': video_id,
                'videoUrl': video_url,
                'warning': 'Matches filtered by keyword; returning first result as fallback.'
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
    download_dir = req_data.get('downloadDir', '').strip()
    
    if not video_id:
        return jsonify({'status': 'error', 'message': 'Video ID cannot be empty'}), 400
        
    import uuid
    task_id = f"yt_dl_{video_id}_{uuid.uuid4().hex[:6]}"
    
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        target_dir = download_dir
    else:
        exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        target_dir = exports_dir
    
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
        output_template = os.path.join(target_dir, f"{safe_title}.%(ext)s")
    else:
        output_template = os.path.join(target_dir, f"{safe_title}_{quality}.%(ext)s")
        
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
            query_str = f"{entry.artist} - {entry.title}" if entry.title else entry.artist
            
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
        title = entry.get('title') or ""
        artist = entry.get('artist') or ""
        text_content += f"{artist} - {title}\n"
        
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
        title = entry.get('title') or ""
        artist = entry.get('artist') or ""
        text_content += f"{artist} - {title}\n"
        
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


# ======================================================================
# LOCAL ARCHIVE MANAGER PIPELINE ENDPOINTS
# ======================================================================

# Add current directory to path so we can import manage_music_videos and core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import manage_music_videos
    import core
    HAS_LOCAL_MANAGER = True
except Exception as e:
    print(f"Warning: Local music video manager modules could not be imported: {e}")
    HAS_LOCAL_MANAGER = False

# Global state for archive pipeline execution
pipeline_running = False
pipeline_status_text = "Idle"
pipeline_logs = []
logs_lock = threading.Lock()
original_log_msg = None

def web_log_msg(msg, level="INFO", console_prefix="", console=True):
    if original_log_msg:
        original_log_msg(msg, level, console_prefix, console)
    
    clean_msg = re.sub(r'\x1b\[[0-9;]*m', '', msg)
    prefix = ""
    if level == "SUCCESS":
        prefix = "[SUCCESS] "
    elif level == "OK":
        prefix = "[OK] "
    elif level == "WARNING":
        prefix = "[WARNING] "
    elif level == "ERROR":
        prefix = "[ERROR] "
    elif level == "DEBUG":
        prefix = "[DEBUG] "
        
    with logs_lock:
        pipeline_logs.append({
            'time': datetime.now().strftime("%H:%M:%S"),
            'level': level,
            'message': f"{prefix}{clean_msg}"
        })
        if len(pipeline_logs) > 1000:
            pipeline_logs.pop(0)

# Hook the logger if imported successfully
if HAS_LOCAL_MANAGER:
    original_log_msg = manage_music_videos.log_msg
    manage_music_videos.log_msg = web_log_msg


def run_pipeline_worker(archive_path, commit, skip_icons, skip_deezer, force, history_days):
    global pipeline_running, pipeline_status_text
    pipeline_running = True
    
    # Initialize / clean log file
    try:
        with open(manage_music_videos.LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(f"=== MUSIC VIDEO MANAGER WEB RUN | TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Target Directory: {archive_path}\n")
            f.write("=" * 60 + "\n\n")
    except Exception:
        pass
        
    try:
        pipeline_status_text = "Sorting root files and shortcuts..."
        manage_music_videos.log_msg("MUSIC VIDEO MASTER PIPELINE RUN", "OK")
        manage_music_videos.log_msg(f"Active Folder: {archive_path}", "INFO")
        manage_music_videos.log_msg("-" * 60, "INFO")
        
        # STEP 1: Sorting and guest shortcuts
        manage_music_videos.log_msg("STEP 1: SORTING ROOT VIDEOS & RECONCILING SHORTCUTS...", "OK")
        manage_music_videos.execute_sorting(archive_path, commit=commit)
        
        # STEP 2: Catalogs
        pipeline_status_text = "Generating catalog sheets..."
        manage_music_videos.log_msg("STEP 2: GENERATING MUSIC VIDEO CATALOG SHEETS...", "OK")
        manage_music_videos.execute_catalog_generation(
            archive_path, 
            skip_deezer=skip_deezer,
            history_days=history_days,
            force=force
        )
        
        # STEP 3: Avatars and folder icons
        if not skip_icons:
            pipeline_status_text = "Downloading avatars and applying folder icons..."
            manage_music_videos.log_msg("STEP 3: BATCH DOWNLOADING AVATARS & SETTING ICONS...", "OK")
            manage_music_videos.execute_artist_face_download(
                archive_path, 
                overwrite=force, 
                apply_icons=True, 
                image_size="xl"
            )
            
        # STEP 4: Shell notify refresh
        if manage_music_videos.HAS_CORE:
            manage_music_videos.log_msg("Refreshing Windows Explorer shell to update icons...", "INFO")
            manage_music_videos.core.refresh_explorer()
            
        manage_music_videos.log_msg("-" * 60, "INFO")
        manage_music_videos.log_msg("Pipeline operations completed successfully!", "SUCCESS")
        pipeline_status_text = "Completed"
    except Exception as e:
        manage_music_videos.log_msg(f"Pipeline crashed with an error: {e}", "ERROR")
        pipeline_status_text = "Failed"
    finally:
        pipeline_running = False


# Global settings for the archive pipeline
PIPELINE_PATH = r"G:\Music\Music Video"
SYNC_DEEZER_AVATARS = True
GENERATE_CATALOGS = True
RECONCILE_SHORTCUTS = False

@app.route('/api/archive/status', methods=['GET', 'POST'])
def api_archive_status():
    global PIPELINE_PATH, TIDAL_TOKEN, SYNC_DEEZER_AVATARS, GENERATE_CATALOGS, RECONCILE_SHORTCUTS
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
    
    if request.method == 'POST':
        req_data = request.json or {}
        if 'path' in req_data:
            PIPELINE_PATH = req_data['path'].strip()
        if 'tidalToken' in req_data:
            TIDAL_TOKEN = req_data['tidalToken'].strip()
        if 'syncDeezerAvatars' in req_data:
            SYNC_DEEZER_AVATARS = bool(req_data['syncDeezerAvatars'])
        if 'generateCatalogs' in req_data:
            GENERATE_CATALOGS = bool(req_data['generateCatalogs'])
        if 'reconcileShortcuts' in req_data:
            RECONCILE_SHORTCUTS = bool(req_data['reconcileShortcuts'])
        return jsonify({'status': 'success', 'message': 'Configuration updated.'})
    
    # GET method
    archive_path = request.args.get('path', '').strip()
    if not archive_path:
        archive_path = PIPELINE_PATH
        if not os.path.exists(archive_path):
            archive_path = r"G:\Music\Music Video"
            if not os.path.exists(archive_path):
                archive_path = os.getcwd()
            
    total_artists = 0
    total_videos = 0
    total_shortcuts = 0
    cached_count = 0
    
    excluded_terms = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]
    
    if os.path.exists(archive_path) and os.path.isdir(archive_path):
        try:
            artists = manage_music_videos.get_existing_dirs(archive_path)
            excluded_names = ('__pycache__', 'node_modules', 'venv', '.git', 'env', '.idea', '.vscode', '.antigravitycli')
            artists = [a for a in artists if a.lower() not in excluded_names]
            total_artists = len(artists)
            
            for artist in artists:
                artist_path = os.path.join(archive_path, artist)
                try:
                    for item in os.listdir(artist_path):
                        item_lower = item.lower()
                        if any(term in item_lower for term in excluded_terms):
                            continue
                        ext = os.path.splitext(item_lower)[1]
                        if ext in manage_music_videos.video_extensions:
                            total_videos += 1
                        elif ext == '.lnk' and 'shortcut' in item_lower:
                            total_shortcuts += 1
                except Exception:
                    pass
        except Exception:
            pass
            
    try:
        history = manage_music_videos.load_history()
        cached_count = len(history)
    except Exception:
        pass
        
    return jsonify({
        'status': 'success',
        'pipelineRunning': pipeline_running,
        'pipelineStatusText': pipeline_status_text,
        'config': {
            'path': PIPELINE_PATH,
            'tidalToken': TIDAL_TOKEN,
            'syncDeezerAvatars': SYNC_DEEZER_AVATARS,
            'generateCatalogs': GENERATE_CATALOGS,
            'reconcileShortcuts': RECONCILE_SHORTCUTS
        },
        'stats': {
            'artists': total_artists,
            'videos': total_videos,
            'shortcuts': total_shortcuts,
            'cached': cached_count
        }
    })


@app.route('/api/archive/run', methods=['POST'])
def api_archive_run():
    global pipeline_running, pipeline_status_text, pipeline_logs
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    if pipeline_running:
        return jsonify({'status': 'error', 'message': 'Pipeline orchestrator is already executing operations.'}), 400
        
    req_data = request.json or {}
    archive_path = req_data.get('path', '').strip() or PIPELINE_PATH
    commit = req_data.get('commit', True)
    skip_icons = req_data.get('skipIcons', False)
    skip_deezer = req_data.get('skipDeezer', False)
    force = req_data.get('force', False)
    
    try:
        history_days = int(req_data.get('historyDays', 7))
    except ValueError:
        history_days = 7
        
    if not archive_path:
        return jsonify({'status': 'error', 'message': 'Archive directory path is required.'}), 400
        
    if not os.path.exists(archive_path) or not os.path.isdir(archive_path):
        return jsonify({'status': 'error', 'message': 'Archive directory path does not exist.'}), 400
        
    with logs_lock:
        pipeline_logs.clear()
        
    threading.Thread(
        target=run_pipeline_worker,
        args=(archive_path, commit, skip_icons, skip_deezer, force, history_days),
        daemon=True
    ).start()
    
    return jsonify({'status': 'success', 'message': 'Pipeline started successfully.'})


@app.route('/api/archive/logs', methods=['GET'])
def api_archive_logs():
    with logs_lock:
        return jsonify(pipeline_logs)


@app.route('/api/archive/clear_cache', methods=['POST'])
def api_archive_clear_cache():
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    try:
        if os.path.exists(manage_music_videos.HISTORY_FILE_PATH):
            os.remove(manage_music_videos.HISTORY_FILE_PATH)
        return jsonify({'status': 'success', 'message': 'Cache history cleared successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/archive/artists', methods=['GET'])
def api_archive_artists():
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    archive_path = request.args.get('path', '').strip() or PIPELINE_PATH
    search_query = request.args.get('search', '').strip().lower()
    
    if not archive_path or not os.path.exists(archive_path) or not os.path.isdir(archive_path):
        return jsonify([])
        
    try:
        artists = sorted(manage_music_videos.get_existing_dirs(archive_path))
    except Exception:
        artists = []
        
    excluded_names = ('__pycache__', 'node_modules', 'venv', '.git', 'env', '.idea', '.vscode', '.antigravitycli')
    artists = [a for a in artists if a.lower() not in excluded_names]
    
    history = {}
    try:
        history = manage_music_videos.load_history()
    except Exception:
        pass
        
    artists_list = []
    excluded_terms = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]
    for artist_name in artists:
        if search_query and search_query not in artist_name.lower():
            continue
            
        artist_folder = os.path.join(archive_path, artist_name)
        
        vid_count = 0
        lnk_count = 0
        try:
            for item in os.listdir(artist_folder):
                item_lower = item.lower()
                if any(term in item_lower for term in excluded_terms):
                    continue
                ext = os.path.splitext(item_lower)[1]
                if ext in manage_music_videos.video_extensions:
                    vid_count += 1
                elif ext == '.lnk' and 'shortcut' in item_lower:
                    lnk_count += 1
        except Exception:
            pass
            
        hist = history.get(artist_name)
        status_text = "No Cache History"
        elapsed_days = None
        if hist:
            last_checked_str = hist.get("last_checked")
            if last_checked_str:
                try:
                    last_checked_dt = datetime.strptime(last_checked_str, "%Y-%m-%d %H:%M:%S")
                    elapsed_days = (datetime.now() - last_checked_dt).total_seconds() / (24 * 3600)
                    status_text = f"Cached ({round(elapsed_days, 1)}d ago)"
                except Exception:
                    status_text = "Cached"
            else:
                status_text = "Cached"
                
        has_avatar = False
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            avatar_path = os.path.join(artist_folder, f"avatar{ext}")
            if os.path.exists(avatar_path):
                has_avatar = True
                break
                
        artists_list.append({
            'name': artist_name,
            'folder': artist_folder,
            'videos': vid_count,
            'shortcuts': lnk_count,
            'status': status_text,
            'elapsedDays': elapsed_days,
            'hasAvatar': has_avatar
        })
        
    return jsonify(artists_list)


@app.route('/api/archive/avatar', methods=['GET'])
def api_archive_avatar():
    artist_name = request.args.get('artist', '').strip()
    archive_path = request.args.get('path', '').strip() or PIPELINE_PATH
    
    if not artist_name or not archive_path:
        return jsonify({'status': 'error', 'message': 'Parameters missing'}), 400
        
    artist_folder = os.path.join(archive_path, artist_name)
    if os.path.exists(artist_folder) and os.path.isdir(artist_folder):
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            avatar_file = os.path.join(artist_folder, f"avatar{ext}")
            if os.path.exists(avatar_file):
                from flask import send_file
                return send_file(avatar_file)
                
    return jsonify({'status': 'error', 'message': 'No avatar found'}), 404


@app.route('/api/archive/run_single', methods=['POST'])
def api_archive_run_single():
    global pipeline_running, pipeline_status_text
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    if pipeline_running:
        return jsonify({'status': 'error', 'message': 'Orchestrator pipeline is currently running.'}), 400
        
    req_data = request.json or {}
    artist_name = req_data.get('artist', '').strip()
    archive_path = req_data.get('path', '').strip() or PIPELINE_PATH
    action_type = req_data.get('type', 'catalog').strip()
    
    if not artist_name or not archive_path:
        return jsonify({'status': 'error', 'message': 'Artist name and archive path are required.'}), 400
        
    def single_worker():
        global pipeline_running, pipeline_status_text
        pipeline_running = True
        
        with logs_lock:
            pipeline_logs.clear()
            
        original_get_dirs = manage_music_videos.get_existing_dirs
        manage_music_videos.get_existing_dirs = lambda path: [artist_name]
        
        try:
            if action_type == 'catalog':
                pipeline_status_text = f"Running catalog for {artist_name}..."
                manage_music_videos.log_msg(f"Starting single catalog check for: '{artist_name}'...", "INFO")
                manage_music_videos.execute_catalog_generation(
                    archive_path,
                    skip_deezer=False,
                    history_days=0,
                    force=True
                )
                manage_music_videos.log_msg(f"Catalog for '{artist_name}' successfully compiled!", "SUCCESS")
            elif action_type == 'avatar':
                pipeline_status_text = f"Downloading avatar for {artist_name}..."
                manage_music_videos.log_msg(f"Starting circular avatar download/refresh for: '{artist_name}'...", "INFO")
                manage_music_videos.execute_artist_face_download(
                    archive_path,
                    overwrite=True,
                    apply_icons=True,
                    image_size="xl"
                )
                if manage_music_videos.HAS_CORE:
                    manage_music_videos.core.refresh_explorer()
                manage_music_videos.log_msg(f"Avatar for '{artist_name}' successfully applied!", "SUCCESS")
                
            pipeline_status_text = "Completed"
        except Exception as e:
            manage_music_videos.log_msg(f"Single task error: {e}", "ERROR")
            pipeline_status_text = "Failed"
        finally:
            manage_music_videos.get_existing_dirs = original_get_dirs
            pipeline_running = False
            
    threading.Thread(target=single_worker, daemon=True).start()
    return jsonify({'status': 'success', 'message': 'Single artist task started.'})


@app.route('/api/archive/missing', methods=['GET'])
def api_archive_missing():
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    archive_path = request.args.get('path', '').strip() or PIPELINE_PATH
    search_query = request.args.get('search', '').strip().lower()
    
    if not archive_path or not os.path.exists(archive_path) or not os.path.isdir(archive_path):
        return jsonify([])
        
    try:
        artists = manage_music_videos.get_existing_dirs(archive_path)
    except Exception:
        return jsonify([])
        
    missing_tracks = []
    for artist in artists:
        artist_path = os.path.join(archive_path, artist)
        txt_path = os.path.join(artist_path, "music_videos.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                match = re.search(r"MISSING MUSIC VIDEOS \(NOT YET DOWNLOADED\):\n-+\n(.*?)\n=+", content, re.DOTALL)
                if match:
                    section_text = match.group(1).strip()
                    if section_text and "(All of this artist's top tracks" not in section_text and "(Unable to verify" not in section_text:
                        tracks = re.split(r"\n\s*\n", section_text)
                        for track in tracks:
                            lines = [l.strip() for l in track.split("\n") if l.strip()]
                            if len(lines) >= 1:
                                title_match = re.match(r"^\d+\.\s*(.*)$", lines[0])
                                title = title_match.group(1) if title_match else lines[0]
                                
                                album = "Unknown Album"
                                link = ""
                                for line in lines[1:]:
                                    if "• Album:" in line:
                                        album = line.replace("• Album:", "").strip()
                                    elif "• Deezer:" in line:
                                        link = line.replace("• Deezer:", "").strip()
                                        
                                if search_query:
                                    if search_query not in artist.lower() and search_query not in title.lower() and search_query not in album.lower():
                                        continue
                                        
                                missing_tracks.append({
                                    "artist": artist,
                                    "title": title,
                                    "album": album,
                                    "link": link
                                })
            except Exception:
                pass
                
    return jsonify(missing_tracks)


@app.route('/api/archive/artist/sync', methods=['GET'])
def api_archive_artist_sync():
    if not HAS_LOCAL_MANAGER:
        return jsonify({'status': 'error', 'message': 'Local manager scripts are not loaded.'}), 500
        
    artist_name = request.args.get('artist', '').strip()
    archive_path = request.args.get('path', '').strip() or PIPELINE_PATH
    country_code = request.args.get('countryCode', DEFAULT_COUNTRY).strip().upper()
    
    if not artist_name or not archive_path:
        return jsonify({'status': 'error', 'message': 'Artist and path parameters are required.'}), 400
        
    artist_folder = os.path.join(archive_path, artist_name)
    if not os.path.exists(artist_folder) or not os.path.isdir(artist_folder):
        return jsonify({'status': 'error', 'message': f"Artist folder '{artist_name}' does not exist."}), 404
        
    local_files = []
    try:
        for item in os.listdir(artist_folder):
            item_path = os.path.join(artist_folder, item)
            if os.path.isfile(item_path):
                ext = os.path.splitext(item.lower())[1]
                title_clean = os.path.splitext(item)[0]
                title_clean = re.sub(r'(?i)\s*[\(\[]\s*(?:banned|excluded)\s*[\)\]]', '', title_clean)
                if ext in manage_music_videos.video_extensions:
                    local_files.append({
                        'filename': item,
                        'title': title_clean,
                        'type': 'video'
                    })
                elif ext == '.lnk' and 'shortcut' in item.lower():
                    local_files.append({
                        'filename': item,
                        'title': title_clean.replace(" - Shortcut", "").replace(" - shortcut", ""),
                        'type': 'shortcut'
                    })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Failed to scan local files: {str(e)}"}), 500

    artist_id = None
    tidal_artist_name = artist_name
    tidal_artist_pic = None
    tidal_videos = []
    
    artists = search_artists(artist_name, country_code)
    if artists:
        matched_artist = artists[0]
        for a in artists:
            if a['name'].lower() == artist_name.lower():
                matched_artist = a
                break
        artist_id = matched_artist['id']
        tidal_artist_name = matched_artist['name']
        tidal_artist_pic = matched_artist['picture']
        
    if artist_id:
        try:
            _, _, tidal_videos = fetch_artist_data(artist_id, country_code)
        except Exception as e:
            print(f"Error fetching Tidal videos for ID {artist_id}: {e}")
            
    classified = process_and_filter_videos(tidal_videos)
    
    # Filter banned videos from priority and standard categories using banned.json
    banned_ids = set()
    banned_titles = set()
    banned_file_path = os.path.join(artist_folder, "banned.json")
    if os.path.exists(banned_file_path):
        try:
            with open(banned_file_path, "r", encoding="utf-8") as f:
                banned_data = json.load(f)
                banned_ids = set(str(x) for x in banned_data.get("ids", []))
                banned_titles = set(str(x).lower().strip() for x in banned_data.get("titles", []))
        except Exception as e:
            print(f"Error loading banned.json: {e}")
            
    for cat in ['priority', 'standard']:
        new_cat_list = []
        for video in classified[cat]:
            v_id = str(video.get('id', ''))
            v_title = video.get('title', '')
            if v_id in banned_ids or v_title.lower().strip() in banned_titles:
                video['category'] = 'Excluded'
                video['exclusion_reason'] = 'Banned by user'
                classified['excluded'].append(video)
            else:
                new_cat_list.append(video)
        classified[cat] = new_cat_list
    
    try:
        for cat in ['priority', 'standard', 'excluded']:
            for video in classified[cat]:
                t_id = str(video['id'])
                artists_str = ", ".join(video.get('artists', [])) if video.get('artists') else tidal_artist_name
                v_query = f"{artists_str} - {video['title']}"
                cached_entry = get_from_yt_cache(t_id, v_query)
                if cached_entry:
                    video['youtubeId'] = cached_entry['videoId']
                    video['youtubeUrl'] = cached_entry['videoUrl']
    except Exception as e:
        print(f"Error injecting YT cache: {e}")
        
    def get_norm(val, art_name):
        v = val.lower().strip()
        v = os.path.splitext(v)[0]
        if art_name:
            v = v.replace(art_name.lower().strip(), "")
        common = ["official music video", "official video", "music video", "lyric video", "lyrics video", 
                  "official lyrics", "official lyric", "official audio", "audio video", "shortcut", "collab", 
                  "video", "audio", "lyrics", "hd", "hq", "1080p", "720p", "4k", "banned", "excluded"]
        for term in common:
            v = v.replace(term, "")
        v = re.sub(r'[^a-z0-9]', '', v)
        return v
        
    local_norms = {}
    for lf in local_files:
        norm = get_norm(lf['title'], artist_name)
        if norm:
            local_norms[norm] = lf
            
    existing_videos = []
    waiting_videos = []
    excluded_videos = []
    excluded_terms = ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]
    
    all_allowed = classified['priority'] + classified['standard']
    matched_local_filenames = set()
    
    # 1. Match local files against allowed Tidal videos
    for video in all_allowed:
        v_title = video['title']
        v_norm = get_norm(v_title, artist_name)
        
        matched_lf = None
        for l_norm, lf in local_norms.items():
            if l_norm == v_norm or v_norm in l_norm or l_norm in v_norm:
                # Check if the matched local file itself contains a banned keyword
                lf_title_lower = lf['title'].lower()
                is_lf_excluded = False
                for term in excluded_terms:
                    if term in lf_title_lower:
                        is_lf_excluded = True
                        break
                if is_lf_excluded:
                    continue
                
                matched_lf = lf
                break
                
        if matched_lf:
            video['localFile'] = matched_lf['filename']
            video['localType'] = matched_lf['type']
            existing_videos.append(video)
            matched_local_filenames.add(matched_lf['filename'])
        else:
            waiting_videos.append(video)
            
    # 2. Match local files against excluded Tidal videos
    for video in classified['excluded']:
        v_title = video['title']
        v_norm = get_norm(v_title, artist_name)
        
        matched_lf = None
        for l_norm, lf in local_norms.items():
            if l_norm == v_norm or v_norm in l_norm or l_norm in v_norm:
                matched_lf = lf
                break
                
        if matched_lf:
            video['localFile'] = matched_lf['filename']
            video['localType'] = matched_lf['type']
            matched_local_filenames.add(matched_lf['filename'])
            
        excluded_videos.append(video)
            
    # 3. For local-only files, filter using banned keywords to categorize them
    import uuid
    for lf in local_files:
        if lf['filename'] not in matched_local_filenames:
            title_lower = lf['title'].lower()
            excluded_by = None
            for term in excluded_terms:
                if term in title_lower:
                    excluded_by = term
                    break
            
            local_video_data = {
                'id': f"local_{uuid.uuid4().hex[:6]}",
                'title': lf['title'],
                'localFile': lf['filename'],
                'localType': lf['type'],
                'artists': [artist_name],
                'duration': '—',
                'releaseDate': 'Local File',
                'popularity': 0,
            }
            
            if excluded_by:
                local_video_data['category'] = "Excluded"
                local_video_data['exclusion_reason'] = f"Local file contains '{excluded_by}'"
                excluded_videos.append(local_video_data)
            else:
                local_video_data['category'] = 'Local Only'
                existing_videos.append(local_video_data)
        
    return jsonify({
        'status': 'success',
        'artist': {
            'name': artist_name,
            'tidalName': tidal_artist_name,
            'tidalId': artist_id,
            'picture': tidal_artist_pic,
            'folderPath': artist_folder
        },
        'existing': existing_videos,
        'waiting': waiting_videos,
        'excluded': excluded_videos
    })


@app.route('/api/archive/open_folder', methods=['POST'])
def api_archive_open_folder():
    req_data = request.json or {}
    folder_path = req_data.get('path', '').strip()
    
    if not folder_path:
        return jsonify({'status': 'error', 'message': 'Path is required.'}), 400
        
    if not os.path.exists(folder_path):
        return jsonify({'status': 'error', 'message': 'Folder path does not exist.'}), 400
        
    try:
        os.startfile(folder_path)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/archive/open_file', methods=['POST'])
def api_archive_open_file():
    req_data = request.json or {}
    file_path = req_data.get('path', '').strip()
    
    if not file_path:
        return jsonify({'status': 'error', 'message': 'Path is required.'}), 400
        
    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File path does not exist.'}), 400
        
    try:
        os.startfile(file_path)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/archive/video/ban', methods=['POST'])
def api_archive_video_ban():
    req_data = request.json or {}
    folder = req_data.get('folder', '').strip()
    filename = req_data.get('filename', '').strip()
    title = req_data.get('title', '').strip()
    tidal_id = req_data.get('tidalId', '')
    ban = req_data.get('ban', True)
    
    if not folder:
        return jsonify({'status': 'error', 'message': 'Folder path is required.'}), 400
        
    if not filename:
        if not title:
            return jsonify({'status': 'error', 'message': 'Title or filename is required.'}), 400
            
        banned_file_path = os.path.join(folder, "banned.json")
        banned_data = {"titles": [], "ids": []}
        if os.path.exists(banned_file_path):
            try:
                with open(banned_file_path, "r", encoding="utf-8") as f:
                    banned_data = json.load(f)
            except Exception:
                pass
                
        titles = list(banned_data.get("titles", []))
        ids = list(banned_data.get("ids", []))
        
        title_lower = title.lower().strip()
        titles_lower = [t.lower().strip() for t in titles]
        
        if ban:
            if title_lower not in titles_lower:
                titles.append(title)
            if tidal_id:
                tidal_id_str = str(tidal_id)
                if tidal_id_str not in ids:
                    ids.append(tidal_id_str)
        else:
            titles = [t for t in titles if t.lower().strip() != title_lower]
            if tidal_id:
                tidal_id_str = str(tidal_id)
                ids = [i for i in ids if str(i) != tidal_id_str]
                
        banned_data["titles"] = titles
        banned_data["ids"] = ids
        
        try:
            with open(banned_file_path, "w", encoding="utf-8") as f:
                json.dump(banned_data, f, indent=2, ensure_ascii=False)
            return jsonify({'status': 'success', 'message': f"Track successfully {'banned' if ban else 'unbanned'}."})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f"Failed to update banned.json: {str(e)}"}), 500
            
    old_path = os.path.join(folder, filename)
    if not os.path.exists(old_path):
        return jsonify({'status': 'error', 'message': f"File not found: {filename}"}), 404
        
    base, ext = os.path.splitext(filename)
    
    # Determine new filename
    if ban:
        # Avoid double-adding
        if not re.search(r'(?i)\s*[\(\[]\s*(?:banned|excluded)\s*[\)\]]', base):
            new_filename = f"{base} [Banned]{ext}"
        else:
            new_filename = filename
    else:
        # Remove any occurrence of [Banned] or [Excluded] or [banned] etc.
        new_base = re.sub(r'(?i)\s*[\(\[]\s*(?:banned|excluded)\s*[\)\]]', '', base)
        new_filename = f"{new_base}{ext}"
        
    new_path = os.path.join(folder, new_filename)
    
    if old_path != new_path:
        try:
            # Check if destination already exists
            if os.path.exists(new_path):
                return jsonify({'status': 'error', 'message': f"Destination file already exists: {new_filename}"}), 400
            
            os.rename(old_path, new_path)
            return jsonify({
                'status': 'success', 
                'newFilename': new_filename,
                'message': f"File successfully {'banned' if ban else 'unbanned'}."
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': f"Failed to rename file: {str(e)}"}), 500
    else:
        return jsonify({'status': 'success', 'newFilename': filename, 'message': 'No changes needed.'})


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
