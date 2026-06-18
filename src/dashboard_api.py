# -*- coding: utf-8 -*-
# MusicMV animated dashboard - ADDITIVE module. Drop this file into src/ next to app.py.
# It adds a brand new page at /dashboard plus read-only JSON APIs. It does NOT change
# any existing route or pipeline behavior.
#
# Wired from app.py with ONE small edit (see APPLY_PATCH.md):
#     from dashboard_api import register_dashboard
#     register_dashboard(app, lambda: PIPELINE_PATH)
#
# Everything here is grounded in the REAL repo: it scans PIPELINE_PATH for artist
# folders, reads real video files + sizes, counts .lnk collaboration shortcuts, finds
# avatar.jpg, and best-effort parses the "Missing" section of music_videos.txt.

import os
import re

from flask import Blueprint, jsonify, request, render_template, send_file, abort

# Fallback video extensions if manage_music_videos.video_extensions is unavailable.
_DEFAULT_VIDEO_EXTS = {
    ".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg", ".ts",
}
_AVATAR_NAMES = ("avatar.jpg", "avatar.png", "avatar.jpeg", "avatar.webp")
_DEEZER_RE = re.compile(r"https?://[^\s)\]]*deezer\.com[^\s)\]]*", re.IGNORECASE)


def _video_exts():
    try:
        import manage_music_videos
        exts = getattr(manage_music_videos, "video_extensions", None)
        if exts:
            out = set()
            for e in exts:
                e = e.lower()
                out.add(e if e.startswith(".") else "." + e)
            return out
    except Exception:
        pass
    return set(_DEFAULT_VIDEO_EXTS)


def _human_mb(num_bytes):
    try:
        return round(num_bytes / (1024.0 * 1024.0), 1)
    except Exception:
        return 0.0


def _within(root, target):
    """True if target is inside root (handles different drives safely)."""
    try:
        root_abs = os.path.abspath(root)
        tgt_abs = os.path.abspath(target)
        return os.path.commonpath([root_abs, tgt_abs]) == root_abs
    except Exception:
        return False


def _parse_missing(txt_path):
    """Best-effort parse of the 'Missing Music Videos' section in music_videos.txt.
    Returns list of {title, album, deezer}. Never raises."""
    missing = []
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return missing
    in_missing = False
    for raw in lines:
        line = raw.rstrip("\n")
        low = line.lower()
        if ("missing" in low) and ("video" in low or "track" in low):
            in_missing = True
            continue
        if not in_missing:
            continue
        link_m = _DEEZER_RE.search(line)
        if not link_m:
            continue
        link = link_m.group(0)
        before = line[:link_m.start()].strip(" \t-*\u2022.|\u2192")
        before = before.strip("0123456789).· \t")
        album = ""
        title = before
        if " - " in before:
            parts = before.split(" - ")
            title = parts[0].strip()
            album = parts[1].strip() if len(parts) > 1 else ""
        elif "(" in before and before.endswith(")"):
            title = before[:before.rfind("(")].strip()
            album = before[before.rfind("(") + 1:-1].strip()
        if title:
            missing.append({"title": title, "album": album, "deezer": link})
    return missing


def _scan(path):
    exts = _video_exts()
    totals = {"artists": 0, "videos": 0, "collaborations": 0, "missing": 0}
    if not path or not os.path.isdir(path):
        return {"ok": False, "artists": [], "totals": totals, "path": path or "",
                "message": "Archive path is not set or not found. Run the pipeline first."}
    try:
        dirs = sorted([e for e in os.scandir(path) if e.is_dir()], key=lambda e: e.name.lower())
    except Exception as e:
        return {"ok": False, "artists": [], "totals": totals, "path": path, "message": str(e)}

    artists = []
    skip = ("system volume information", "$recycle.bin")
    for d in dirs:
        name = d.name
        if name.startswith(".") or name.lower() in skip:
            continue
        primary, collabs, missing, has_avatar = [], [], [], False
        try:
            for item in os.scandir(d.path):
                if not item.is_file():
                    continue
                low = item.name.lower()
                ext = os.path.splitext(low)[1]
                if low in _AVATAR_NAMES:
                    has_avatar = True
                    continue
                if ext == ".lnk":
                    title = re.sub(r"\s*-\s*shortcut$", "", os.path.splitext(item.name)[0], flags=re.IGNORECASE)
                    collabs.append({"title": title, "filename": item.name, "path": item.path})
                    continue
                if ext in exts:
                    try:
                        size_mb = _human_mb(item.stat().st_size)
                    except Exception:
                        size_mb = 0.0
                    primary.append({"title": os.path.splitext(item.name)[0],
                                    "filename": item.name, "size_mb": size_mb, "path": item.path})
        except Exception:
            pass
        txt = os.path.join(d.path, "music_videos.txt")
        if os.path.isfile(txt):
            missing = _parse_missing(txt)
        primary.sort(key=lambda v: v["title"].lower())
        artists.append({
            "name": name,
            "has_avatar": has_avatar,
            "primary": primary,
            "collaborations": collabs,
            "missing": missing,
            "counts": {"primary": len(primary), "collaborations": len(collabs), "missing": len(missing)},
        })
        totals["videos"] += len(primary)
        totals["collaborations"] += len(collabs)
        totals["missing"] += len(missing)
    totals["artists"] = len(artists)
    return {"ok": True, "artists": artists, "totals": totals, "path": path, "message": ""}


def register_dashboard(app, get_pipeline_path):
    """Attach the dashboard to an existing Flask app.
    get_pipeline_path: a zero-arg callable returning the current archive root string.
    """
    bp = Blueprint("musicmv_dashboard", __name__)

    @bp.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @bp.route("/api/dashboard")
    def dashboard_data():
        try:
            return jsonify(_scan(get_pipeline_path()))
        except Exception as e:
            return jsonify({"ok": False, "artists": [], "totals": {}, "message": str(e)}), 500

    @bp.route("/api/dashboard/avatar/<path:artist>")
    def dashboard_avatar(artist):
        root = get_pipeline_path()
        if not root:
            abort(404)
        folder = os.path.join(root, artist)
        if not _within(root, folder):
            abort(403)
        for fn in _AVATAR_NAMES:
            p = os.path.join(folder, fn)
            if os.path.isfile(p):
                return send_file(p)
        abort(404)

    @bp.route("/api/dashboard/reveal", methods=["POST"])
    def dashboard_reveal():
        data = request.get_json(silent=True) or {}
        target = (data.get("path") or "").strip()
        mode = (data.get("mode") or "open").strip()
        root = get_pipeline_path()
        if not root or not target:
            return jsonify({"ok": False, "message": "No path provided."}), 400
        if not _within(root, target):
            return jsonify({"ok": False, "message": "Path is outside the archive."}), 403
        ap = os.path.abspath(target)
        if not os.path.exists(ap):
            return jsonify({"ok": False, "message": "File not found."}), 404
        try:
            if mode == "folder":
                if os.name == "nt":
                    os.system('explorer /select,"%s"' % ap)
                elif hasattr(os, "startfile"):
                    os.startfile(os.path.dirname(ap))  # type: ignore
                else:
                    import subprocess, sys
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, os.path.dirname(ap)])
            else:
                if hasattr(os, "startfile"):
                    os.startfile(ap)  # type: ignore
                else:
                    import subprocess, sys
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.Popen([opener, ap])
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "message": str(e)}), 500

    app.register_blueprint(bp)
    return bp
