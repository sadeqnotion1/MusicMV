import os
import sys
import re
import subprocess
import shutil
import time
import json
import urllib.request
import urllib.parse
import argparse

# Ensure standard output supports UTF-8 for unicode artist/song names in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add current directory to path so we can import core.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import core
    HAS_CORE = True
except ImportError:
    HAS_CORE = False

# Configuration and Paths
DEEZER_SEARCH_URL = "https://api.deezer.com/search/artist?q="
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_video_manager.log")
HISTORY_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_video_history.json")

video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv')

# Casing corrections for artist search / folders
artist_casing_corrections = {
    "kendrick lemar": "Kendrick Lamar",
    "kendrik lemar": "Kendrick Lamar",
    "lisa": "Lisa",
    "jennie": "Jennie",
    "blackpink": "BLACKPINK",
    "raye": "RAYE",
    "ykniece": "YKNiece",
    "bunnab": "BunnaB",
    "lil nas": "Lil Nas X",
    "lil nas x": "Lil Nas X",
    "cardib": "Cardi B",
    "cardi b": "Cardi B",
    "selena gomez": "Selena Gomez",
    "sellina gomes": "Selena Gomez",
    "sexyy red": "Sexyy Red"
}

# Manual overrides for specific files
manual_overrides = {
    "Calvin_Harris_Potion_Official_Video_ft_Dua_Lipa_Young_Thug.mp4": ["Calvin Harris", "Dua Lipa", "Young Thug"],
    "DJ_Snake_Taki_Taki_ft_Selena_Gomez,_Ozuna,_Cardi_B_Official.mp4": ["DJ Snake", "Selena Gomez", "Ozuna", "Cardi B"],
    "Dua_Lipa_Be_the_One_Live_from_Radical_Optimism_Tour_2025,_Ham.mp4": ["Dua Lipa"],
    "Dua_Lipa_Dance_The_Night_From_Barbie_The_Album_Official_Mus.mp4": ["Dua Lipa"],
    "Dua_Lipa_Levitating_feat_Madonna_and_Missy_Elliott_The_Ble.mp4": ["Dua Lipa", "Madonna", "Missy Elliott"],
    "Dua_Lipa_Swan_Song_From_Alita_Battle_Angel_Official_Music_V.mp4": ["Dua Lipa"],
    "Dua_Lipa_Training_Season_Houdini_Live_at_The_GRAMMYs_2024.mp4": ["Dua Lipa"],
    "Dua_Lipa_Training_Season_Live_from_the_Royal_Albert_Hall_Of.mp4": ["Dua Lipa"],
    "Martin_Garrix_Dua_Lipa_Scared_To_Be_Lonely_Official_Video.mp4": ["Martin Garrix", "Dua Lipa"],
    "Megan_Thee_Stallion_Dua_Lipa_Sweetest_Pie_Official_Video.mp4": ["Megan Thee Stallion", "Dua Lipa"],
    "Silk_City,_Dua_Lipa_Electricity_Official_Video_ft_Diplo,_Ma.mp4": ["Silk City", "Dua Lipa", "Diplo", "Mark Ronson"],
    "Taylor_Swift_Fortnight_feat_Post_Malone_Official_Music_Vid.mp4": ["Taylor Swift", "Post Malone"],
    "The_Weeknd_ft_Dua_Lipa_Let_Me_With_You_ft_Eilish_Sounds.mp4": ["The Weeknd", "Dua Lipa"]
}

def log_msg(msg, level="INFO", console_prefix="", console=True):
    """
    Central logger function. Prints emoji-safe messages to the console
    and appends a structured, timestamped log line to E:\\Projects\\Icon\\music_video_manager.log.
    If console is False, only writes to the log file.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}\n"
    
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass
        
    if not console:
        return
        
    if level == "DEBUG":
        print(f"{console_prefix}[DEBUG] {msg}")
    elif level == "WARNING":
        print(f"{console_prefix}[WARNING] {msg}")
    elif level == "OK":
        print(f"{console_prefix}[OK] {msg}")
    elif level == "SUCCESS":
        print(f"{console_prefix}[SUCCESS] {msg}")
    elif level == "ERROR":
        print(f"{console_prefix}[ERROR] {msg}")
    else:
        print(f"{console_prefix}{msg}")

CS_SHORTCUT_HELPER_SOURCE = """using System;
using System.Runtime.InteropServices;
using System.Text;

[ComImport]
[Guid("00021401-0000-0000-C000-000000000046")]
public class ShellLink {}

[ComImport]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
[Guid("000214F9-0000-0000-C000-000000000046")]
public interface IShellLinkW {
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszFile, int cchMaxPath, IntPtr pfd, int fFlags);
    void GetIDList(out IntPtr ppidl);
    void SetIDList(IntPtr pidl);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszName, int cchMaxName);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszDir, int cchMaxPath);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string pszDir);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszArgs, int cchMaxPath);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string pszArgs);
    void GetHotkey(out short pwHotkey);
    void SetHotkey(short wHotkey);
    void GetShowCmd(out int piShowCmd);
    void SetShowCmd(int iShowCmd);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszIconPath, int cchIconPath, out int piIcon);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string pszIconPath, int iIcon);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string pszPathRel, int dwReserved);
    void Resolve(IntPtr hwnd, int fFlags);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string pszFile);
}

