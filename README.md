# 🎵 Music Video Master Sorter & Catalog Manager

A state-of-the-art automated pipeline for Windows designed to sort raw music video files, manage guest artist collaborations, download circular high-resolution artist profiles, and generate comprehensive track catalogs (including missing track detection).

---

## 🚀 Key Features

* **Automated Root Sorter**:
  * Automatically scans the root archive directory, parses file titles, and moves primary tracks to their respective artist subfolders.
* **Dual-Pass Guest Collaborator Reconciliation**:
  * Detects featured artists in song filenames (e.g., `ft.`, `feat.`, `featuring`) and places Windows shortcut links (`.lnk`) in the featured artists' folders pointing back to the source file.
* **Robust Wide-Character C# COM Link Wrapper**:
  * Utilizes an on-the-fly compiled C# COM interface (`IShellLinkW` and `IPersistFile`) inside the PowerShell subprocess to create and read shortcuts, preventing crashes and supporting all international wide-characters (e.g. `Rosalía`, `Chlöe`, `Angèle`) under any system ANSI code page.
* **Deezer-Powered Circular Artist Profiles**:
  * Automatically queries the Deezer API, downloads high-res profile images, crops them to circular icons, and registers them as beautiful system folder icons.
* **Detailed Music Video Catalogs (`music_videos.txt`)**:
  * Creates individual catalog sheets inside each artist folder listing:
    1. **Primary Music Videos**: Alphabetically sorted local tracks with exact file sizes.
    2. **Guest Appearances & Collaborations**: Pointer shortcuts with primary source folders and targets.
    3. **Missing Music Videos (Not Yet Downloaded)**: Automatically compares local files with the artist's Top 50 tracks on Deezer, listing missing hits along with their album name and direct Deezer links!

---

## 🛠️ Tech Stack & Requirements

* **Language**: Python 3.9+
* **Dependencies**: Pillow (PIL), ctypes, standard libraries (urllib, json, re)
* **Windows Integration**: PowerShell subprocess calling a native C# compiled COM Link wrapper.

---

## ⚡ Quick Start

### 1. Frictionless Run (Combined Batch Launcher)
* **`Run-Music-Video-Manager.bat`**: Unified master launcher that runs the entire end-to-end pipeline sequentially (sorting root videos, reconciling collaborator shortcuts, generating catalogs, downloading avatars, and applying circular folder icons).

### 2. Manual CLI Run
```bash
python manage_music_videos.py --dir "G:\Music\Music Video" --commit
```

---

## 📂 Repository Architecture

```
E:\Projects\Icon-Music\
├── Run-Music-Video-Manager.bat     # Combined master sorter, cataloger, and icon wizard
├── manage_music_videos.py          # Unified music video pipeline orchestrator
├── core.py                         # Core logic (imaging, Windows file flags, shell notifies)
├── sort_music_videos.py            # Historical sorting module (legacy archive)
├── download_artist_faces.py        # Historical face downloader (legacy archive)
├── requirements.txt                # Dependencies list
└── README.md                       # Repository documentation
```
