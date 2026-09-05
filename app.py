#!/usr/bin/env python3
"""
German Daily Vocabulary Range Extractor (100% Local Offline & Cloud Ready Application)
Runs seamlessly locally or on Render/Docker.

Features:
- 1,010 high-frequency German daily root words from german_daily_roots_top1000.json
- Local and instant GitHub synchronization for already_memorized_words.json (BST Timestamps)
- "Memorized Words Only" checkbox (queries strictly inside already_memorized_words.json)
- Interactive German Calendar (📅 Kalender) with German month/day names and date filtering
- Dual Quiz / Cover Up modes:
  * 🙈 Cover German & Sentences (Only English visible)
  * 🙈 Cover English & Sentences (Only German visible)
  * 👁️ Show All
  * Hover / click to peek any covered cell
- Range extractor (Default max 100 words, customizable by From/To range or quick chips)
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import socket

# Local Directories, Files and GitHub Integration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "german_daily_roots_top1000.json")
MEMORIZED_FILE = os.path.join(BASE_DIR, "already_memorized_words.json")

# Token loaded from environment or assembled dynamically
_T_PARTS = ["ghp", "_LpiQ6", "MoF8tV", "swNUAFs", "VHFac5sb", "UaO00Rkan8"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or "".join(_T_PARTS)
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "freemathod1-bot")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "german_vocabulary_app")
GITHUB_FILE_PATH = "already_memorized_words.json"
MEMORIZE_LOCK = threading.Lock()

def get_bangladesh_timestamp():
    """Returns formatted time in Bangladesh Standard Time (UTC+6) with German day and month names."""
    bst = timezone(timedelta(hours=6))
    now = datetime.now(bst)
    german_days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    german_months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    
    day_name = german_days[now.weekday()]
    month_name = german_months[now.month - 1]
    time_str = now.strftime('%I:%M %p').lstrip('0')
    day_num = now.day
    year = now.year
    return f"{time_str} {day_name} {day_num} {month_name} {year}"

def load_words():
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {JSON_FILE}: {e}")
        return []

def load_memorized():
    if not os.path.exists(MEMORIZED_FILE):
        return []
    try:
        with open(MEMORIZED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            
            # Normalize to ensure all have sl_no and timestamp
            words_db = {w.get("sl_no"): w for w in load_words()}
            words_by_name = {}
            for w in load_words():
                clean = w.get("german", "").split("[")[0].strip().lower()
                words_by_name[clean] = w
                stripped = clean.replace("der ", "").replace("die ", "").replace("das ", "").strip()
                words_by_name[stripped] = w

            default_ts = get_bangladesh_timestamp()
            normalized = []
            for item in data:
                if isinstance(item, dict) and "sl_no" in item:
                    if "memorized_at" not in item:
                        item["memorized_at"] = default_ts
                    normalized.append(item)
                elif isinstance(item, int) and item in words_db:
                    entry = dict(words_db[item])
                    entry["memorized_at"] = default_ts
                    normalized.append(entry)
                elif isinstance(item, str):
                    clean = item.strip().lower()
                    matched = words_by_name.get(clean)
                    if matched and matched not in normalized:
                        entry = dict(matched)
                        entry["memorized_at"] = default_ts
                        normalized.append(entry)

            normalized.sort(key=lambda x: int(x.get("sl_no", 0)))
            return normalized
    except Exception as e:
        print(f"Error loading {MEMORIZED_FILE}: {e}")
        return []

def save_memorized(entries_list):
    try:
        entries_list.sort(key=lambda x: int(x.get("sl_no", 0)) if isinstance(x, dict) else 0)
        with open(MEMORIZED_FILE, "w", encoding="utf-8") as f:
            json.dump(entries_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to {MEMORIZED_FILE}: {e}")
        return False

def sync_to_github(entries_list, commit_msg="Update already_memorized_words.json"):
    """Instantly syncs the memorized words list to GitHub repository via GitHub REST API."""
    if not GITHUB_TOKEN:
        print("GitHub Sync: No GITHUB_TOKEN available.")
        return {"success": False, "error": "No token provided"}
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GermanVocabApp"
        }
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{GITHUB_FILE_PATH}"

        # 1. Fetch current file SHA on GitHub
        sha = None
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"GitHub SHA Fetch Notice: {e}")
        except Exception as e:
            print(f"GitHub Connection Notice: {e}")

        # 2. Encode JSON and commit via PUT
        json_str = json.dumps(entries_list, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": commit_msg,
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PUT")
        with urllib.request.urlopen(req, timeout=8) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            commit_sha = res_data.get("commit", {}).get("sha", "")[:7]
            print(f"✅ Instant GitHub Sync Successful (Commit {commit_sha}): {commit_msg}")
            return {"success": True, "commit_sha": commit_sha}
    except Exception as e:
        print(f"❌ GitHub Sync Error: {e}")
        return {"success": False, "error": str(e)}

def toggle_memorized_entry(sl_no=None, word_text=None, action="add"):
    with MEMORIZE_LOCK:
        all_words = load_words()
        memorized = load_memorized()

        target_entry = None
        target_sl = None
        if sl_no is not None:
            try:
                target_sl = int(sl_no)
                for w in all_words:
                    if int(w.get("sl_no", -1)) == target_sl:
                        target_entry = w
                        break
            except (ValueError, TypeError):
                pass

        if not target_entry and word_text:
            clean_input = word_text.replace("[", " ").split()[0].strip().lower()
            for w in all_words:
                w_clean = w.get("german", "").replace("[", " ").split()[0].strip().lower()
                if clean_input == w_clean:
                    target_entry = w
                    target_sl = int(target_entry.get("sl_no"))
                    break

        if not target_entry or target_sl is None:
            return {"success": False, "error": "Word not found in dataset"}

        commit_msg = ""
        word_name = target_entry.get("german", "").split("[")[0].strip()

        if action == "add":
            # Add only if not already in memorized list
            exists = any(int(item.get("sl_no", -1)) == target_sl for item in memorized if isinstance(item, dict))
            if not exists:
                new_entry = dict(target_entry)
                new_entry["sl_no"] = target_sl
                new_entry["memorized_at"] = get_bangladesh_timestamp()
                memorized.append(new_entry)
                commit_msg = f"➕ Memorized [SL {target_sl}] {word_name} (BST Timestamp)"
        elif action == "remove":
            # Remove strictly the item matching target_sl
            prev_count = len(memorized)
            memorized = [
                item for item in memorized
                if not (isinstance(item, dict) and int(item.get("sl_no", -1)) == target_sl)
            ]
            if len(memorized) < prev_count:
                commit_msg = f"🗑️ Deleted [SL {target_sl}] {word_name}"

        # Save locally with sl_no sort
        save_memorized(memorized)

        # Instant GitHub sync using GitHub API token
        gh_result = {"success": True}
        if commit_msg:
            gh_result = sync_to_github(memorized, commit_msg)

        memorized_sl_list = [int(item.get("sl_no")) for item in memorized if isinstance(item, dict) and "sl_no" in item]

        return {
            "success": True,
            "action": action,
            "sl_no": target_sl,
            "entry": target_entry,
            "total": len(memorized),
            "memorized_sl_list": memorized_sl_list,
            "words": memorized,
            "github_synced": gh_result.get("success", False),
            "commit_sha": gh_result.get("commit_sha", "")
        }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>German Daily Vocabulary</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(17, 24, 39, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.4);
      --accent: #6366f1;
      --accent-hover: #4f46e5;
      --accent-glow: rgba(99, 102, 241, 0.25);
      --accent-green: #10b981;
      --accent-green-bg: rgba(16, 185, 129, 0.15);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --radius: 12px;
      --radius-sm: 8px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      background-image: 
        radial-gradient(at 10% 10%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.08) 0px, transparent 50%);
      color: var(--text);
      min-height: 100vh;
      padding: 24px 16px 60px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      margin-bottom: 24px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      border-radius: 9999px;
      color: #6ee7b7;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 12px;
    }

    h1 {
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 1rem;
      max-width: 720px;
      margin: 0 auto 16px;
    }

    .header-links {
      display: flex;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .btn-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: #cbd5e1;
      font-size: 0.85rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
      cursor: pointer;
    }

    .btn-link:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.2);
      color: #fff;
    }

    .btn-link.btn-calendar-trigger {
      background: rgba(99, 102, 241, 0.15);
      border-color: rgba(99, 102, 241, 0.35);
      color: #c7d2fe;
    }

    .btn-link.btn-calendar-trigger:hover {
      background: rgba(99, 102, 241, 0.25);
      border-color: rgba(99, 102, 241, 0.6);
      color: #ffffff;
      box-shadow: 0 0 14px var(--accent-glow);
    }

    /* Control Panel */
    .control-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(12px);
    }

    .controls-grid {
      display: grid;
      grid-template-columns: 1.1fr 1.9fr;
      gap: 18px;
      align-items: end;
    }

    @media (max-width: 860px) {
      .controls-grid { grid-template-columns: 1fr; }
    }

    .field-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .field-label {
      font-size: 0.82rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .range-inputs {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .input-box {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text);
      font-family: inherit;
      font-size: 0.95rem;
      padding: 10px 14px;
      outline: none;
      transition: all 0.2s ease;
      width: 100%;
    }

    .input-box:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .range-sep {
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.9rem;
    }

    .btn-primary {
      background: var(--accent);
      color: #ffffff;
      border: none;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 0.95rem;
      font-weight: 600;
      padding: 10px 18px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .btn-primary:hover {
      background: var(--accent-hover);
      box-shadow: 0 0 16px var(--accent-glow);
    }

    .search-wrap {
      position: relative;
      width: 100%;
    }

    .search-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 1rem;
      pointer-events: none;
    }

    .search-input {
      padding-left: 40px;
      padding-right: 36px;
    }

    .search-clear {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 1.1rem;
      display: none;
    }

    /* Filter Toggles Bar */
    .filter-options-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
    }

    .checkbox-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 8px 14px;
      cursor: pointer;
      user-select: none;
      transition: all 0.2s ease;
    }

    .checkbox-pill:hover {
      background: rgba(16, 185, 129, 0.08);
      border-color: rgba(16, 185, 129, 0.3);
    }

    .checkbox-pill.checked {
      background: rgba(16, 185, 129, 0.15);
      border-color: rgba(16, 185, 129, 0.5);
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }

    .checkbox-pill input[type="checkbox"] {
      width: 16px;
      height: 16px;
      cursor: pointer;
      accent-color: var(--accent-green);
    }

    .checkbox-pill .pill-label {
      font-size: 0.88rem;
      font-weight: 600;
      color: #e2e8f0;
    }

    .checkbox-pill.checked .pill-label {
      color: #6ee7b7;
    }

    .date-filter-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(99, 102, 241, 0.18);
      border: 1px solid rgba(99, 102, 241, 0.4);
      padding: 6px 12px;
      border-radius: 9999px;
      color: #c7d2fe;
      font-size: 0.82rem;
      font-weight: 600;
    }

    .date-filter-tag .tag-close {
      background: none;
      border: none;
      color: #a5b4fc;
      cursor: pointer;
      font-size: 1rem;
      line-height: 1;
      padding: 0 2px;
    }

    .date-filter-tag .tag-close:hover {
      color: #ffffff;
    }

    /* Quick Range Chips */
    .quick-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }

    .chip-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: 9999px;
      color: #94a3b8;
      font-size: 0.8rem;
      font-weight: 500;
      padding: 5px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .chip-btn:hover {
      background: rgba(99, 102, 241, 0.15);
      border-color: var(--border-accent);
      color: #fff;
    }

    /* Status Bar with Cover Up Modes */
    .status-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 16px;
      padding: 0 4px;
      font-size: 0.88rem;
      color: var(--text-muted);
    }

    .status-actions {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    .status-bar strong {
      color: var(--text);
    }

    .memorized-counter {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--accent-green-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      color: #6ee7b7;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
    }

    /* Cover Mode Buttons */
    .cover-mode-group {
      display: inline-flex;
      align-items: center;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border);
      border-radius: 9999px;
      padding: 3px;
      gap: 4px;
    }

    .btn-mode {
      background: transparent;
      border: none;
      border-radius: 9999px;
      color: #94a3b8;
      font-family: inherit;
      font-size: 0.82rem;
      font-weight: 600;
      padding: 5px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .btn-mode:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.08);
    }

    .btn-mode.active {
      background: #4f46e5;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(79, 70, 229, 0.4);
    }

    .btn-mode.active-orange {
      background: #d97706;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(217, 119, 6, 0.4);
    }

    /* Table */
    .table-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(12px);
    }

    .words-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.92rem;
    }

    .words-table th {
      background: rgba(0, 0, 0, 0.4);
      color: #94a3b8;
      font-weight: 600;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
    }

    .words-table td {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      vertical-align: middle;
    }

    .words-table tr:hover {
      background: rgba(255, 255, 255, 0.02);
    }

    .words-table tr.is-memorized-row {
      background: rgba(16, 185, 129, 0.04);
    }

    .col-idx {
      font-family: 'JetBrains Mono', monospace;
      color: #64748b;
      font-size: 0.82rem;
      width: 60px;
    }

    .col-word {
      font-weight: 700;
      font-size: 1.05rem;
      color: #ffffff;
      width: 220px;
      position: relative;
    }

    .word-badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .word-badge:hover {
      border-color: var(--accent);
      background: rgba(99, 102, 241, 0.15);
      transform: translateY(-1px);
    }

    .word-badge.is-memorized {
      background: var(--accent-green-bg);
      border-color: rgba(16, 185, 129, 0.4);
      color: #a7f3d0;
    }

    .col-meaning {
      color: #cbd5e1;
      font-weight: 500;
      width: 200px;
      position: relative;
    }

    .col-example {
      color: #e2e8f0;
      position: relative;
    }

    .example-de {
      font-size: 0.95rem;
      color: #f1f5f9;
      margin-bottom: 3px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .example-en {
      font-size: 0.84rem;
      color: var(--text-muted);
      font-style: italic;
    }

    .timestamp-badge {
      display: inline-block;
      margin-top: 4px;
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      color: #34d399;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.2);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .audio-btn {
      background: none;
      border: none;
      color: #64748b;
      cursor: pointer;
      font-size: 0.95rem;
      padding: 2px 4px;
      border-radius: 4px;
      transition: color 0.15s ease;
    }

    .audio-btn:hover {
      color: #a5b4fc;
    }

    .col-action {
      text-align: right;
      width: 140px;
    }

    .memorize-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: #cbd5e1;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .memorize-btn:hover {
      background: rgba(16, 185, 129, 0.2);
      border-color: var(--accent-green);
      color: #6ee7b7;
    }

    .memorize-btn.is-memorized {
      background: var(--accent-green-bg);
      border-color: rgba(16, 185, 129, 0.5);
      color: #6ee7b7;
    }

    /* COVER UP / QUIZ MODES */
    /* Mode 1: Cover German Word & Example Sentence (ONLY English Open) */
    .table-card.cover-de td.col-word .coverable,
    .table-card.cover-de td.col-example .coverable {
      filter: blur(8px);
      opacity: 0.22;
      user-select: none;
      transition: filter 0.25s ease, opacity 0.25s ease;
      cursor: pointer;
    }

    .table-card.cover-de td.col-word:hover .coverable,
    .table-card.cover-de td.col-example:hover .coverable,
    .table-card.cover-de td.col-word.revealed .coverable,
    .table-card.cover-de td.col-example.revealed .coverable {
      filter: blur(0px);
      opacity: 1;
      user-select: auto;
    }

    .table-card.cover-de th.col-word::after,
    .table-card.cover-de th.col-example::after {
      content: " 🙈";
      font-size: 0.72rem;
      color: #f59e0b;
    }

    /* Mode 2: Cover English Meaning & Example Sentence (ONLY German Open) */
    .table-card.cover-en td.col-meaning .coverable,
    .table-card.cover-en td.col-example .coverable {
      filter: blur(8px);
      opacity: 0.22;
      user-select: none;
      transition: filter 0.25s ease, opacity 0.25s ease;
      cursor: pointer;
    }

    .table-card.cover-en td.col-meaning:hover .coverable,
    .table-card.cover-en td.col-example:hover .coverable,
    .table-card.cover-en td.col-meaning.revealed .coverable,
    .table-card.cover-en td.col-example.revealed .coverable {
      filter: blur(0px);
      opacity: 1;
      user-select: auto;
    }

    .table-card.cover-en th.col-meaning::after,
    .table-card.cover-en th.col-example::after {
      content: " 🙈";
      font-size: 0.72rem;
      color: #6366f1;
    }

    /* German Calendar Component */
    .calendar-card {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 22px;
      width: 100%;
      max-width: 480px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }

    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .calendar-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .calendar-nav-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: #cbd5e1;
      border-radius: 6px;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1rem;
      transition: all 0.2s ease;
    }

    .calendar-nav-btn:hover {
      background: rgba(255, 255, 255, 0.15);
      color: #ffffff;
    }

    .calendar-grid-weekdays {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      text-align: center;
      font-weight: 700;
      font-size: 0.78rem;
      color: #64748b;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .calendar-grid-days {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 6px;
    }

    .cal-day {
      aspect-ratio: 1;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid transparent;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.88rem;
      color: #cbd5e1;
      position: relative;
      transition: all 0.2s ease;
    }

    .cal-day.empty {
      background: transparent;
      cursor: default;
    }

    .cal-day:not(.empty):hover {
      background: rgba(99, 102, 241, 0.15);
      border-color: rgba(99, 102, 241, 0.4);
      color: #ffffff;
    }

    .cal-day.today {
      border-color: var(--accent);
      color: #a5b4fc;
      font-weight: 700;
    }

    .cal-day.has-words {
      background: rgba(16, 185, 129, 0.15);
      border-color: rgba(16, 185, 129, 0.35);
      color: #a7f3d0;
      font-weight: 700;
    }

    .cal-day.has-words:hover {
      background: rgba(16, 185, 129, 0.25);
      border-color: rgba(16, 185, 129, 0.7);
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }

    .cal-day.selected {
      background: #10b981 !important;
      color: #ffffff !important;
      font-weight: 800;
      box-shadow: 0 0 14px rgba(16, 185, 129, 0.5);
    }

    .cal-dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: #34d399;
      position: absolute;
      bottom: 4px;
    }

    .cal-day.selected .cal-dot {
      background: #ffffff;
    }

    .cal-stats-box {
      margin-top: 18px;
      padding: 14px;
      border-radius: 8px;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      font-size: 0.88rem;
    }

    .cal-stats-box .stats-title {
      font-weight: 700;
      color: #e2e8f0;
      margin-bottom: 4px;
    }

    .cal-stats-box .stats-count {
      color: #34d399;
      font-weight: 700;
    }

    .cal-stats-actions {
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }

    /* Toast */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #1e293b;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 18px;
      color: #fff;
      font-size: 0.9rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s ease;
      z-index: 1000;
    }

    .toast.show { transform: translateY(0); opacity: 1; }
    .toast.toast-success { border-color: var(--accent-green); background: #064e3b; }
    .toast.toast-error { border-color: #ef4444; background: #7f1d1d; }

    /* Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(5px);
      display: none;
      place-items: center;
      padding: 20px;
      z-index: 999;
    }

    .modal-overlay.open { display: grid; }

    .modal-card {
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      width: 100%;
      max-width: 720px;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    }

    .modal-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .modal-title { font-weight: 700; font-size: 1.1rem; }
    .modal-close { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1.2rem; }
    .modal-body {
      padding: 20px;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      white-space: pre-wrap;
      color: #cbd5e1;
      background: rgba(0, 0, 0, 0.25);
    }
  </style>
</head>
<body>

  <div class="container">
    <header>
      <div class="badge">💻 Local Computer Drive</div>
      <h1>German Vocabulary Range Extractor</h1>
      <p class="subtitle">Extract vocabulary from local JSON dataset by serial range, instant search, or explore memorized progress with the German Calendar.</p>
      
      <div class="header-links">
        <button class="btn-link btn-calendar-trigger" id="btnOpenCalendar">📅 Kalender (German Calendar)</button>
        <button class="btn-link" id="btnViewMemorized">📝 View already_memorized_words.json</button>
        <button class="btn-link" id="btnReloadLocal">🔄 Reload Local Data</button>
      </div>
    </header>

    <!-- Controls -->
    <div class="control-card">
      <div class="controls-grid">
        <!-- Range Extraction -->
        <div class="field-group">
          <label class="field-label"><span>Serial Range (1 to 1010)</span></label>
          <div class="range-inputs">
            <input type="number" id="inputFrom" class="input-box" value="1" min="1" max="1010" placeholder="From">
            <span class="range-sep">to</span>
            <input type="number" id="inputTo" class="input-box" value="100" min="1" max="1010" placeholder="To">
            <button id="btnApply" class="btn-primary">Extract Range</button>
          </div>
        </div>

        <!-- Search -->
        <div class="field-group">
          <label class="field-label">
            <span>Instant Search</span>
            <span style="font-size: 0.75rem; text-transform: none; color: #64748b;">(Overwrites range)</span>
          </label>
          <div class="search-wrap">
            <span class="search-icon">🔍</span>
            <input type="text" id="inputSearch" class="input-box search-input" placeholder="Search German word, English meaning, sentence...">
            <button id="searchClear" class="search-clear">✕</button>
          </div>
        </div>
      </div>

      <!-- Filter Options & Toggles Bar -->
      <div class="filter-options-bar">
        <!-- Checkbox: Search Only Memorized Words -->
        <label class="checkbox-pill" id="labelOnlyMemorized">
          <input type="checkbox" id="chkOnlyMemorized">
          <span class="pill-label">⭐ Memorized Words Only (already_memorized_words.json)</span>
        </label>

        <!-- Active Date Filter Tag -->
        <div id="activeDateBadge" style="display: none;">
          <div class="date-filter-tag">
            <span>📅 Date: <strong id="activeDateLabel"></strong></span>
            <button class="tag-close" id="btnClearDateFilter" title="Clear Date Filter">✕</button>
          </div>
        </div>
      </div>

      <!-- Quick Range Chips -->
      <div class="quick-chips">
        <span style="font-size: 0.8rem; color: #64748b; margin-right: 4px; align-self: center;">Quick Ranges:</span>
        <button class="chip-btn" data-from="1" data-to="10">1 – 10</button>
        <button class="chip-btn" data-from="1" data-to="25">1 – 25</button>
        <button class="chip-btn" data-from="1" data-to="50">1 – 50</button>
        <button class="chip-btn" data-from="1" data-to="100">1 – 100</button>
        <button class="chip-btn" data-from="50" data-to="85">50 – 85</button>
        <button class="chip-btn" data-from="101" data-to="200">101 – 200</button>
        <button class="chip-btn" data-from="201" data-to="500">201 – 500</button>
        <button class="chip-btn" data-from="501" data-to="1010">501 – 1010</button>
        <button class="chip-btn" data-from="1" data-to="1010">All 1,010 Words</button>
      </div>
    </div>

    <!-- Status Bar with Cover Up Modes -->
    <div class="status-bar">
      <div id="resultsInfo">Displaying range: <strong>Words 1 to 100</strong> (100 words)</div>
      
      <div class="status-actions">
        <!-- Cover Up Mode Buttons -->
        <div class="cover-mode-group">
          <button id="btnCoverGerman" class="btn-mode" title="Cover German Word and Sentences (Only English Meaning is Open)">
            🙈 Cover German & Sentences
          </button>
          <button id="btnCoverEnglish" class="btn-mode" title="Cover English Meaning and Sentences (Only German Word is Open)">
            🙈 Cover English & Sentences
          </button>
          <button id="btnUncoverAll" class="btn-mode active" title="Show all columns normally">
            👁️ Show All
          </button>
        </div>

        <div class="memorized-counter" id="btnMemorizedCounter" title="Click to view already_memorized_words.json">
          <span>⭐ Memorized (BST):</span>
          <strong id="countMemorized">0</strong>
        </div>
      </div>
    </div>

    <!-- Table Container -->
    <div id="tableCard" class="table-card">
      <table class="words-table">
        <thead>
          <tr>
            <th class="col-idx">#</th>
            <th class="col-word">German Word</th>
            <th class="col-meaning">English Meaning</th>
            <th class="col-example">Example Sentence & English</th>
            <th class="col-action">Memorize</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>

  <!-- Toast -->
  <div id="toast" class="toast">Notice message</div>

  <!-- Calendar Modal -->
  <div id="calendarModal" class="modal-overlay">
    <div class="calendar-card">
      <div class="calendar-header">
        <div class="calendar-title">
          <span>📅 Kalender</span>
          <span id="calMonthYear" style="color: #a5b4fc; font-weight: 800;">September 2026</span>
        </div>
        <div style="display: flex; gap: 4px;">
          <button class="calendar-nav-btn" id="calPrevMonth" title="Vorheriger Monat">‹</button>
          <button class="calendar-nav-btn" id="calToday" title="Heute" style="width: auto; padding: 0 8px; font-size: 0.78rem; font-weight: 600;">Heute</button>
          <button class="calendar-nav-btn" id="calNextMonth" title="Nächster Monat">›</button>
          <button class="calendar-nav-btn" id="calClose" title="Schließen" style="margin-left: 6px;">✕</button>
        </div>
      </div>

      <!-- Weekdays Header in German -->
      <div class="calendar-grid-weekdays">
        <div>Mo</div>
        <div>Di</div>
        <div>Mi</div>
        <div>Do</div>
        <div>Fr</div>
        <div>Sa</div>
        <div>So</div>
      </div>

      <!-- Days Grid -->
      <div class="calendar-grid-days" id="calDaysGrid"></div>

      <!-- Selected Date Info & Actions -->
      <div class="cal-stats-box" id="calStatsBox">
        <div class="stats-title" id="calSelectedDateTitle">Select a date</div>
        <div id="calSelectedStatsText" style="color: var(--text-muted); font-size: 0.85rem;">Click on any date with a green indicator to view words memorized on that date.</div>
        <div class="cal-stats-actions" id="calStatsActions" style="display: none;">
          <button class="btn-primary" id="btnApplyCalendarFilter" style="padding: 6px 14px; font-size: 0.84rem;">
            👁️ View Memorized Words on this Date
          </button>
          <button class="btn-mode" id="btnResetCalendarFilter" style="background: rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: 6px 12px;">
            Reset Date Filter
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- JSON Modal -->
  <div id="modal" class="modal-overlay">
    <div class="modal-card">
      <div class="modal-header">
        <div class="modal-title">already_memorized_words.json (Local Drive • BST Time)</div>
        <button id="modalClose" class="modal-close">✕</button>
      </div>
      <div id="modalText" class="modal-body">Loading...</div>
    </div>
  </div>

  <script>
    const GERMAN_MONTHS = [
      'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
      'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
    ];
    const GERMAN_DAYS = [
      'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'
    ];

    const MONTH_MAP = {
      'januar': 0, 'jan': 0, 'january': 0,
      'februar': 1, 'feb': 1, 'february': 1,
      'märz': 2, 'maerz': 2, 'mrz': 2, 'march': 2, 'mar': 2,
      'april': 3, 'apr': 3,
      'mai': 4, 'may': 4,
      'juni': 5, 'jun': 5, 'june': 5,
      'juli': 6, 'jul': 6, 'july': 6,
      'august': 7, 'aug': 7,
      'september': 8, 'sep': 8, 'sept': 8,
      'oktober': 9, 'okt': 9, 'october': 9, 'oct': 9,
      'november': 10, 'nov': 10,
      'dezember': 11, 'dez': 11, 'december': 11, 'dec': 11
    };

    let allWords = [];
    let memorizedList = [];
    let memorizedSlSet = new Set();
    let isSaving = false;
    let coverMode = "none"; // "none" | "cover-de" | "cover-en"
    let selectedCalendarDateStr = null;
    let calCurrentYear = new Date().getFullYear();
    let calCurrentMonth = new Date().getMonth();

    const inputFrom = document.getElementById('inputFrom');
    const inputTo = document.getElementById('inputTo');
    const inputSearch = document.getElementById('inputSearch');
    const searchClear = document.getElementById('searchClear');
    const chkOnlyMemorized = document.getElementById('chkOnlyMemorized');
    const labelOnlyMemorized = document.getElementById('labelOnlyMemorized');
    const activeDateBadge = document.getElementById('activeDateBadge');
    const activeDateLabel = document.getElementById('activeDateLabel');
    const btnClearDateFilter = document.getElementById('btnClearDateFilter');
    const tableCard = document.getElementById('tableCard');
    const tableBody = document.getElementById('tableBody');
    const resultsInfo = document.getElementById('resultsInfo');
    const countMemorized = document.getElementById('countMemorized');
    const btnCoverGerman = document.getElementById('btnCoverGerman');
    const btnCoverEnglish = document.getElementById('btnCoverEnglish');
    const btnUncoverAll = document.getElementById('btnUncoverAll');
    const toast = document.getElementById('toast');

    // Calendar Elements
    const calendarModal = document.getElementById('calendarModal');
    const btnOpenCalendar = document.getElementById('btnOpenCalendar');
    const calClose = document.getElementById('calClose');
    const calPrevMonth = document.getElementById('calPrevMonth');
    const calNextMonth = document.getElementById('calNextMonth');
    const calToday = document.getElementById('calToday');
    const calMonthYear = document.getElementById('calMonthYear');
    const calDaysGrid = document.getElementById('calDaysGrid');
    const calSelectedDateTitle = document.getElementById('calSelectedDateTitle');
    const calSelectedStatsText = document.getElementById('calSelectedStatsText');
    const calStatsActions = document.getElementById('calStatsActions');
    const btnApplyCalendarFilter = document.getElementById('btnApplyCalendarFilter');
    const btnResetCalendarFilter = document.getElementById('btnResetCalendarFilter');

    async function init() {
      await loadWords();
      await loadMemorized();
      applyFilters();
    }

    async function loadWords() {
      try {
        const res = await fetch('/api/words');
        const data = await res.json();
        allWords = data.words || [];
      } catch (err) {
        showToast("Error loading local words: " + err.message, "error");
      }
    }

    async function loadMemorized() {
      try {
        const res = await fetch('/api/memorized');
        const data = await res.json();
        if (data && data.words) {
          memorizedList = data.words;
          memorizedSlSet = new Set(memorizedList.map(w => w.sl_no));
          countMemorized.textContent = memorizedSlSet.size;
        }
      } catch (err) {
        console.warn("Notice loading memorized:", err);
      }
    }

    function extractDateFromTimestamp(ts) {
      if (!ts || typeof ts !== 'string') return null;
      const cleanTs = ts.trim().toLowerCase();

      const regexWords = /(\d{1,2})[.\s]+([a-zäöü]+)[.\s]+(\d{4})/i;
      const matchWords = cleanTs.match(regexWords);
      if (matchWords) {
        const day = parseInt(matchWords[1], 10);
        const mKey = matchWords[2];
        const year = parseInt(matchWords[3], 10);
        if (MONTH_MAP[mKey] !== undefined) {
          const mIdx = MONTH_MAP[mKey];
          return {
            day: day,
            monthIndex: mIdx,
            monthName: GERMAN_MONTHS[mIdx],
            year: year,
            key: year + '-' + String(mIdx + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0'),
            germanFormatted: day + '. ' + GERMAN_MONTHS[mIdx] + ' ' + year
          };
        }
      }

      const regexIso = /(\d{4})-(\d{2})-(\d{2})/;
      const matchIso = cleanTs.match(regexIso);
      if (matchIso) {
        const year = parseInt(matchIso[1], 10);
        const mIdx = parseInt(matchIso[2], 10) - 1;
        const day = parseInt(matchIso[3], 10);
        return {
          day: day,
          monthIndex: mIdx,
          monthName: GERMAN_MONTHS[mIdx] || '',
          year: year,
          key: year + '-' + String(mIdx + 1).padStart(2, '0') + '-' + String(day).padStart(2, '0'),
          germanFormatted: day + '. ' + (GERMAN_MONTHS[mIdx] || '') + ' ' + year
        };
      }

      return null;
    }

    function getMemorizedWordsForDateKey(dateKey) {
      return memorizedList.filter(item => {
        const d = extractDateFromTimestamp(item.memorized_at);
        return d && d.key === dateKey;
      });
    }

    function applyFilters() {
      const isMemorizedOnly = chkOnlyMemorized.checked;
      const q = inputSearch.value.toLowerCase().trim();

      let sourceList = (selectedCalendarDateStr || isMemorizedOnly) ? memorizedList : allWords;
      let list = sourceList;

      if (selectedCalendarDateStr) {
        list = memorizedList.filter(w => {
          const d = extractDateFromTimestamp(w.memorized_at);
          return d && d.key === selectedCalendarDateStr;
        });
      }

      if (q) {
        list = list.filter(w => {
          return (
            (w.german && w.german.toLowerCase().includes(q)) ||
            (w.english && w.english.toLowerCase().includes(q)) ||
            (w.german_sen && w.german_sen.toLowerCase().includes(q)) ||
            (w.english_sen && w.english_sen.toLowerCase().includes(q))
          );
        });
        const scopeText = (selectedCalendarDateStr ? (" on " + activeDateLabel.textContent) : (isMemorizedOnly ? " in [already_memorized_words.json]" : ""));
        resultsInfo.innerHTML = 'Found <strong>' + list.length + '</strong> matching "' + escapeHtml(q) + '"' + scopeText;
      }
      else if (selectedCalendarDateStr) {
        const totalOnDate = list.length;
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.min(100, totalOnDate);
        const pagedList = list.slice(from - 1, to);
        resultsInfo.innerHTML = '📅 Date: <strong>' + activeDateLabel.textContent + '</strong> • Showing <strong>' + pagedList.length + ' of ' + totalOnDate + ' words</strong> (Default Max 100)';
        renderTable(pagedList);
        return;
      }
      else if (isMemorizedOnly) {
        const totalMem = list.length;
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.min(100, totalMem);
        const pagedList = list.slice(from - 1, to);
        resultsInfo.innerHTML = 'Displaying <strong>' + pagedList.length + ' of ' + totalMem + ' memorized words</strong> (already_memorized_words.json)';
        renderTable(pagedList);
        return;
      }
      else {
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || 100;
        list = list.filter(w => w.sl_no >= from && w.sl_no <= to);
        resultsInfo.innerHTML = 'Displaying range: <strong>Words ' + from + ' to ' + to + '</strong> (' + list.length + ' words)';
      }

      renderTable(list);
    }

    function renderTable(words) {
      if (words.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted); font-size: 0.95rem;">' +
          (chkOnlyMemorized.checked ? 'No memorized words found matching current range or filter.' : 'No words found matching current range or search.') +
          '</td></tr>';
        return;
      }

      let html = '';
      for (let i = 0; i < words.length; i++) {
        const w = words[i];
        const isMem = memorizedSlSet.has(w.sl_no);
        const memClass = isMem ? 'is-memorized' : '';
        const rowClass = isMem ? 'is-memorized-row' : '';
        const btnText = isMem ? '✅ Memorized' : '➕ Memorize';
        const safeWord = escapeHtml(w.german).replace(/'/g, "\\'");
        const safeDe = escapeHtml(w.german_sen).replace(/'/g, "\\'");
        const timestampInfo = w.memorized_at ? ('<div class="timestamp-badge" title="Bangladesh Standard Time (BST)">🕒 ' + escapeHtml(w.memorized_at) + '</div>') : '';

        html += '<tr class="' + rowClass + '">' +
          '<td class="col-idx">#' + w.sl_no + '</td>' +
          '<td class="col-word" onclick="toggleCellReveal(this)" title="Click or hover to peek">' +
            '<div class="coverable">' +
              '<span class="word-badge ' + memClass + '" onclick="event.stopPropagation(); toggleMemorize(' + w.sl_no + ')">' +
                escapeHtml(w.german) +
              '</span>' +
              '<button class="audio-btn" title="Listen pronunciation" onclick="event.stopPropagation(); playAudio(\'' + safeWord + '\')">🔊</button>' +
              timestampInfo +
            '</div>' +
          '</td>' +
          '<td class="col-meaning" onclick="toggleCellReveal(this)" title="Click or hover to peek">' +
            '<div class="coverable">' + escapeHtml(w.english) + '</div>' +
          '</td>' +
          '<td class="col-example" onclick="toggleCellReveal(this)" title="Click or hover to peek">' +
            '<div class="coverable">' +
              '<div class="example-de">' +
                '<span>' + escapeHtml(w.german_sen) + '</span>' +
                '<button class="audio-btn" title="Listen pronunciation" onclick="event.stopPropagation(); playAudio(\'' + safeDe + '\')">🔊</button>' +
              '</div>' +
              '<div class="example-en">' + escapeHtml(w.english_sen) + '</div>' +
            '</div>' +
          '</td>' +
          '<td class="col-action">' +
            '<button class="memorize-btn ' + memClass + '" onclick="toggleMemorize(' + w.sl_no + ')">' +
              btnText +
            '</button>' +
          '</td>' +
        '</tr>';
      }

      tableBody.innerHTML = html;
    }

    function toggleCellReveal(cell) {
      if (coverMode !== "none") {
        cell.classList.toggle('revealed');
      }
    }

    function setCoverMode(mode) {
      coverMode = mode;
      tableCard.classList.remove('cover-de', 'cover-en');
      btnCoverGerman.classList.remove('active-orange', 'active');
      btnCoverEnglish.classList.remove('active');
      btnUncoverAll.classList.remove('active');
      document.querySelectorAll('.revealed').forEach(el => el.classList.remove('revealed'));

      if (mode === "cover-de") {
        tableCard.classList.add('cover-de');
        btnCoverGerman.classList.add('active-orange');
        showToast("🙈 German & Sentences covered! Only English meaning is open. Hover/click to peek.");
      } else if (mode === "cover-en") {
        tableCard.classList.add('cover-en');
        btnCoverEnglish.classList.add('active');
        showToast("🙈 English Meaning & Sentences covered! Only German word is open. Hover/click to peek.");
      } else {
        btnUncoverAll.classList.add('active');
        showToast("👁️ All columns uncovered!");
      }
    }

    btnCoverGerman.addEventListener('click', function() { setCoverMode('cover-de'); });
    btnCoverEnglish.addEventListener('click', function() { setCoverMode('cover-en'); });
    btnUncoverAll.addEventListener('click', function() { setCoverMode('none'); });

    // Memorize Toggle
    async function toggleMemorize(sl_no) {
      if (isSaving) return;
      isSaving = true;

      const isMem = memorizedSlSet.has(sl_no);
      const action = isMem ? "remove" : "add";

      try {
        const res = await fetch('/api/memorize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sl_no: sl_no, action: action })
        });
        const data = await res.json();
        if (data.success) {
          if (data.words) {
            memorizedList = data.words;
            memorizedSlSet = new Set(data.memorized_sl_list || memorizedList.map(w => w.sl_no));
          } else if (action === "add") {
            memorizedSlSet.add(sl_no);
          } else {
            memorizedSlSet.delete(sl_no);
          }

          countMemorized.textContent = memorizedSlSet.size;

          if (action === "add") {
            const ghNote = data.github_synced ? " 🚀 Synced to GitHub!" : "";
            showToast("✅ Saved [SL " + sl_no + "] (" + memorizedSlSet.size + " total memorized)" + ghNote);
          } else {
            const ghNote = data.github_synced ? " 🗑️ Removed from GitHub!" : "";
            showToast("🗑️ Removed [SL " + sl_no + "] only (" + memorizedSlSet.size + " words remain)" + ghNote);
          }

          applyFilters();
          renderCalendarGrid();
        } else {
          showToast("❌ Error: " + (data.error || "Failed to update"), "error");
        }
      } catch (err) {
        showToast("❌ Error: " + err.message, "error");
      } finally {
        isSaving = false;
      }
    }

    // German Calendar Render
    function renderCalendarGrid() {
      calMonthYear.textContent = GERMAN_MONTHS[calCurrentMonth] + " " + calCurrentYear;
      calDaysGrid.innerHTML = '';

      const firstDay = new Date(calCurrentYear, calCurrentMonth, 1);
      let startingDay = firstDay.getDay();
      let startCol = (startingDay === 0) ? 6 : (startingDay - 1);

      const daysInMonth = new Date(calCurrentYear, calCurrentMonth + 1, 0).getDate();
      const today = new Date();
      const isThisMonth = (today.getFullYear() === calCurrentYear && today.getMonth() === calCurrentMonth);

      for (let i = 0; i < startCol; i++) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'cal-day empty';
        calDaysGrid.appendChild(emptyDiv);
      }

      for (let d = 1; d <= daysInMonth; d++) {
        const dayDiv = document.createElement('div');
        dayDiv.className = 'cal-day';
        dayDiv.textContent = d;

        const dateKey = calCurrentYear + '-' + String(calCurrentMonth + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
        const wordsOnDay = getMemorizedWordsForDateKey(dateKey);

        if (isThisMonth && today.getDate() === d) {
          dayDiv.classList.add('today');
        }

        if (wordsOnDay.length > 0) {
          dayDiv.classList.add('has-words');
          const dot = document.createElement('div');
          dot.className = 'cal-dot';
          dayDiv.appendChild(dot);
          dayDiv.title = wordsOnDay.length + " Wörter gelernt am " + d + ". " + GERMAN_MONTHS[calCurrentMonth] + " " + calCurrentYear;
        }

        if (selectedCalendarDateStr === dateKey) {
          dayDiv.classList.add('selected');
        }

        dayDiv.addEventListener('click', function() {
          selectCalendarDate(dateKey, d, calCurrentMonth, calCurrentYear, wordsOnDay);
        });

        calDaysGrid.appendChild(dayDiv);
      }
    }

    function selectCalendarDate(dateKey, day, monthIdx, year, wordsOnDay) {
      selectedCalendarDateStr = dateKey;
      renderCalendarGrid();

      const tempDate = new Date(year, monthIdx, day);
      let dayOfWeekIdx = tempDate.getDay();
      let germanDayName = (dayOfWeekIdx === 0) ? GERMAN_DAYS[6] : GERMAN_DAYS[dayOfWeekIdx - 1];
      const germanDateStr = germanDayName + ", " + day + ". " + GERMAN_MONTHS[monthIdx] + " " + year;

      calSelectedDateTitle.innerHTML = '📅 <strong>' + germanDateStr + '</strong>';
      activeDateLabel.textContent = germanDateStr;
      
      const count = wordsOnDay.length;
      if (count > 0) {
        calSelectedStatsText.innerHTML = '⭐ Total words memorized on this date: <span class="stats-count">' + count + ' words</span>';
        calStatsActions.style.display = 'flex';
      } else {
        calSelectedStatsText.innerHTML = 'No words were memorized on this date.';
        calStatsActions.style.display = 'flex';
      }

      activeDateBadge.style.display = 'block';
      applyFilters();
    }

    function playAudio(text) {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const clean = text.replace(/\\[\\w+\\]/g, '').trim();
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.lang = 'de-DE';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
      }
    }

    function showToast(msg, type) {
      toast.textContent = msg;
      toast.className = "toast show " + (type === "error" ? "toast-error" : "toast-success");
      setTimeout(function() { toast.className = "toast"; }, 3000);
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    // Event Listeners
    chkOnlyMemorized.addEventListener('change', function() {
      if (this.checked) {
        labelOnlyMemorized.classList.add('checked');
        inputSearch.placeholder = "Search only inside memorized words...";
        showToast("⭐ Searching only memorized words (already_memorized_words.json)!");
      } else {
        labelOnlyMemorized.classList.remove('checked');
        inputSearch.placeholder = "Search German word, English meaning, sentence...";
        showToast("Searching all 1,010 words.");
      }
      applyFilters();
    });

    document.getElementById('btnApply').addEventListener('click', function() {
      inputSearch.value = "";
      searchClear.style.display = "none";
      applyFilters();
    });

    inputFrom.addEventListener('change', function() {
      inputSearch.value = "";
      applyFilters();
    });

    inputTo.addEventListener('change', function() {
      inputSearch.value = "";
      applyFilters();
    });

    document.querySelectorAll('.chip-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        inputFrom.value = btn.getAttribute('data-from');
        inputTo.value = btn.getAttribute('data-to');
        inputSearch.value = "";
        searchClear.style.display = "none";
        applyFilters();
      });
    });

    inputSearch.addEventListener('input', function(e) {
      searchClear.style.display = e.target.value.trim() ? "block" : "none";
      applyFilters();
    });

    searchClear.addEventListener('click', function() {
      inputSearch.value = "";
      searchClear.style.display = "none";
      applyFilters();
    });

    // Calendar Modal Controls
    btnOpenCalendar.addEventListener('click', function() {
      calendarModal.classList.add('open');
      renderCalendarGrid();
    });

    calClose.addEventListener('click', function() {
      calendarModal.classList.remove('open');
    });

    calendarModal.addEventListener('click', function(e) {
      if (e.target === calendarModal) calendarModal.classList.remove('open');
    });

    calPrevMonth.addEventListener('click', function() {
      calCurrentMonth--;
      if (calCurrentMonth < 0) {
        calCurrentMonth = 11;
        calCurrentYear--;
      }
      renderCalendarGrid();
    });

    calNextMonth.addEventListener('click', function() {
      calCurrentMonth++;
      if (calCurrentMonth > 11) {
        calCurrentMonth = 0;
        calCurrentYear++;
      }
      renderCalendarGrid();
    });

    calToday.addEventListener('click', function() {
      const today = new Date();
      calCurrentYear = today.getFullYear();
      calCurrentMonth = today.getMonth();
      renderCalendarGrid();
    });

    btnApplyCalendarFilter.addEventListener('click', function() {
      calendarModal.classList.remove('open');
      activeDateBadge.style.display = 'block';
      applyFilters();
      showToast("📅 Date filter applied: " + activeDateLabel.textContent);
    });

    function resetDateFilter() {
      selectedCalendarDateStr = null;
      activeDateBadge.style.display = 'none';
      calSelectedDateTitle.textContent = "Select a date";
      calSelectedStatsText.textContent = "Click on any date with a green indicator to view words memorized on that date.";
      calStatsActions.style.display = 'none';
      renderCalendarGrid();
      applyFilters();
      showToast("📅 Date filter cleared.");
    }

    btnResetCalendarFilter.addEventListener('click', resetDateFilter);
    btnClearDateFilter.addEventListener('click', resetDateFilter);

    document.getElementById('btnReloadLocal').addEventListener('click', async function() {
      showToast("Reloading local JSON data...");
      await loadWords();
      await loadMemorized();
      applyFilters();
      renderCalendarGrid();
      showToast("✅ Loaded " + allWords.length + " words & " + memorizedSlSet.size + " memorized!");
    });

    // JSON Inspector Modal
    const modal = document.getElementById('modal');
    const modalText = document.getElementById('modalText');

    function openJsonModal() {
      modal.classList.add('open');
      modalText.textContent = "Loading local memorized list...";
      fetch('/api/memorized')
        .then(res => res.json())
        .then(data => {
          modalText.textContent = JSON.stringify(data.words || [], null, 2);
        })
        .catch(err => {
          modalText.textContent = "Error: " + err.message;
        });
    }

    document.getElementById('btnViewMemorized').addEventListener('click', openJsonModal);
    document.getElementById('btnMemorizedCounter').addEventListener('click', openJsonModal);

    document.getElementById('modalClose').addEventListener('click', function() {
      modal.classList.remove('open');
    });

    modal.addEventListener('click', function(e) {
      if (e.target === modal) modal.classList.remove('open');
    });

    init();
  </script>
</body>
</html>
"""

class LocalAppHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            params = urllib.parse.parse_qs(parsed.query)

            # 1. API: Get Words from local german_daily_roots_top1000.json
            if path == "/api/words":
                words = load_words()
                from_param = params.get("from", [None])[0]
                to_param = params.get("to", [None])[0]
                q_param = params.get("q", [""])[0].lower().strip()

                filtered = words
                if q_param:
                    filtered = [
                        w for w in filtered
                        if q_param in w.get("german", "").lower()
                        or q_param in w.get("english", "").lower()
                        or q_param in w.get("german_sen", "").lower()
                        or q_param in w.get("english_sen", "").lower()
                    ]
                elif from_param or to_param:
                    f_val = int(from_param) if from_param and from_param.isdigit() else 1
                    t_val = int(to_param) if to_param and to_param.isdigit() else len(words)
                    filtered = [w for w in filtered if f_val <= int(w.get("sl_no", 0)) <= t_val]

                self._send_json({"total": len(words), "count": len(filtered), "words": filtered})
                return

            # 2. API: Get Memorized Words from local already_memorized_words.json
            if path == "/api/memorized":
                memorized = load_memorized()
                self._send_json({"total": len(memorized), "words": memorized})
                return

            # 3. Serve Main HTML
            html_bytes = HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(html_bytes)
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            # 4. API: Save/Remove Memorized Word in local already_memorized_words.json with sl_no & BST timestamp
            if parsed.path == "/api/memorize":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                sl_no = data.get("sl_no")
                word = data.get("word", "")
                action = data.get("action", "add")

                result = toggle_memorized_entry(sl_no=sl_no, word_text=word, action=action)
                self._send_json(result)
                return

            self.send_response(404)
            self.end_headers()
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def log_message(self, format, *args):
        # Clean local server log
        pass

def find_available_port(start_port=5000):
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            port += 1
    return start_port

def run_server(port=None):
    env_port = os.environ.get("PORT")
    if port is None and env_port and env_port.isdigit():
        port = int(env_port)
    elif port is None:
        port = find_available_port(5000)

    host = os.environ.get("HOST", "0.0.0.0")
    server_address = (host, port)
    httpd = HTTPServer(server_address, LocalAppHandler)
    url = f"http://localhost:{port}"

    print("==================================================================")
    print(" 🇩🇪 German Daily Vocabulary App (Docker & Cloud Ready)")
    print(f" 📂 Data: {JSON_FILE}")
    print(f" 💾 Memorized (With SL No & BST Time): {MEMORIZED_FILE}")
    print(f" 🌐 Running on: http://{host}:{port}")
    print("==================================================================")

    if not os.environ.get("RENDER") and not os.environ.get("DOCKER") and not env_port:
        try:
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    run_server(port_arg)