[ComImport]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
[Guid("0000010b-0000-0000-C000-000000000046")]
public interface IPersistFile {
    void GetClassID(out Guid pClassID);
    void IsDirty();
    void Load([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, int dwMode);
    void Save([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, [MarshalAs(UnmanagedType.Bool)] bool fRemember);
    void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string pszFileName);
    void GetCurFile([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder ppszFileName);
}

public static class ShortcutHelper {
    public static void Create(string shortcutPath, string targetPath) {
        ShellLink link = new ShellLink();
        IShellLinkW shellLink = (IShellLinkW)link;
        shellLink.SetPath(targetPath);
        IPersistFile persistFile = (IPersistFile)link;
        persistFile.Save(shortcutPath, true);
    }
    
    public static string Read(string shortcutPath) {
        ShellLink link = new ShellLink();
        IPersistFile persistFile = (IPersistFile)link;
        persistFile.Load(shortcutPath, 0);
        IShellLinkW shellLink = (IShellLinkW)link;
        StringBuilder sb = new StringBuilder(260);
        shellLink.GetPath(sb, sb.Capacity, IntPtr.Zero, 0);
        return sb.ToString();
    }
}"""

def create_shortcut(target_path, shortcut_path):
    """Create Windows shortcut using PowerShell with native C# IShellLinkW COM wrapper."""
    target_path = os.path.abspath(target_path).replace('/', '\\')
    shortcut_path = os.path.abspath(shortcut_path).replace('/', '\\')
    
    # Escape single-quotes for PowerShell string insertion
    t_path_escaped = target_path.replace("'", "''")
    s_path_escaped = shortcut_path.replace("'", "''")
    
    ps_content = f"""$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$source = @"
{CS_SHORTCUT_HELPER_SOURCE}
"@

if (-not ([System.Management.Automation.PSTypeName]"ShortcutHelper").Type) {{
    Add-Type -TypeDefinition $source
}}
[ShortcutHelper]::Create('{s_path_escaped}', '{t_path_escaped}')
"""
    temp_dir = os.environ.get("TEMP", os.path.dirname(shortcut_path))
    temp_script_path = os.path.join(temp_dir, "temp_create_shortcut_mgr.ps1")
    
    with open(temp_script_path, "w", encoding="utf-8-sig") as f:
        f.write(ps_content)
        
    result = subprocess.run([
        "powershell", 
        "-NoProfile", 
        "-ExecutionPolicy", "Bypass", 
        "-File", temp_script_path
    ], capture_output=True)
    
    try:
        os.remove(temp_script_path)
    except:
        pass
        
    if result.returncode != 0:
        err_msg = ""
        try:
            err_msg = result.stderr.decode('utf-8', errors='replace')
        except Exception:
            try:
                err_msg = result.stderr.decode('cp1252', errors='replace')
            except Exception:
                err_msg = str(result.stderr)
        raise Exception(f"Failed to create shortcut: {err_msg}")

def get_shortcut_target(shortcut_path):
    """Read Windows shortcut target using PowerShell with native C# IShellLinkW COM wrapper."""
    shortcut_path = os.path.abspath(shortcut_path).replace('/', '\\')
    if not os.path.exists(shortcut_path):
        return None
        
    # Escape single-quotes for PowerShell string insertion
    s_path_escaped = shortcut_path.replace("'", "''")
        
    ps_content = f"""$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$source = @"
{CS_SHORTCUT_HELPER_SOURCE}
"@

if (-not ([System.Management.Automation.PSTypeName]"ShortcutHelper").Type) {{
    Add-Type -TypeDefinition $source
}}
$target = [ShortcutHelper]::Read('{s_path_escaped}')
Write-Output $target
"""
    temp_dir = os.environ.get("TEMP", os.path.dirname(shortcut_path))
    temp_script_path = os.path.join(temp_dir, "temp_read_shortcut_mgr.ps1")
    try:
        with open(temp_script_path, "w", encoding="utf-8-sig") as f:
            f.write(ps_content)
        
        result = subprocess.run([
            "powershell", 
            "-NoProfile", 
            "-ExecutionPolicy", "Bypass", 
            "-File", temp_script_path
        ], capture_output=True)
        
        try:
            target = result.stdout.decode('utf-8', errors='replace').strip()
        except Exception:
            try:
                target = result.stdout.decode('cp1252', errors='replace').strip()
            except Exception:
                target = ""
        return target if target else None
    except Exception:
        return None
    finally:
        try:
            os.remove(temp_script_path)
        except:
            pass

def clean_artist_name(name):
    name = name.strip()
    name = re.sub(r'^[\s\-_,]+|[\s\-_,]+$', '', name)
    name = re.sub(r'(?i)\b(ft|feat|featuring)\b\.?.*$', '', name)
    name = name.strip()
    return name

def split_artists(artist_str):
    delimiters = re.compile(r'(?i)\s*(?:,|\s+&\s+|\b&\b|&|\band\b|\bwith\b|\bx\b|\+)\s*')
    parts = delimiters.split(artist_str)
    artists = []
    for part in parts:
        cleaned = clean_artist_name(part)
        if cleaned and len(cleaned) > 1:
            artists.append(cleaned)
    return artists

def get_existing_dirs(path):
    dirs = []
    try:
        for item in os.listdir(path):
            if os.path.isdir(os.path.join(path, item)) and not item.startswith('.'):
                dirs.append(item)
    except Exception as e:
        log_msg(f"Failed to read subdirectories: {e}", "ERROR")
    return dirs

def parse_artists_from_filename(filename, current_folder, known_folders):
    if filename in manual_overrides:
        return manual_overrides[filename]
        
    base_name, _ = os.path.splitext(filename)
    
    # Strip common tags
    cleaned_base = base_name
    tags_regex = re.compile(r'(?i)\s*[\(\[]\s*(?:Official\s+)?(?:Music\s+)?Video\s*[\)\]]')
    cleaned_base = tags_regex.sub('', cleaned_base)
    cleaned_base = re.compile(r'(?i)\s*[\(\[]\s*Official\s+MV\s*[\)\]]').sub('', cleaned_base)
    cleaned_base = re.compile(r'(?i)\s*\bOfficial\s+MV\b').sub('', cleaned_base)
    cleaned_base = re.compile(r'(?i)\s*\bOfficial\s+Music\s+Video\b').sub('', cleaned_base)
    cleaned_base = re.compile(r'(?i)\s*\bOfficial\s+Video\b').sub('', cleaned_base)
    
    # Replace underscores if underline format
    if '_' in cleaned_base and (' ' not in cleaned_base or cleaned_base.count('_') > cleaned_base.count(' ')):
        cleaned_base = cleaned_base.replace('_', ' ')
        
    # Check if there's no structured separator (like ' - ' or '  ')
    if ' - ' not in cleaned_base and '  ' not in cleaned_base:
        # Search filename for any known artist name
        found_known_artists = []
        sorted_known = sorted(known_folders, key=len, reverse=True)
        for k in sorted_known:
            pattern = rf'(?i)\b{re.escape(k)}\b'
            if re.search(pattern, cleaned_base):
                if k not in found_known_artists:
                    found_known_artists.append(k)
                    
        # Check custom casing corrections
        for custom_k in sorted(artist_casing_corrections.keys(), key=len, reverse=True):
            pattern = rf'(?i)\b{re.escape(custom_k)}\b'
            if re.search(pattern, cleaned_base):
                res_name = artist_casing_corrections[custom_k]
                if res_name not in found_known_artists:
                    found_known_artists.append(res_name)
                    
        if found_known_artists:
            return found_known_artists
        else:
            return [current_folder]
            
    # Regular parsing with separators
    primary = []
    secondary = []
    
    if ' - ' in cleaned_base:
        parts = cleaned_base.split(' - ', 1)
        artist_part = parts[0]
        song_part = parts[1]
        
        primary = split_artists(artist_part)
        
        feat_match = re.search(r'(?i)\b(?:ft|feat|featuring)\b\.?\s*([^\(\[\)\]]+)', song_part)
        if feat_match:
            secondary = split_artists(feat_match.group(1))
            
        sorted_known = sorted(known_folders, key=len, reverse=True)
        for k in sorted_known:
            pattern = rf'(?i)\b{re.escape(k)}\b'
            if re.search(pattern, song_part):
                if k not in primary and k not in secondary:
                    secondary.append(k)
                    
    elif '  ' in cleaned_base:
        parts = re.split(r'\s{2,}', cleaned_base, 1)
        artist_part = parts[0]
        song_part = parts[1]
        
        primary = split_artists(artist_part)
        
        feat_match = re.search(r'(?i)\b(?:ft|feat|featuring)\b\.?\s*([^\(\[\)\]]+)', song_part)
        if feat_match:
            secondary = split_artists(feat_match.group(1))
            
        sorted_known = sorted(known_folders, key=len, reverse=True)
        for k in sorted_known:
            pattern = rf'(?i)\b{re.escape(k)}\b'
            if re.search(pattern, song_part):
                if k not in primary and k not in secondary:
                    secondary.append(k)
                    
    all_parsed = []
    for a in primary + secondary:
        if a not in all_parsed:
            all_parsed.append(a)
            
    return all_parsed

def clean_song_title(filename, artist_name):
    """Extract and format a clean song title from a filename."""
    base_name, _ = os.path.splitext(filename)
    
    # Strip common tags
    cleaned = base_name
    cleaned = re.sub(r'(?i)\s*[\(\[]\s*(?:banned|excluded)\s*[\)\]]', '', cleaned)
    tags_regex = re.compile(r'(?i)\s*[\(\[]\s*(?:Official\s+)?(?:Music\s+)?Video\s*[\)\]]')
    cleaned = tags_regex.sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*[\(\[]\s*Official\s+MV\s*[\)\]]').sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*\bOfficial\s+MV\b').sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*\bOfficial\s+Music\s+Video\b').sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*\bOfficial\s+Video\b').sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*\bLyric\s+Video\b').sub('', cleaned)
    cleaned = re.compile(r'(?i)\s*[\(\[]\s*Lyric\s*Video\s*[\)\]]').sub('', cleaned)
    
    # Replace underscores if underline format
    if '_' in cleaned and (' ' not in cleaned or cleaned.count('_') > cleaned.count(' ')):
        cleaned = cleaned.replace('_', ' ')
        
    # Split by ' - ' or '  '
    if ' - ' in cleaned:
        parts = cleaned.split(' - ', 1)
        if parts[0].strip().lower() == artist_name.lower():
            cleaned = parts[1]
        else:
            cleaned = parts[1]
    elif '  ' in cleaned:
        parts = re.split(r'\s{2,}', cleaned, 1)
        if parts[0].strip().lower() == artist_name.lower():
            cleaned = parts[1]
        else:
            cleaned = parts[1]
            
    # Strip guest tags from song title to make it super clean
    cleaned = re.sub(r'(?i)\s*[\(\[]?\s*\b(?:ft|feat|featuring)\b\.?.*$', '', cleaned)
    
    # Clean special characters
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.title()

_deezer_cache = {}
_deezer_top_tracks_cache = {}

def search_deezer_artist(artist_name):
    """Search for artist on Deezer and return the artist data dictionary (with memory caching)."""
    artist_name_clean = artist_name.strip().lower()
    if artist_name_clean in _deezer_cache:
        return _deezer_cache[artist_name_clean]
        
    query = urllib.parse.quote(artist_name)
    url = f"{DEEZER_SEARCH_URL}{query}"
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'data' in data and len(data['data']) > 0:
                res = data['data'][0]
                _deezer_cache[artist_name_clean] = res
                return res
    except Exception as e:
        log_msg(f"Search connection error for '{artist_name}': {e}", "WARNING")
    _deezer_cache[artist_name_clean] = None
    return None

def get_deezer_artist_top_tracks(artist_id, limit=50):
    """Fetch top tracks for an artist from Deezer (with memory caching)."""
    if artist_id in _deezer_top_tracks_cache:
        return _deezer_top_tracks_cache[artist_id]
        
    url = f"https://api.deezer.com/artist/{artist_id}/top?limit={limit}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'data' in data:
                res = data['data']
                _deezer_top_tracks_cache[artist_id] = res
                return res
    except Exception as e:
        log_msg(f"Error fetching top tracks for artist ID {artist_id}: {e}", "DEBUG")
    return []

def normalize_title_for_matching(title):
    """Normalize a song title for fuzzy/exact alphanumeric matching."""
    title = title.lower()
    # Remove text in parentheses/brackets (e.g. "(Official Music Video)")
    title = re.sub(r'[\(\[][^\)\]]*[\)\]]', ' ', title)
    # Remove featuring tags and everything after them
    title = re.sub(r'(?i)\b(ft|feat|featuring)\b\.?.*$', ' ', title)
    # Remove common music video tags
    tags = ['official', 'music', 'video', 'mv', 'hd', 'hq', '4k', '1080p', '720p', 'lyrics', 'audio', 'lyric', 'extended', 'remix', 'radio', 'edit', 'remastered', 'live']
    for tag in tags:
        title = re.sub(rf'\b{tag}\b', ' ', title)
    # Remove track numbers at the beginning (e.g., "01 - Title", "01. Title", "01 Title")
    title = re.sub(r'^\d+\s*[-_.]?\s*', '', title)
    # Keep only alphanumeric characters
    cleaned = ''.join(c for c in title if c.isalnum())
    return cleaned

def download_image(url, save_path):
    """Download image from URL."""
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
            return True
    except Exception as e:
        log_msg(f"Failed to download image from {url}: {e}", "WARNING")
        return False

# ==============================================================================
# CORE WORKFLOW ACTIONS
# ==============================================================================

def execute_sorting(target_dir, commit=False):
    log_msg("STEP 1: SORTING ROOT VIDEOS & RECONCILING SHORTCUTS")
    log_msg("-" * 60)
    
    root_count = run_organizer(target_dir, commit=commit)
    missing_count = run_reconciler(target_dir, commit=commit)
    
    return root_count, missing_count

def run_organizer(workspace_dir, commit=False):
    kendrik_lemar_path = os.path.join(workspace_dir, "Kendrik Lemar")
    kendrick_lamar_path = os.path.join(workspace_dir, "Kendrick Lamar")
    
    if os.path.exists(kendrik_lemar_path):
        log_msg(f"[TYPO FIX] Found directory 'Kendrik Lemar'. Consolidating to 'Kendrick Lamar'.", "WARNING")
        if commit:
            try:
                if os.path.exists(kendrick_lamar_path):
                    for item in os.listdir(kendrik_lemar_path):
                        shutil.move(os.path.join(kendrik_lemar_path, item), os.path.join(kendrick_lamar_path, item))
                    os.rmdir(kendrik_lemar_path)
                else:
                    os.rename(kendrik_lemar_path, kendrick_lamar_path)
                log_msg("Consolidated typo folder successfully.", "SUCCESS")
            except Exception as e:
                log_msg(f"Consolidation failed: {e}", "ERROR")
            
    existing_dirs = get_existing_dirs(workspace_dir)
    if not commit and "Kendrik Lemar" in existing_dirs:
        existing_dirs.remove("Kendrik Lemar")
        if "Kendrick Lamar" not in existing_dirs:
            existing_dirs.append("Kendrick Lamar")
            
    dir_map_lower = {d.lower(): d for d in existing_dirs}
    
    def resolve_artist_name(name):
        name_lower = name.lower()
        if name_lower in artist_casing_corrections:
            return artist_casing_corrections[name_lower]
        if name_lower in dir_map_lower:
            return dir_map_lower[name_lower]
        return name
        
    root_files = []
    try:
        for item in os.listdir(workspace_dir):
            full_path = os.path.join(workspace_dir, item)
            if os.path.isfile(full_path) and not item.startswith('.'):
                if item.lower() == 'desktop.ini':
                    continue
                if item.lower().endswith('.lnk'):
                    if commit:
                        try:
                            os.remove(full_path)
                            log_msg(f"Cleaned root level shortcut: '{item}'", "OK")
                        except Exception:
                            pass
                    continue
                if item.lower().endswith(video_extensions):
                    root_files.append(item)
    except Exception as e:
        log_msg(f"Failed to scan root files: {e}", "ERROR")
        return 0
                
    if not root_files:
        log_msg("No new root files found to sort.", "OK")
        return 0
        
    log_msg(f"Found {len(root_files)} files at the root level to sort.\n", "INFO")
    
    actions = []
    for f in sorted(root_files):
        parsed = parse_artists_from_filename(f, "Unknown", existing_dirs)
        primary = parsed[0] if parsed else "Unknown"
        secondary = parsed[1:] if len(parsed) > 1 else []
        
        primary_resolved = resolve_artist_name(primary)
        secondary_resolved = [resolve_artist_name(s) for s in secondary]
        
        actions.append({
            "filename": f,
            "primary": primary_resolved,
            "secondary": secondary_resolved
        })
        
    log_msg("SORTING PLAN:")
    for a in actions:
        log_msg(f"  • Move:      '{a['filename']}' -> '{a['primary']}/'", "INFO")
        if a['secondary']:
            log_msg(f"    Shortcuts: {', '.join(a['secondary'])}", "INFO")
            
    if commit:
        log_msg("\nSorting files...", "INFO")
        for a in actions:
            orig_file = a["filename"]
            prim = a["primary"]
            secs = a["secondary"]
            
            src_path = os.path.join(workspace_dir, orig_file)
            if not os.path.exists(src_path):
                continue
                
            prim_folder = os.path.join(workspace_dir, prim)
            os.makedirs(prim_folder, exist_ok=True)
            dest_path = os.path.join(prim_folder, orig_file)
            
            try:
                shutil.move(src_path, dest_path)
                log_msg(f"Moved: '{orig_file}' -> '{prim}/'", "SUCCESS")
                
                for sec in secs:
                    sec_folder = os.path.join(workspace_dir, sec)
                    os.makedirs(sec_folder, exist_ok=True)
                    
                    base_name, _ = os.path.splitext(orig_file)
                    shortcut_name = f"{base_name} - Shortcut.lnk"
                    shortcut_path = os.path.join(sec_folder, shortcut_name)
                    
                    try:
                        create_shortcut(dest_path, shortcut_path)
                        log_msg(f"  Created shortcut in '{sec}': '{shortcut_name}'", "OK")
                    except Exception as e:
                        log_msg(f"  Failed shortcut in '{sec}': {e}", "WARNING")
            except Exception as e:
                log_msg(f"Failed to move '{orig_file}': {e}", "ERROR")
                
    return len(root_files)

def run_reconciler(workspace_dir, commit=False):
    existing_dirs = get_existing_dirs(workspace_dir)
    dir_map_lower = {d.lower(): d for d in existing_dirs}
    
    def resolve_artist_name(name):
        name_lower = name.lower()
        if name_lower in artist_casing_corrections:
            return artist_casing_corrections[name_lower]
        if name_lower in dir_map_lower:
            return dir_map_lower[name_lower]
        return name
        
    # Scan subfolders
    files_to_process = []
    for artist_dir in sorted(existing_dirs):
        artist_path = os.path.join(workspace_dir, artist_dir)
        try:
            for item in os.listdir(artist_path):
                item_lower = item.lower()
                if any(term in item_lower for term in ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]):
                    continue
                item_path = os.path.join(artist_path, item)
                if os.path.isfile(item_path) and item_lower.endswith(video_extensions):
                    files_to_process.append({
                        "filename": item,
                        "current_folder": artist_dir,
                        "full_path": item_path
                    })
        except Exception:
            pass
                
    log_msg(f"Scanning {len(files_to_process)} sorted music video files inside artist folders.", "INFO")
    
    shortcuts_to_create = []
    for item in files_to_process:
        filename = item["filename"]
        curr_folder = item["current_folder"]
        full_path = item["full_path"]
        
        parsed_artists = parse_artists_from_filename(filename, curr_folder, existing_dirs)
        resolved_artists = [resolve_artist_name(a) for a in parsed_artists]
        
        other_artists = []
        for artist in resolved_artists:
            if artist.lower() != curr_folder.lower():
                if artist not in other_artists:
                    other_artists.append(artist)
                    
        if other_artists:
            for other_artist in other_artists:
                other_artist_folder = os.path.join(workspace_dir, other_artist)
                base_name, _ = os.path.splitext(filename)
                shortcut_name = f"{base_name} - Shortcut.lnk"
                shortcut_path = os.path.join(other_artist_folder, shortcut_name)
                
                if not os.path.exists(shortcut_path):
                    shortcuts_to_create.append({
                        "video_file": filename,
                        "video_path": full_path,
                        "source_folder": curr_folder,
                        "shortcut_folder": other_artist,
                        "shortcut_name": shortcut_name,
                        "shortcut_path": shortcut_path
                    })
                    
    log_msg(f"Found {len(shortcuts_to_create)} missing shortcuts.", "INFO")
    
    if shortcuts_to_create:
        log_msg("\nMISSING SHORTCUT PLAN:")
        for s in shortcuts_to_create:
            log_msg(f"  • Create shortcut in '{s['shortcut_folder']}/' -> for '{s['source_folder']}/{s['video_file']}'", "INFO")
            
        if commit:
            log_msg("\nCreating missing shortcuts...", "INFO")
            for s in shortcuts_to_create:
                dest_folder_path = os.path.join(workspace_dir, s['shortcut_folder'])
                os.makedirs(dest_folder_path, exist_ok=True)
                
                try:
                    create_shortcut(s['video_path'], s['shortcut_path'])
                    log_msg(f"  Created: '{s['shortcut_folder']}/{s['shortcut_name']}'", "SUCCESS")
                except Exception as e:
                    log_msg(f"  Failed shortcut in '{s['shortcut_folder']}': {e}", "WARNING")
                
    return len(shortcuts_to_create)

def load_history():
    """Load history from JSON file."""
    if os.path.exists(HISTORY_FILE_PATH):
        try:
            with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_msg(f"Failed to load history: {e}", "WARNING")
    return {}

def save_history(history):
    """Save history to JSON file."""
    try:
        with open(HISTORY_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_msg(f"Failed to save history: {e}", "WARNING")

def get_folder_signature(folder_path):
    """Generate a signature of the folder's video and shortcut files to detect changes."""
    signature_parts = []
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for item in sorted(os.listdir(folder_path)):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item.lower())[1]
                    if ext in video_extensions or (ext == '.lnk' and 'shortcut' in item.lower()):
                        try:
                            stat = os.stat(item_path)
                            signature_parts.append(f"{item}:{stat.st_size}:{stat.st_mtime}")
                        except Exception:
                            signature_parts.append(f"{item}:unknown")
    except Exception:
        pass
    return "|".join(signature_parts)

# ==============================================================================
# CATALOG GENERATION WORKFLOW
# ==============================================================================

def execute_catalog_generation(target_dir, skip_deezer=False, history_days=7, force=False):
    log_msg("\nSTEP 2: GENERATING MUSIC VIDEO CATALOG SHEETS FOR EACH ARTIST")
    log_msg("-" * 60)
    if skip_deezer:
        log_msg("Deezer API integration is disabled (--skip-deezer). Compiling local-only catalogs.", "WARNING")
        
    existing_dirs = get_existing_dirs(target_dir)
    if not existing_dirs:
        log_msg("No artist folders found to catalog.", "WARNING")
        return
        
    history = load_history()
    history_updated = False
    skipped_history_count = 0
    
    cataloged_count = 0
    total_folders = len(existing_dirs)
    for idx, artist_name in enumerate(sorted(existing_dirs), 1):
        artist_folder = os.path.join(target_dir, artist_name)
        catalog_path = os.path.join(artist_folder, "music_videos.txt")
        
        # Generate current signature
        current_sig = get_folder_signature(artist_folder)
        
        # Check if we can skip
        can_skip = False
        if not force and os.path.exists(catalog_path):
            artist_hist = history.get(artist_name)
            if artist_hist:
                last_checked_str = artist_hist.get("last_checked")
                saved_sig = artist_hist.get("files_signature")
                
                if saved_sig == current_sig and last_checked_str:
                    try:
                        last_checked = time.strptime(last_checked_str, "%Y-%m-%d %H:%M:%S")
                        last_checked_epoch = time.mktime(last_checked)
                        elapsed_days = (time.time() - last_checked_epoch) / (24 * 3600)
                        if elapsed_days < history_days:
                            can_skip = True
                    except Exception:
                        pass
                        
        if can_skip:
            log_msg(f"  [{idx}/{total_folders}] ⏩ Skipping catalog for: '{artist_name}' (recently checked & no changes)", "INFO")
            skipped_history_count += 1
            continue
            
        # Display real-time progress on the console so it never appears "stuck"
        log_msg(f"  [{idx}/{total_folders}] Compiling catalog for: '{artist_name}'...", "INFO")
        
        primary_videos = []
        collaborations = []
        
        try:
            for item in os.listdir(artist_folder):
                item_lower = item.lower()
                if any(term in item_lower for term in ["lyric video", "lyric vid", "visualizer", "behind the scenes", "audio", "lyrics", "lyric", "banned", "excluded"]):
                    continue
                item_path = os.path.join(artist_folder, item)
                if os.path.isfile(item_path):
                    ext = os.path.splitext(item_lower)[1]
                    if ext in video_extensions:
                        # Fetch file size
                        size_bytes = os.path.getsize(item_path)
                        size_mb = round(size_bytes / (1024 * 1024), 2)
                        
                        song_title = clean_song_title(item, artist_name)
                        primary_videos.append({
                            "filename": item,
                            "title": song_title,
                            "size": size_mb
                        })
                    elif ext == '.lnk' and 'shortcut' in item.lower():
                        # Read shortcut target
                        target = get_shortcut_target(item_path)
                        primary_artist = "Unknown"
                        target_size = 0.0
                        
                        if target and os.path.exists(target):
                            primary_artist = os.path.basename(os.path.dirname(target))
                            t_bytes = os.path.getsize(target)
                            target_size = round(t_bytes / (1024 * 1024), 2)
                            
                        song_title = clean_song_title(item.replace(" - Shortcut", "").replace(" - shortcut", ""), artist_name)
                        collaborations.append({
                            "filename": item,
                            "title": song_title,
                            "primary_artist": primary_artist,
                            "size": target_size
                        })
        except Exception as e:
            log_msg(f"Failed to scan videos for artist '{artist_name}': {e}", "WARNING")
            continue
            
        # Build beautiful catalog file
        catalog_path = os.path.join(artist_folder, "music_videos.txt")
        
        # Identify missing music videos using Deezer top tracks API
        missing_videos = []
        artist_data = None
        
        # Load banned titles from banned.json if it exists
        banned_titles = set()
        banned_file_path = os.path.join(artist_folder, "banned.json")
        if os.path.exists(banned_file_path):
            try:
                with open(banned_file_path, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                    banned_titles = set(str(x).lower().strip() for x in b_data.get("titles", []))
            except Exception:
                pass
        
        if not skip_deezer:
            artist_query = clean_artist_name(artist_name)
            artist_data = search_deezer_artist(artist_query)
            if artist_data:
                artist_id = artist_data.get("id")
                if artist_id:
                    top_tracks = get_deezer_artist_top_tracks(artist_id, limit=50)
                    if top_tracks:
                        # Normalize local files and collaborations
                        local_normalized = set()
                        for pv in primary_videos:
                            local_normalized.add(normalize_title_for_matching(pv['title']))
                        for col in collaborations:
                            local_normalized.add(normalize_title_for_matching(col['title']))
                            
                        for track in top_tracks:
                            track_title = track.get("title_short") or track.get("title")
                            if not track_title:
                                continue
                            if track_title.lower().strip() in banned_titles:
                                continue
                            norm_track = normalize_title_for_matching(track_title)
                            if norm_track not in local_normalized:
                                # Double check if the artist matches the target search query to prevent false-positives
                                is_relevant = False
                                track_artist = track.get("artist", {}).get("name", "")
                                if clean_artist_name(track_artist).lower() == artist_query.lower():
                                    is_relevant = True
                                else:
                                    # Check all contributors (for guest tracks/collabs)
                                    contributors = track.get("contributors", [])
                                    for c in contributors:
                                        if clean_artist_name(c.get("name", "")).lower() == artist_query.lower():
                                            is_relevant = True
                                            break
                                if is_relevant:
                                    missing_videos.append({
                                        "title": track_title,
                                        "album": track.get("album", {}).get("title", "Unknown Album"),
                                        "link": track.get("link", "")
                                    })
                                    
        total_tracks = len(primary_videos) + len(collaborations)
        
        sheet = []
        sheet.append("=" * 70)
        sheet.append(f" MUSIC VIDEO CATALOG - {artist_name.upper()}")
        sheet.append("=" * 70)
        sheet.append(f"• Artist:           {artist_name}")
        if skip_deezer:
            sheet.append(f"• Total Tracks:     {total_tracks} (Primary: {len(primary_videos)}, Collaborations: {len(collaborations)})")
        else:
            sheet.append(f"• Total Tracks:     {total_tracks} (Primary: {len(primary_videos)}, Collaborations: {len(collaborations)}, Missing/Not Downloaded: {len(missing_videos)})")
        sheet.append(f"• Last Updated:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
        sheet.append("=" * 70)
        sheet.append("")
        
        sheet.append("PRIMARY MUSIC VIDEOS:")
        sheet.append("-" * 70)
        if primary_videos:
            # Sort primary videos alphabetically by title
            for idx2, pv in enumerate(sorted(primary_videos, key=lambda x: x['title'].lower()), 1):
                sheet.append(f"  {idx2:02d}. {pv['title']}")
                sheet.append(f"      • Filename: {pv['filename']}")
                sheet.append(f"      • File Size: {pv['size']} MB")
                sheet.append("")
        else:
            sheet.append("  (No primary music videos found in this folder)")
            sheet.append("")
            
        sheet.append("GUEST APPEARANCES & COLLABORATIONS:")
        sheet.append("-" * 70)
        if collaborations:
            # Sort collaborations alphabetically by title
            for idx2, col in enumerate(sorted(collaborations, key=lambda x: x['title'].lower()), 1):
                sheet.append(f"  {idx2:02d}. {col['title']}")
                sheet.append(f"      • Shortcut: {col['filename']}")
                sheet.append(f"      • Primary Folder: {col['primary_artist']}/")
                if col['size'] > 0:
                    sheet.append(f"      • File Size: {col['size']} MB")
                sheet.append("")
        else:
            sheet.append("  (No collaborative shortcuts found in this folder)")
            sheet.append("")
            
        if not skip_deezer:
            sheet.append("MISSING MUSIC VIDEOS (NOT YET DOWNLOADED):")
            sheet.append("-" * 70)
            if missing_videos:
                # Sort missing videos alphabetically by title
                for idx2, mv in enumerate(sorted(missing_videos, key=lambda x: x['title'].lower()), 1):
                    sheet.append(f"  {idx2:02d}. {mv['title']}")
                    sheet.append(f"      • Album: {mv['album']}")
                    if mv['link']:
                        sheet.append(f"      • Deezer: {mv['link']}")
                    sheet.append("")
            else:
                if artist_data:
                    sheet.append("  (All of this artist's top tracks appear to be present locally!)")
                else:
                    sheet.append("  (Unable to verify missing tracks - Deezer API unreachable or artist not found)")
                sheet.append("")
            
        sheet.append("=" * 70)
        
        try:
            with open(catalog_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(sheet))
            cataloged_count += 1
            if skip_deezer:
                log_msg(f"    Generated catalog for '{artist_name}' ({total_tracks} tracks)", "SUCCESS")
            else:
                log_msg(f"    Generated catalog for '{artist_name}' ({total_tracks} tracks, {len(missing_videos)} missing)", "SUCCESS")
            
            # Update history on successful write
            history[artist_name] = {
                "last_checked": time.strftime("%Y-%m-%d %H:%M:%S"),
                "files_signature": current_sig
            }
            history_updated = True
        except Exception as e:
            log_msg(f"    Failed to write catalog for '{artist_name}': {e}", "WARNING")
            
    if history_updated:
        save_history(history)
        
    if skipped_history_count > 0:
        log_msg(f"⏩ Skipped {skipped_history_count} artists because they were recently checked and had no changes.", "OK")
            
    log_msg(f"Successfully generated music video catalog sheets inside {cataloged_count} artist directories!", "SUCCESS")

# ==============================================================================
# ARTIST FACE DOWNLOAD & ICON WORKFLOW
# ==============================================================================

def execute_artist_face_download(target_dir, overwrite=False, apply_icons=True, image_size="xl"):
    log_msg("\nSTEP 3: BATCH DOWNLOADING ARTIST AVATARS & SETTING FOLDER ICONS")
    log_msg("-" * 60)
    
    subfolders = get_existing_dirs(target_dir)
    excluded_names = ('__pycache__', 'node_modules', 'venv', '.git', 'env', '.idea', '.vscode', '.antigravitycli')
    subfolders = [f for f in subfolders if f.lower() not in excluded_names]
    
    if not subfolders:
        log_msg("No artist directories found to download icons for.", "WARNING")
        return
        
    log_msg(f"Found {len(subfolders)} artist directories to check.", "INFO")
    
    downloads_count = 0
    skipped_count = 0
    failed_count = 0
    applied_count = 0
    
    size_field = f"picture_{image_size}"
    
    for idx, folder_name in enumerate(subfolders, 1):
        folder_path = os.path.join(target_dir, folder_name)
        
        has_existing_avatar = False
        avatar_path = None
        
        # Look for existing avatar files matching our standard
        if HAS_CORE:
            for file in os.listdir(folder_path):
                name, ext = os.path.splitext(file.lower())
                if name in core.AVATAR_NAMES and ext in core.AVATAR_EXTENSIONS:
                    has_existing_avatar = True
                    avatar_path = os.path.join(folder_path, file)
                    break
        else:
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                test_path = os.path.join(folder_path, f"avatar{ext}")
                if os.path.exists(test_path):
                    has_existing_avatar = True
                    avatar_path = test_path
                    break
                    
        # Skip if already exists and overwrite is False
        if has_existing_avatar and not overwrite:
            skipped_count += 1
            
            # Apply folder icon anyway if desktop.ini is missing
            if apply_icons and HAS_CORE:
                try:
                    icon_path = os.path.join(folder_path, 'avatar.ico')
                    desktop_ini = os.path.join(folder_path, 'desktop.ini')
                    if not os.path.exists(icon_path) or not os.path.exists(desktop_ini):
                        core.apply_folder_icon(folder_path, avatar_path)
                        applied_count += 1
                except Exception:
                    pass
            continue
            
        artist_query = clean_artist_name(folder_name)
        log_msg(f"[{idx}/{len(subfolders)}] Fetching profile image for: '{artist_query}'", "INFO")
        
        artist_data = search_deezer_artist(artist_query)
        if not artist_data:
            log_msg(f"  Artist '{artist_query}' not found on Deezer API.", "WARNING")
            failed_count += 1
            continue
            
        img_url = artist_data.get(size_field) or artist_data.get("picture_big") or artist_data.get("picture")
        if not img_url:
            log_msg(f"  No picture URL available for '{artist_query}'.", "WARNING")
            failed_count += 1
            continue
            
        save_file_path = os.path.join(folder_path, "avatar.jpg")
        
        # Remove any existing avatars with other extensions
        for ext in ['.png', '.jpeg', '.webp']:
            old_file = os.path.join(folder_path, f"avatar{ext}")
            if os.path.exists(old_file) and old_file != save_file_path:
                try:
                    os.remove(old_file)
                except Exception:
                    pass
                    
        if download_image(img_url, save_file_path):
            downloads_count += 1
            log_msg(f"  Saved avatar file to: {os.path.basename(save_file_path)}", "OK")
            
            if apply_icons and HAS_CORE:
                try:
                    core.apply_folder_icon(folder_path, save_file_path)
                    applied_count += 1
                    log_msg("  Folder icon applied successfully!", "SUCCESS")
                except Exception as e:
                    log_msg(f"  Folder icon failed: {e}", "WARNING")
        else:
            failed_count += 1
            
        time.sleep(0.5)
        
    log_msg("-" * 60)
    log_msg("BATCH ICON SUMMARY:")
    log_msg(f"  Total Avatars Downloaded: {downloads_count}")
    log_msg(f"  Folders Configured with Icons: {applied_count}")
    log_msg(f"  Folders Skipped: {skipped_count}")
    log_msg(f"  Failed/Not Found: {failed_count}")
    log_msg("-" * 60)

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Music Video Master Manager - Automatically organize folders, generate shortcuts, build catalogues, and download custom artist profiles."
    )
    
    parser.add_argument(
        "--dir", "-d",
        type=str,
        help="Directory containing the music video files. Defaults to G:\\Music\\Music Video."
    )
    
    parser.add_argument(
        "--commit", "-c",
        action="store_true",
        help="Commit sorting and folder icon application instantly."
    )
    
    parser.add_argument(
        "--overwrite-avatars",
        action="store_true",
        help="Redownload and overwrite existing artist profile avatars."
    )
    
    parser.add_argument(
        "--skip-icons",
        action="store_true",
        help="Skip searching, downloading and applying circular artist profiles."
    )
    
    parser.add_argument(
        "--skip-deezer",
        action="store_true",
        help="Skip querying Deezer API entirely to keep execution 100% offline and local."
    )
    
    parser.add_argument(
        "--history-days",
        type=int,
        default=7,
        help="Number of days to cache artist catalog checks before querying Deezer API again (default: 7)."
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Ignore history/cache and force-update all catalogs."
    )
    
    args = parser.parse_args()
    
    # Configure path with interactive prompt
    target_dir = args.dir
    if not target_dir:
        default_mv_path = r"G:\Music\Music Video"
        if not os.path.exists(default_mv_path) or not os.path.isdir(default_mv_path):
            default_mv_path = os.getcwd()
            
        print("=== MUSIC VIDEO MASTER MANAGER & ICON WIZARD ===")
        print("=" * 60)
        try:
            user_input = input(f"Enter the Music Video folder path to process\n   [Default: {default_mv_path}]: ").strip()
            if user_input:
                target_dir = user_input
            else:
                target_dir = default_mv_path
        except (EOFError, KeyboardInterrupt):
            target_dir = default_mv_path
            print()
            
    target_dir = os.path.abspath(target_dir)
    
    # Clean/Initialize log file on new execution run
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(f"=== MUSIC VIDEO MASTER MANAGER START | TIME: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Target Directory: {target_dir}\n")
            f.write("=" * 60 + "\n\n")
    except Exception:
        pass
        
    log_msg("=" * 60)
    log_msg(" MUSIC VIDEO MASTER MANAGER & ICON WIZARD ")
    log_msg("=" * 60)
    log_msg(f"Archive Directory: {target_dir}")
    log_msg(f"Diagnostic Log Saved: {os.path.basename(LOG_FILE_PATH)}")
    log_msg("-" * 60)
    
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        log_msg(f"Error: Target directory does not exist: {target_dir}", "ERROR")
        sys.exit(1)
        
    commit_changes = args.commit
    
    # If not committed, run sorting dry-run first
    if not commit_changes:
        root_count = run_organizer(target_dir, commit=False)
        missing_count = run_reconciler(target_dir, commit=False)
        total_actions = root_count + missing_count
        
        if total_actions > 0:
            log_msg("\n" + "=" * 60)
            try:
                user_input = input(f"Would you like to apply the above changes and run the manager? (y/N): ").strip().lower()
                if user_input in ('y', 'yes'):
                    commit_changes = True
                else:
                    log_msg("\nOperation cancelled. No changes were made.", "WARNING")
                    return
            except (EOFError, KeyboardInterrupt):
                log_msg("\nOperation cancelled. No changes were made.", "WARNING")
                return
        else:
            log_msg("\nNo files need sorting or reconciliation. Proceeding with manager...", "INFO")
            commit_changes = True
            
    if commit_changes:
        # STEP 1: Sort Root Files & Reconcile Shortcuts
        execute_sorting(target_dir, commit=True)
        
        # STEP 2: Generate Music Video Catalog for Each Artist
        execute_catalog_generation(
            target_dir, 
            skip_deezer=args.skip_deezer, 
            history_days=args.history_days, 
            force=args.force
        )
        
        # STEP 3: Batch Download Artist Avatars & Set Folder Icons
        if not args.skip_icons:
            execute_artist_face_download(
                target_dir, 
                overwrite=args.overwrite_avatars, 
                apply_icons=True, 
                image_size="xl"
            )
            
        # STEP 4: Shell Notification Refresh
        if HAS_CORE:
            log_msg("\nSending Windows Shell notify refresh to update all custom folder icons instantly...")
            core.refresh_explorer()
            
        log_msg("\nAll music video manager operations completed successfully!", "SUCCESS")
        
    print("\nPress Enter to exit...")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

if __name__ == "__main__":
    main()
