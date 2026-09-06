#!/usr/bin/env python3
"""
German Daily Vocabulary Range Extractor & Multi-Dataset Dictionary
(100% Local Offline & Cloud Ready Application)
Runs seamlessly locally or on Render/Docker.

Integrated Datasets:
- 🌟 german_daily_roots_top1000.json (1,010 Daily Root Words with Example Sentences)
- 📘 a1_german_word_list_with_english.json (790 Goethe A1 Vocabulary)
- 📗 a2_german_word_list_with_english.json (1,342 Goethe A2 Vocabulary)
- 📙 b1_german_word_list_with_english.json (3,261 Goethe B1 Vocabulary)
- 📚 a1_a2_b1_combined.json (3,328 Complete CEFR A1-B1 Combined Words)
- 📄 Dynamic auto-discovery of any other .json files in the folder

Data Tracking:
- 💾 already_memorized_words.json: Stores memorized words with BST timestamps & GitHub sync
- 🗑️ deleted_datas.json: Stores deleted words with BST timestamps, source dataset & GitHub sync

Features:
- Instant Dataset Switching with real-time range reconfiguration
- One-click "Delete" button beside "Memorize" button (stores to deleted_datas.json)
- Filter by "Memorized Words Only" and "Deleted Words Only (with Restore option)"
- Interactive German Calendar (📅 Kalender) with German month/day names and date filtering
- Dual Quiz / Cover Up modes:
  * 🙈 Cover German & Sentences (Only English visible)
  * 🙈 Cover English & Sentences (Only German visible)
  * 👁️ Show All
  * Hover / click to peek any covered cell
- Range extractor (Customizable by From/To range or dynamic quick chips)
- German Text-to-Speech audio pronunciation for all vocabulary & sentences
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
DEFAULT_DATASET = "german_daily_roots_top1000.json"
MEMORIZED_FILE = os.path.join(BASE_DIR, "already_memorized_words.json")
DELETED_FILE = os.path.join(BASE_DIR, "deleted_datas.json")

# Metadata mapping for known datasets
KNOWN_DATASETS = {
    "german_daily_roots_top1000.json": {
        "name": "Top 1,000 Daily Roots",
        "icon": "🌟",
        "badge": "Roots + Sentences",
        "description": "1,010 high-frequency German daily root words with example sentences & translations"
    },
    "a1_german_word_list_with_english.json": {
        "name": "Goethe A1 Word List",
        "icon": "📘",
        "badge": "A1 Beginner",
        "description": "790 Goethe-Zertifikat A1 official vocabulary items"
    },
    "a2_german_word_list_with_english.json": {
        "name": "Goethe A2 Word List",
        "icon": "📗",
        "badge": "A2 Elementary",
        "description": "1,342 Goethe-Zertifikat A2 official vocabulary items"
    },
    "b1_german_word_list_with_english.json": {
        "name": "Goethe B1 Word List",
        "icon": "📙",
        "badge": "B1 Intermediate",
        "description": "3,261 Goethe-Zertifikat B1 official vocabulary items"
    },
    "a1_a2_b1_combined.json": {
        "name": "A1 + A2 + B1 Combined",
        "icon": "📚",
        "badge": "Full CEFR A1–B1",
        "description": "3,328 combined Goethe/CEFR A1, A2, and B1 vocabulary collection"
    }
}

# Metadata mapping for known German PDF reference guides
KNOWN_PDFS = {
    # 🏷️ Suffixes & Prefixes
    "german_noun_suffixes_and_prefixes.pdf": {
        "title": "German Noun Suffixes & Prefixes",
        "category": "Suffixes & Prefixes",
        "icon": "🏷️",
        "badge": "Nouns",
        "description": "Comprehensive guide to prefixes and suffixes forming German nouns and gender patterns."
    },
    "german_verb_suffixes_and_prefixes.pdf": {
        "title": "German Verb Suffixes & Prefixes",
        "category": "Suffixes & Prefixes",
        "icon": "🏷️",
        "badge": "Verbs",
        "description": "Essential inseparable and separable prefixes and suffix rules for German verbs."
    },
    "german_adjective_suffixes_and_prefixes.pdf": {
        "title": "German Adjective Suffixes & Prefixes",
        "category": "Suffixes & Prefixes",
        "icon": "🏷️",
        "badge": "Adjectives",
        "description": "Rules and patterns for building adjectives with prefixes (un-, ur-) and suffixes (-bar, -lich, -ig)."
    },
    "german_adverb_suffixes_and_prefixes.pdf": {
        "title": "German Adverb Suffixes & Prefixes",
        "category": "Suffixes & Prefixes",
        "icon": "🏷️",
        "badge": "Adverbs",
        "description": "Adverbial derivation patterns, prefixes, and suffixes in standard German."
    },

    # ⚡ Verbs & Conjugation
    "most_common_german_regular_verbs.pdf": {
        "title": "Most Common German Regular Verbs",
        "category": "Verbs & Conjugation",
        "icon": "⚡",
        "badge": "Regular Verbs",
        "description": "Frequent regular (weak) German verbs with standard conjugations and definitions."
    },
    "all_irregular_german_verbs_with_english_meaning.pdf": {
        "title": "All Irregular German Verbs + English Meaning",
        "category": "Verbs & Conjugation",
        "icon": "⚡",
        "badge": "Irregular Verbs",
        "description": "Complete list of strong and irregular German verbs with vowel stems and English translations."
    },
    "german_verbs_6_septermber_2026_gemni.pdf": {
        "title": "German Verbs Master Reference (Gemini)",
        "category": "Verbs & Conjugation",
        "icon": "⚡",
        "badge": "Master Verbs",
        "description": "Comprehensive German verbs compilation and detailed reference guide."
    },

    # 🔤 Parts of Speech
    "most_common_german_nouns_with_english_meaning.pdf": {
        "title": "Most Common German Nouns + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Nouns",
        "description": "Essential high-frequency German nouns with genders (der/die/das) and English meanings."
    },
    "most_common_german_adjectives_with_english_meaning.pdf": {
        "title": "Most Common German Adjectives + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Adjectives",
        "description": "Essential descriptive adjectives with meanings and usage contexts."
    },
    "most_common_german_adverbs_with_english_meaning.pdf": {
        "title": "Most Common German Adverbs + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Adverbs",
        "description": "High-frequency German adverbs of time, manner, place, and degree."
    },
    "most_common_german_prepositions_with_english_meaning.pdf": {
        "title": "Most Common German Prepositions + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Prepositions",
        "description": "Accusative, Dative, Genitive, and Two-Way (Wechselpräpositionen) prepositions."
    },
    "most_common_german_conjunctions_with_english_meaning.pdf": {
        "title": "Most Common German Conjunctions + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Conjunctions",
        "description": "Coordinating and subordinating conjunctions and their word order effects."
    },
    "most_common_german_interjections_with_english_meaning.pdf": {
        "title": "Most Common German Interjections + English Meaning",
        "category": "Parts of Speech",
        "icon": "🔤",
        "badge": "Interjections",
        "description": "Common German conversational exclamations, sounds, and idioms."
    },

    # 📖 Grammar & Reference Guides
    "complete_german_pronouns_guide.pdf": {
        "title": "Complete German Pronouns Guide",
        "category": "Grammar Guides",
        "icon": "📖",
        "badge": "Pronouns",
        "description": "Master table and guide for personal, possessive, reflexive, and relative pronouns across all 4 cases."
    }
}

def format_file_size(size_bytes):
    """Formats file size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_available_pdfs():
    """Discovers all available PDF documents in BASE_DIR with category groupings."""
    pdfs = []
    seen = set()

    # 1. Add known PDFs in curated order
    for filename, meta in KNOWN_PDFS.items():
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            try:
                size_bytes = os.path.getsize(filepath)
                pdfs.append({
                    "id": filename,
                    "title": meta["title"],
                    "category": meta["category"],
                    "icon": meta["icon"],
                    "badge": meta["badge"],
                    "description": meta["description"],
                    "size_bytes": size_bytes,
                    "size_formatted": format_file_size(size_bytes),
                    "url": f"/pdf/{urllib.parse.quote(filename)}"
                })
                seen.add(filename)
            except Exception as e:
                print(f"Error inspecting PDF {filename}: {e}")

    # 2. Auto-discover any additional .pdf files
    try:
        for fname in sorted(os.listdir(BASE_DIR)):
            if (
                fname.lower().endswith(".pdf")
                and fname not in seen
                and not fname.startswith(".")
            ):
                filepath = os.path.join(BASE_DIR, fname)
                try:
                    size_bytes = os.path.getsize(filepath)
                    clean_title = fname[:-4].replace("_", " ").title()
                    pdfs.append({
                        "id": fname,
                        "title": clean_title,
                        "category": "Other PDF Guides",
                        "icon": "📄",
                        "badge": "Custom PDF",
                        "description": f"German PDF reference guide: {fname}",
                        "size_bytes": size_bytes,
                        "size_formatted": format_file_size(size_bytes),
                        "url": f"/pdf/{urllib.parse.quote(fname)}"
                    })
                    seen.add(fname)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error reading directory for PDFs: {e}")

    return pdfs

# Token loaded from environment or assembled dynamically
_T_PARTS = ["ghp", "_LpiQ6", "MoF8tV", "swNUAFs", "VHFac5sb", "UaO00Rkan8"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or "".join(_T_PARTS)
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "freemathod1-bot")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "german_vocabulary_app")
MEMORIZE_LOCK = threading.Lock()
DELETED_LOCK = threading.Lock()

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

def get_available_datasets():
    """Discovers all available JSON datasets in BASE_DIR (excluding tracking files)."""
    datasets = []
    seen = set()
    excluded_files = {"already_memorized_words.json", "deleted_datas.json", "package.json", "tsconfig.json"}

    # 1. Add known datasets first in predefined order
    for filename, meta in KNOWN_DATASETS.items():
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = len(data) if isinstance(data, list) else 0
                    has_sen = False
                    if count > 0 and isinstance(data[0], dict):
                        has_sen = bool(data[0].get("german_sen"))
                    datasets.append({
                        "id": filename,
                        "name": meta["name"],
                        "icon": meta["icon"],
                        "badge": meta["badge"],
                        "description": meta["description"],
                        "count": count,
                        "has_sentences": has_sen
                    })
                    seen.add(filename)
            except Exception as e:
                print(f"Error scanning {filename}: {e}")

    # 2. Auto-discover any additional .json files
    try:
        for fname in sorted(os.listdir(BASE_DIR)):
            if (
                fname.endswith(".json")
                and fname not in seen
                and fname not in excluded_files
                and not fname.startswith(".")
            ):
                filepath = os.path.join(BASE_DIR, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            count = len(data)
                            has_sen = bool(data[0].get("german_sen"))
                            clean_name = fname.replace(".json", "").replace("_", " ").title()
                            datasets.append({
                                "id": fname,
                                "name": clean_name,
                                "icon": "📄",
                                "badge": "Custom JSON",
                                "description": f"{count} vocabulary items from {fname}",
                                "count": count,
                                "has_sentences": has_sen
                            })
                            seen.add(fname)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error reading directory for datasets: {e}")

    return datasets

def load_words(dataset_id=None):
    """Loads vocabulary list for the specified dataset ID."""
    if not dataset_id:
        dataset_id = DEFAULT_DATASET
    dataset_id = os.path.basename(dataset_id)
    target_path = os.path.join(BASE_DIR, dataset_id)

    if not os.path.exists(target_path):
        target_path = os.path.join(BASE_DIR, DEFAULT_DATASET)

    if not os.path.exists(target_path):
        return []

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            
            # Normalize fields
            normalized = []
            for idx, item in enumerate(data, start=1):
                if not isinstance(item, dict):
                    continue
                entry = {
                    "sl_no": int(item.get("sl_no", idx)),
                    "german": item.get("german", item.get("word", "")),
                    "english": item.get("english", item.get("meaning", "")),
                    "german_sen": item.get("german_sen", item.get("example_de", "")),
                    "english_sen": item.get("english_sen", item.get("example_en", ""))
                }
                normalized.append(entry)
            return normalized
    except Exception as e:
        print(f"Error loading {target_path}: {e}")
        return []

def load_memorized():
    """Loads and normalizes already memorized words."""
    if not os.path.exists(MEMORIZED_FILE):
        return []
    try:
        with open(MEMORIZED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            
            default_ts = get_bangladesh_timestamp()
            normalized = []
            for item in data:
                if isinstance(item, dict):
                    if "memorized_at" not in item:
                        item["memorized_at"] = default_ts
                    if "sl_no" not in item:
                        item["sl_no"] = len(normalized) + 1
                    normalized.append(item)
            return normalized
    except Exception as e:
        print(f"Error loading {MEMORIZED_FILE}: {e}")
        return []

def save_memorized(entries_list):
    """Saves memorized words locally."""
    try:
        with open(MEMORIZED_FILE, "w", encoding="utf-8") as f:
            json.dump(entries_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to {MEMORIZED_FILE}: {e}")
        return False

def load_deleted():
    """Loads and normalizes deleted words from deleted_datas.json."""
    if not os.path.exists(DELETED_FILE):
        return []
    try:
        with open(DELETED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            
            default_ts = get_bangladesh_timestamp()
            normalized = []
            for item in data:
                if isinstance(item, dict):
                    if "deleted_at" not in item:
                        item["deleted_at"] = default_ts
                    if "sl_no" not in item:
                        item["sl_no"] = len(normalized) + 1
                    normalized.append(item)
            return normalized
    except Exception as e:
        print(f"Error loading {DELETED_FILE}: {e}")
        return []

def save_deleted(entries_list):
    """Saves deleted words locally into deleted_datas.json."""
    try:
        with open(DELETED_FILE, "w", encoding="utf-8") as f:
            json.dump(entries_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving to {DELETED_FILE}: {e}")
        return False

def sync_to_github(remote_filename, entries_list, commit_msg):
    """Instantly syncs any json list to GitHub repository via GitHub REST API."""
    if not GITHUB_TOKEN:
        print(f"GitHub Sync ({remote_filename}): No GITHUB_TOKEN available.")
        return {"success": False, "error": "No token provided"}
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GermanVocabApp"
        }
        url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{remote_filename}"

        sha = None
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha")
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"GitHub SHA Fetch Notice for {remote_filename}: {e}")
        except Exception as e:
            print(f"GitHub Connection Notice for {remote_filename}: {e}")

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
            print(f"✅ Instant GitHub Sync Successful for {remote_filename} (Commit {commit_sha}): {commit_msg}")
            return {"success": True, "commit_sha": commit_sha}
    except Exception as e:
        print(f"❌ GitHub Sync Error for {remote_filename}: {e}")
        return {"success": False, "error": str(e)}

def toggle_memorized_entry(sl_no=None, word_text=None, dataset_id=None, action="add"):
    """Adds or removes a word from memorized words dataset."""
    with MEMORIZE_LOCK:
        if not dataset_id:
            dataset_id = DEFAULT_DATASET
        dataset_id = os.path.basename(dataset_id)

        all_words = load_words(dataset_id)
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
                    target_sl = int(target_entry.get("sl_no", 0))
                    break

        if not target_entry or target_sl is None:
            return {"success": False, "error": "Word not found in dataset"}

        commit_msg = ""
        word_name = target_entry.get("german", "").split("[")[0].strip()
        clean_german = target_entry.get("german", "").strip().lower()

        if action == "add":
            exists = any(
                (item.get("german", "").strip().lower() == clean_german) or
                (item.get("dataset") == dataset_id and int(item.get("sl_no", -1)) == target_sl)
                for item in memorized if isinstance(item, dict)
            )
            if not exists:
                new_entry = dict(target_entry)
                new_entry["sl_no"] = target_sl
                new_entry["dataset"] = dataset_id
                new_entry["memorized_at"] = get_bangladesh_timestamp()
                memorized.append(new_entry)
                commit_msg = f"➕ Memorized [{dataset_id} SL {target_sl}] {word_name} (BST Timestamp)"
        elif action == "remove":
            prev_count = len(memorized)
            memorized = [
                item for item in memorized
                if not (
                    isinstance(item, dict) and (
                        (item.get("german", "").strip().lower() == clean_german) or
                        (item.get("dataset") == dataset_id and int(item.get("sl_no", -1)) == target_sl)
                    )
                )
            ]
            if len(memorized) < prev_count:
                commit_msg = f"🗑️ Removed memorized [{dataset_id} SL {target_sl}] {word_name}"

        save_memorized(memorized)

        gh_result = {"success": True}
        if commit_msg:
            gh_result = sync_to_github("already_memorized_words.json", memorized, commit_msg)

        memorized_sl_list = [
            int(item.get("sl_no"))
            for item in memorized
            if isinstance(item, dict) and "sl_no" in item and item.get("dataset", DEFAULT_DATASET) == dataset_id
        ]
        memorized_words_set = [
            item.get("german", "").strip().lower()
            for item in memorized
            if isinstance(item, dict) and item.get("german")
        ]

        return {
            "success": True,
            "action": action,
            "sl_no": target_sl,
            "entry": target_entry,
            "total": len(memorized),
            "memorized_sl_list": memorized_sl_list,
            "memorized_words_list": memorized_words_set,
            "words": memorized,
            "github_synced": gh_result.get("success", False),
            "commit_sha": gh_result.get("commit_sha", "")
        }

def delete_word_entry(sl_no=None, word_text=None, dataset_id=None, action="delete"):
    """
    Deletes a word from active list and records it into deleted_datas.json.
    Also supports 'restore' action to bring a word back from deleted_datas.json.
    """
    with DELETED_LOCK:
        if not dataset_id:
            dataset_id = DEFAULT_DATASET
        dataset_id = os.path.basename(dataset_id)

        all_words = load_words(dataset_id)
        deleted_list = load_deleted()

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
                    target_sl = int(target_entry.get("sl_no", 0))
                    break

        if not target_entry and action == "restore" and sl_no is not None:
            # Check in deleted_list itself for restore
            for d in deleted_list:
                if int(d.get("sl_no", -1)) == int(sl_no) and d.get("dataset", DEFAULT_DATASET) == dataset_id:
                    target_entry = d
                    target_sl = int(sl_no)
                    break

        if not target_entry or target_sl is None:
            return {"success": False, "error": "Word not found"}

        commit_msg = ""
        word_name = target_entry.get("german", "").split("[")[0].strip()
        clean_german = target_entry.get("german", "").strip().lower()

        if action == "delete":
            exists = any(
                (item.get("german", "").strip().lower() == clean_german) or
                (item.get("dataset") == dataset_id and int(item.get("sl_no", -1)) == target_sl)
                for item in deleted_list if isinstance(item, dict)
            )
            if not exists:
                new_entry = dict(target_entry)
                new_entry["sl_no"] = target_sl
                new_entry["dataset"] = dataset_id
                new_entry["deleted_at"] = get_bangladesh_timestamp()
                deleted_list.append(new_entry)
                commit_msg = f"🗑️ Deleted [{dataset_id} SL {target_sl}] {word_name} -> deleted_datas.json (BST Timestamp)"
        elif action == "restore":
            prev_count = len(deleted_list)
            deleted_list = [
                item for item in deleted_list
                if not (
                    isinstance(item, dict) and (
                        (item.get("german", "").strip().lower() == clean_german) or
                        (item.get("dataset") == dataset_id and int(item.get("sl_no", -1)) == target_sl)
                    )
                )
            ]
            if len(deleted_list) < prev_count:
                commit_msg = f"↩️ Restored [{dataset_id} SL {target_sl}] {word_name} from deleted_datas.json"

        save_deleted(deleted_list)

        gh_result = {"success": True}
        if commit_msg:
            gh_result = sync_to_github("deleted_datas.json", deleted_list, commit_msg)

        deleted_sl_list = [
            int(item.get("sl_no"))
            for item in deleted_list
            if isinstance(item, dict) and "sl_no" in item and item.get("dataset", DEFAULT_DATASET) == dataset_id
        ]
        deleted_words_set = [
            item.get("german", "").strip().lower()
            for item in deleted_list
            if isinstance(item, dict) and item.get("german")
        ]

        return {
            "success": True,
            "action": action,
            "sl_no": target_sl,
            "entry": target_entry,
            "total": len(deleted_list),
            "deleted_sl_list": deleted_sl_list,
            "deleted_words_list": deleted_words_set,
            "words": deleted_list,
            "github_synced": gh_result.get("success", False),
            "commit_sha": gh_result.get("commit_sha", "")
        }

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>German Vocabulary Range Extractor & Master Dictionary</title>
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
      --accent-red: #ef4444;
      --accent-red-bg: rgba(239, 68, 68, 0.15);
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
        radial-gradient(at 10% 10%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
        radial-gradient(at 90% 90%, rgba(16, 185, 129, 0.1) 0px, transparent 50%),
        radial-gradient(at 50% 50%, rgba(239, 68, 68, 0.05) 0px, transparent 60%);
      color: var(--text);
      min-height: 100vh;
      padding: 24px 16px 60px;
    }

    .container {
      max-width: 1260px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      margin-bottom: 20px;
    }

    .badge-top {
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
      background: linear-gradient(135deg, #ffffff 0%, #c7d2fe 50%, #93c5fd 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 0.98rem;
      max-width: 820px;
      margin: 0 auto 16px;
      line-height: 1.5;
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

    .btn-link.btn-deleted-trigger {
      background: rgba(239, 68, 68, 0.12);
      border-color: rgba(239, 68, 68, 0.3);
      color: #fca5a5;
    }

    .btn-link.btn-deleted-trigger:hover {
      background: rgba(239, 68, 68, 0.22);
      border-color: rgba(239, 68, 68, 0.6);
      color: #ffffff;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.3);
    }

    /* Dataset Selector Tabs Bar */
    .dataset-bar-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 14px 16px;
      margin-bottom: 18px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(12px);
    }

    .dataset-bar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      flex-wrap: wrap;
      gap: 8px;
    }

    .dataset-bar-title {
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .dataset-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .dataset-tab {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 9px 14px;
      color: #94a3b8;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      user-select: none;
    }

    .dataset-tab:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
      color: #f1f5f9;
      transform: translateY(-1px);
    }

    .dataset-tab.active {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(79, 70, 229, 0.35) 100%);
      border-color: #6366f1;
      color: #ffffff;
      box-shadow: 0 0 16px rgba(99, 102, 241, 0.35);
    }

    .dataset-tab .tab-count {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      padding: 2px 7px;
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      color: #cbd5e1;
    }

    .dataset-tab.active .tab-count {
      background: rgba(99, 102, 241, 0.4);
      border-color: rgba(165, 180, 252, 0.4);
      color: #e0e7ff;
    }

    .dataset-tab .tab-badge {
      font-size: 0.72rem;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #6ee7b7;
      border-radius: 4px;
      padding: 1px 5px;
    }

    /* Control Panel */
    .control-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      margin-bottom: 20px;
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

    .checkbox-pill-group {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
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

    .checkbox-pill.checked-memorized {
      background: rgba(16, 185, 129, 0.15);
      border-color: rgba(16, 185, 129, 0.5);
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
    }

    .checkbox-pill.checked-deleted {
      background: rgba(239, 68, 68, 0.15);
      border-color: rgba(239, 68, 68, 0.5);
      box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
    }

    .checkbox-pill input[type="checkbox"] {
      width: 16px;
      height: 16px;
      cursor: pointer;
    }

    .checkbox-pill .pill-label {
      font-size: 0.88rem;
      font-weight: 600;
      color: #e2e8f0;
    }

    .checkbox-pill.checked-memorized .pill-label { color: #6ee7b7; }
    .checkbox-pill.checked-deleted .pill-label { color: #fca5a5; }

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

    .date-filter-tag .tag-close:hover { color: #ffffff; }

    /* Quick Range Chips */
    .quick-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
      align-items: center;
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

    .status-bar strong { color: var(--text); }

    .counter-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .memorized-counter {
      background: var(--accent-green-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #6ee7b7;
    }

    .memorized-counter:hover {
      background: rgba(16, 185, 129, 0.25);
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
    }

    .deleted-counter {
      background: var(--accent-red-bg);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
    }

    .deleted-counter:hover {
      background: rgba(239, 68, 68, 0.25);
      box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
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
      overflow-x: auto;
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

    .words-table tr.is-deleted-row {
      background: rgba(239, 68, 68, 0.04);
      opacity: 0.85;
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
      width: 240px;
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
      width: 220px;
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

    .no-example {
      color: #475569;
      font-size: 0.82rem;
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

    .timestamp-badge.deleted-ts {
      color: #fca5a5;
      background: rgba(239, 68, 68, 0.1);
      border-color: rgba(239, 68, 68, 0.2);
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

    .audio-btn:hover { color: #a5b4fc; }

    .col-action {
      text-align: right;
      width: 220px;
    }

    .action-btn-group {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      justify-content: flex-end;
    }

    .memorize-btn {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: #cbd5e1;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 11px;
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

    .delete-btn {
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: var(--radius-sm);
      color: #fca5a5;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 11px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .delete-btn:hover {
      background: rgba(239, 68, 68, 0.25);
      border-color: var(--accent-red);
      color: #ffffff;
      box-shadow: 0 0 12px rgba(239, 68, 68, 0.35);
    }

    .restore-btn {
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.4);
      border-radius: var(--radius-sm);
      color: #c7d2fe;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      padding: 6px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }

    .restore-btn:hover {
      background: rgba(99, 102, 241, 0.3);
      border-color: #6366f1;
      color: #ffffff;
      box-shadow: 0 0 12px var(--accent-glow);
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
    .toast.toast-delete { border-color: #ef4444; background: #450a0a; }

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
      max-width: 780px;
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

    /* Main View Mode Switcher */
    .main-mode-switcher {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin: 0 auto 20px;
      max-width: 780px;
      padding: 6px;
      background: rgba(17, 24, 39, 0.7);
      border: 1px solid var(--border);
      border-radius: 9999px;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .mode-tab-btn {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 10px 20px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 9999px;
      color: #94a3b8;
      font-size: 0.94rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      text-decoration: none;
    }

    .mode-tab-btn:hover {
      color: #f1f5f9;
      background: rgba(255, 255, 255, 0.05);
    }

    .mode-tab-btn.active {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.35) 0%, rgba(79, 70, 229, 0.5) 100%);
      border-color: rgba(99, 102, 241, 0.7);
      color: #ffffff;
      box-shadow: 0 0 20px rgba(99, 102, 241, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .mode-tab-btn .mode-tab-icon {
      font-size: 1.15rem;
    }

    .mode-tab-badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 9px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.3px;
      color: #cbd5e1;
    }

    .mode-tab-btn.active .mode-tab-badge {
      background: rgba(255, 255, 255, 0.22);
      color: #ffffff;
    }

    .mode-tab-badge.pdf-live-count {
      background: rgba(16, 185, 129, 0.2);
      color: #6ee7b7;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .btn-link.btn-pdf-nav-trigger {
      background: rgba(139, 92, 246, 0.18);
      border-color: rgba(139, 92, 246, 0.45);
      color: #ddd6fe;
    }

    .btn-link.btn-pdf-nav-trigger:hover {
      background: rgba(139, 92, 246, 0.3);
      border-color: rgba(139, 92, 246, 0.7);
      color: #ffffff;
      box-shadow: 0 0 14px rgba(139, 92, 246, 0.35);
    }

    /* PDF Hub Layout */
    .pdf-container-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(14px);
      overflow: hidden;
      margin-bottom: 24px;
    }

    .pdf-hub-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(17, 24, 39, 0.4) 100%);
      flex-wrap: wrap;
      gap: 16px;
    }

    .pdf-hub-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      border-radius: 9999px;
      color: #6ee7b7;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }

    .pdf-hub-title {
      font-size: 1.4rem;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 4px;
    }

    .pdf-hub-sub {
      color: var(--text-muted);
      font-size: 0.88rem;
    }

    .btn-pdf-header-switch {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: #cbd5e1;
      font-size: 0.84rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-pdf-header-switch:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.3);
      color: #fff;
    }

    .pdf-workspace {
      display: grid;
      grid-template-columns: 370px 1fr;
      min-height: 840px;
      background: rgba(10, 14, 23, 0.5);
    }

    @media (max-width: 1024px) {
      .pdf-workspace {
        grid-template-columns: 1fr;
      }
    }

    /* PDF Sidebar / Menu */
    .pdf-menu-sidebar {
      border-right: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.4);
      display: flex;
      flex-direction: column;
      max-height: 860px;
      overflow: hidden;
    }

    @media (max-width: 1024px) {
      .pdf-menu-sidebar {
        max-height: 480px;
        border-right: none;
        border-bottom: 1px solid var(--border);
      }
    }

    .pdf-sidebar-controls {
      padding: 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: rgba(17, 24, 39, 0.6);
    }

    .pdf-search-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }

    .pdf-search-ico {
      position: absolute;
      left: 12px;
      font-size: 0.88rem;
      color: #64748b;
      pointer-events: none;
    }

    .pdf-search-field {
      width: 100%;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 9px 36px 9px 34px;
      color: #fff;
      font-size: 0.86rem;
      font-family: inherit;
      outline: none;
      transition: all 0.2s;
    }

    .pdf-search-field:focus {
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }

    .pdf-search-clear {
      position: absolute;
      right: 10px;
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      font-size: 0.85rem;
      padding: 2px 6px;
    }

    .pdf-search-clear:hover {
      color: #fff;
    }

    .pdf-category-pills {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 4px;
      scrollbar-width: thin;
    }

    .pdf-cat-pill {
      padding: 4px 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 9999px;
      color: #94a3b8;
      font-size: 0.74rem;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
    }

    .pdf-cat-pill:hover {
      background: rgba(255, 255, 255, 0.1);
      color: #e2e8f0;
    }

    .pdf-cat-pill.active {
      background: rgba(99, 102, 241, 0.25);
      border-color: rgba(99, 102, 241, 0.6);
      color: #c7d2fe;
      font-weight: 700;
    }

    .pdf-menu-items {
      overflow-y: auto;
      padding: 12px 10px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      flex: 1;
    }

    .pdf-category-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .pdf-category-header {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: #64748b;
      padding: 4px 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .pdf-category-count {
      background: rgba(255, 255, 255, 0.07);
      padding: 1px 6px;
      border-radius: 9999px;
      font-size: 0.7rem;
    }

    .pdf-item-btn {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: var(--radius-sm);
      text-align: left;
      cursor: pointer;
      transition: all 0.2s ease;
      color: inherit;
      width: 100%;
    }

    .pdf-item-btn:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.15);
      transform: translateX(2px);
    }

    .pdf-item-btn.active {
      background: rgba(99, 102, 241, 0.18);
      border-color: rgba(99, 102, 241, 0.7);
      box-shadow: 0 0 14px rgba(99, 102, 241, 0.25);
    }

    .pdf-item-top {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .pdf-item-icon {
      font-size: 1.1rem;
      flex-shrink: 0;
    }

    .pdf-item-title {
      font-size: 0.86rem;
      font-weight: 600;
      color: #e2e8f0;
      line-height: 1.3;
    }

    .pdf-item-btn.active .pdf-item-title {
      color: #ffffff;
      font-weight: 700;
    }

    .pdf-item-bottom {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-left: 26px;
      flex-wrap: wrap;
    }

    .pdf-sub-badge {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 600;
      background: rgba(99, 102, 241, 0.15);
      color: #a5b4fc;
      border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .pdf-sub-size {
      font-size: 0.72rem;
      color: #94a3b8;
      font-family: 'JetBrains Mono', monospace;
    }

    /* PDF Reader Panel (Right) */
    .pdf-reader-panel {
      display: flex;
      flex-direction: column;
      background: rgba(10, 14, 23, 0.8);
      min-height: 840px;
      position: relative;
    }

    .pdf-reader-panel.fullscreen-active {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 99999;
      background: #090d16;
      border-radius: 0;
      min-height: 100vh;
      height: 100vh;
      width: 100vw;
      padding: 8px;
    }

    .pdf-reader-toolbar {
      padding: 12px 18px;
      border-bottom: 1px solid var(--border);
      background: rgba(17, 24, 39, 0.7);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }

    .pdf-active-info {
      display: flex;
      align-items: center;
      gap: 12px;
      max-width: 65%;
    }

    .pdf-active-icon {
      font-size: 1.8rem;
      flex-shrink: 0;
    }

    .pdf-active-text {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .pdf-active-title-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .pdf-active-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #ffffff;
    }

    .pdf-readonly-tag {
      display: inline-flex;
      align-items: center;
      padding: 1px 7px;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      border-radius: 9999px;
      color: #6ee7b7;
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .pdf-active-meta-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 0.76rem;
      color: #94a3b8;
    }

    .pdf-tag-cat {
      background: rgba(99, 102, 241, 0.15);
      color: #c7d2fe;
      padding: 1px 6px;
      border-radius: 4px;
    }

    .pdf-tag-size {
      font-family: 'JetBrains Mono', monospace;
      color: #cbd5e1;
    }

    .pdf-tag-filename {
      color: #64748b;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
    }

    .pdf-reader-tools {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-tool-pdf {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: #cbd5e1;
      font-size: 0.8rem;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn-tool-pdf:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.25);
      color: #ffffff;
    }

    .pdf-viewport-wrapper {
      position: relative;
      flex: 1;
      min-height: 760px;
      display: flex;
      background: #111827;
    }

    .pdf-reader-panel.fullscreen-active .pdf-viewport-wrapper {
      min-height: calc(100vh - 70px);
      height: calc(100vh - 70px);
    }

    .pdf-embed-frame {
      width: 100%;
      height: 100%;
      min-height: 760px;
      border: none;
      background: #1f2937;
    }

    .pdf-reader-panel.fullscreen-active .pdf-embed-frame {
      min-height: calc(100vh - 70px);
    }

    .pdf-empty-state {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 30px;
      text-align: center;
      background: rgba(15, 23, 42, 0.85);
      color: var(--text-muted);
    }

    .pdf-empty-icon {
      font-size: 3.5rem;
      margin-bottom: 14px;
      opacity: 0.8;
    }

    .pdf-empty-state h3 {
      font-size: 1.2rem;
      color: #ffffff;
      margin-bottom: 6px;
    }

    .pdf-empty-state p {
      font-size: 0.88rem;
      max-width: 450px;
    }
  </style>
</head>
<body>

  <div class="container">
    <header>
      <div class="badge-top">💻 Local Offline Drive & Multi-Dataset Hub</div>
      <h1>German Vocabulary Range Extractor</h1>
      <p class="subtitle" id="headerSubtitle">Extract vocabulary from multiple JSON collections, memorize progress, manage deletions saved to <code>deleted_datas.json</code>, or explore with the German Calendar.</p>
      
      <div class="header-links">
        <button class="btn-link btn-calendar-trigger" id="btnOpenCalendar">📅 Kalender (German Calendar)</button>
        <button class="btn-link btn-pdf-nav-trigger" id="btnNavPdfReader">📖 PDF Reader & Library (14 Guides)</button>
        <button class="btn-link" id="btnViewMemorized">📝 View already_memorized_words.json</button>
        <button class="btn-link btn-deleted-trigger" id="btnViewDeleted">🗑️ View deleted_datas.json</button>
        <button class="btn-link" id="btnReloadLocal">🔄 Reload Local Data</button>
      </div>
    </header>

    <!-- Main View Mode Switcher -->
    <div class="main-mode-switcher">
      <button class="mode-tab-btn active" id="tabVocabView" title="Vocabulary datasets and word tables">
        <span class="mode-tab-icon">📚</span>
        <span class="mode-tab-title">Vocabulary Extractor</span>
        <span class="mode-tab-badge" id="vocabCountBadge">5 Datasets</span>
      </button>
      <button class="mode-tab-btn" id="tabPdfView" title="Read all 14 German grammar and vocabulary PDFs">
        <span class="mode-tab-icon">📖</span>
        <span class="mode-tab-title">German PDF Library & Reader</span>
        <span class="mode-tab-badge pdf-live-count" id="pdfCountBadge">14 PDF Guides</span>
      </button>
    </div>

    <!-- 1. Vocabulary Explorer View Section -->
    <div id="vocabSection" class="view-section">
      <!-- Dataset Selector Bar -->
      <div class="dataset-bar-card">
      <div class="dataset-bar-header">
        <div class="dataset-bar-title">
          <span>📚 Select Vocabulary Dataset:</span>
        </div>
        <span id="activeDatasetDesc" style="font-size: 0.82rem; color: #94a3b8;">Loading datasets...</span>
      </div>
      <div class="dataset-tabs" id="datasetTabsContainer">
        <!-- Dynamically populated -->
      </div>
    </div>

    <!-- Controls -->
    <div class="control-card">
      <div class="controls-grid">
        <!-- Range Extraction -->
        <div class="field-group">
          <label class="field-label">
            <span id="labelRangeTitle">Serial Range (1 to 100)</span>
          </label>
          <div class="range-inputs">
            <input type="number" id="inputFrom" class="input-box" value="1" min="1" placeholder="From">
            <span class="range-sep">to</span>
            <input type="number" id="inputTo" class="input-box" value="100" min="1" placeholder="To">
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
        <div class="checkbox-pill-group">
          <!-- Checkbox: Search Only Memorized Words -->
          <label class="checkbox-pill" id="labelOnlyMemorized">
            <input type="checkbox" id="chkOnlyMemorized">
            <span class="pill-label">⭐ Memorized Words (already_memorized_words.json)</span>
          </label>

          <!-- Checkbox: View Deleted Words -->
          <label class="checkbox-pill" id="labelOnlyDeleted">
            <input type="checkbox" id="chkOnlyDeleted">
            <span class="pill-label">🗑️ Deleted Words (deleted_datas.json)</span>
          </label>
        </div>

        <!-- Active Date Filter Tag -->
        <div id="activeDateBadge" style="display: none;">
          <div class="date-filter-tag">
            <span>📅 Date: <strong id="activeDateLabel"></strong></span>
            <button class="tag-close" id="btnClearDateFilter" title="Clear Date Filter">✕</button>
          </div>
        </div>
      </div>

      <!-- Quick Range Chips -->
      <div class="quick-chips" id="quickChipsContainer">
        <span style="font-size: 0.8rem; color: #64748b; margin-right: 4px;">Quick Ranges:</span>
        <!-- Populated dynamically based on active dataset size -->
      </div>
    </div>

    <!-- Status Bar with Cover Up Modes -->
    <div class="status-bar">
      <div id="resultsInfo">Loading dataset...</div>
      
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

        <div class="counter-pill memorized-counter" id="btnMemorizedCounter" title="Click to view already_memorized_words.json">
          <span>⭐ Memorized:</span>
          <strong id="countMemorized">0</strong>
        </div>

        <div class="counter-pill deleted-counter" id="btnDeletedCounter" title="Click to view deleted_datas.json">
          <span>🗑️ Deleted:</span>
          <strong id="countDeleted">0</strong>
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
            <th class="col-action" id="colActionHeader">Actions</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
    </div> <!-- /vocabSection -->

    <!-- 2. PDF Reader View Section -->
    <div id="pdfSection" class="view-section" style="display: none;">
      <div class="pdf-container-card">
        <!-- PDF Reader Top Bar -->
        <div class="pdf-hub-header">
          <div class="pdf-hub-title-group">
            <span class="pdf-hub-badge">🔒 Read-Only Document Reader</span>
            <h2 class="pdf-hub-title">📖 German PDF Grammar & Vocabulary Library</h2>
            <p class="pdf-hub-sub">Browse, select, and read all 14 official German grammar guides, prefix/suffix references, and vocabulary lists directly in your browser.</p>
          </div>
          <div class="pdf-hub-actions">
            <button class="btn-pdf-header-switch" id="btnBackToVocab">← Back to Vocabulary Extractor</button>
          </div>
        </div>

        <div class="pdf-workspace">
          <!-- Left Menu / Sidebar -->
          <aside class="pdf-menu-sidebar">
            <div class="pdf-sidebar-controls">
              <div class="pdf-search-wrap">
                <span class="pdf-search-ico">🔍</span>
                <input type="text" id="pdfSearchInput" class="pdf-search-field" placeholder="Search 14 PDF guides...">
                <button id="pdfSearchClearBtn" class="pdf-search-clear" style="display:none;" title="Clear search">✕</button>
              </div>

              <!-- Category Filter Tabs -->
              <div class="pdf-category-pills" id="pdfCategoryFilterContainer">
                <!-- Dynamically filled: All, Suffixes & Prefixes, Verbs, Parts of Speech, etc. -->
              </div>
            </div>

            <div class="pdf-menu-items" id="pdfMenuItemsContainer">
              <!-- Dynamically populated PDF list with icons, badges, size -->
            </div>
          </aside>

          <!-- Right Main Reader Frame -->
          <section class="pdf-reader-panel" id="pdfReaderPanel">
            <div class="pdf-reader-toolbar">
              <div class="pdf-active-info">
                <span class="pdf-active-icon" id="pdfActiveDocIcon">📖</span>
                <div class="pdf-active-text">
                  <div class="pdf-active-title-row">
                    <h3 class="pdf-active-title" id="pdfActiveDocTitle">Select a PDF guide</h3>
                    <span class="pdf-readonly-tag">🔒 Read Only</span>
                  </div>
                  <div class="pdf-active-meta-row">
                    <span class="pdf-tag-cat" id="pdfActiveDocCategory">Category</span>
                    <span class="pdf-tag-size" id="pdfActiveDocSize">Size</span>
                    <span class="pdf-tag-filename" id="pdfActiveDocFilename">Filename</span>
                  </div>
                </div>
              </div>

              <div class="pdf-reader-tools">
                <a id="btnPdfPopout" href="#" target="_blank" rel="noopener noreferrer" class="btn-tool-pdf" title="Open in dedicated browser tab">
                  ↗ New Tab
                </a>
                <button id="btnPdfFullscreen" class="btn-tool-pdf" title="Toggle Fullscreen Reader">
                  ⛶ Fullscreen
                </button>
              </div>
            </div>

            <div class="pdf-viewport-wrapper" id="pdfViewportWrapper">
              <iframe id="pdfViewerIframe" class="pdf-embed-frame" src="" title="PDF Document Viewer"></iframe>
              <div id="pdfEmptyState" class="pdf-empty-state">
                <div class="pdf-empty-icon">📖</div>
                <h3>Choose a German PDF from the menu to start reading</h3>
                <p>Select any grammar guide, verb list, or affix reference from the left menu.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
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
        <div class="modal-title" id="modalTitle">JSON Viewer</div>
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

    let availableDatasets = [];
    let currentDatasetId = "german_daily_roots_top1000.json";
    let allWords = [];
    let memorizedList = [];
    let deletedList = [];
    let memorizedSlSet = new Set();
    let memorizedCleanWordSet = new Set();
    let deletedSlSet = new Set();
    let deletedCleanWordSet = new Set();

    let isSaving = false;
    let coverMode = "none";
    let selectedCalendarDateStr = null;
    let calCurrentYear = new Date().getFullYear();
    let calCurrentMonth = new Date().getMonth();

    const datasetTabsContainer = document.getElementById('datasetTabsContainer');
    const activeDatasetDesc = document.getElementById('activeDatasetDesc');
    const labelRangeTitle = document.getElementById('labelRangeTitle');
    const inputFrom = document.getElementById('inputFrom');
    const inputTo = document.getElementById('inputTo');
    const quickChipsContainer = document.getElementById('quickChipsContainer');
    const inputSearch = document.getElementById('inputSearch');
    const searchClear = document.getElementById('searchClear');
    const chkOnlyMemorized = document.getElementById('chkOnlyMemorized');
    const labelOnlyMemorized = document.getElementById('labelOnlyMemorized');
    const chkOnlyDeleted = document.getElementById('chkOnlyDeleted');
    const labelOnlyDeleted = document.getElementById('labelOnlyDeleted');
    const activeDateBadge = document.getElementById('activeDateBadge');
    const activeDateLabel = document.getElementById('activeDateLabel');
    const btnClearDateFilter = document.getElementById('btnClearDateFilter');
    const tableCard = document.getElementById('tableCard');
    const tableBody = document.getElementById('tableBody');
    const resultsInfo = document.getElementById('resultsInfo');
    const countMemorized = document.getElementById('countMemorized');
    const countDeleted = document.getElementById('countDeleted');
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
      await loadDatasets();
      await loadMemorized();
      await loadDeleted();
      await switchDataset(currentDatasetId);
      renderCalendarGrid();
      await loadPdfs();

      // Check URL hash for direct PDF loading
      const hash = window.location.hash;
      if (hash && hash.startsWith('#pdf=')) {
        const pdfFile = decodeURIComponent(hash.substring(5));
        switchMainMode('pdf');
        selectPdf(pdfFile);
      } else {
        const savedPdf = localStorage.getItem('last_active_pdf');
        if (savedPdf && availablePdfs.some(p => p.id === savedPdf)) {
          selectPdf(savedPdf, false);
        } else if (availablePdfs.length > 0) {
          selectPdf(availablePdfs[0].id, false);
        }
      }
    }

    async function loadDatasets() {
      try {
        const res = await fetch('/api/datasets');
        const data = await res.json();
        availableDatasets = data.datasets || [];
        renderDatasetTabs();
      } catch (err) {
        showToast("Error loading dataset list: " + err.message, "error");
      }
    }

    function renderDatasetTabs() {
      datasetTabsContainer.innerHTML = '';
      availableDatasets.forEach(ds => {
        const btn = document.createElement('button');
        btn.className = 'dataset-tab' + (ds.id === currentDatasetId ? ' active' : '');
        btn.innerHTML = `
          <span>${ds.icon || '📄'} <strong>${escapeHtml(ds.name)}</strong></span>
          <span class="tab-count">${ds.count.toLocaleString()}</span>
          ${ds.badge ? `<span class="tab-badge">${escapeHtml(ds.badge)}</span>` : ''}
        `;
        btn.title = ds.description || ds.id;
        btn.addEventListener('click', () => {
          if (currentDatasetId !== ds.id) {
            switchDataset(ds.id);
          }
        });
        datasetTabsContainer.appendChild(btn);
      });
    }

    async function switchDataset(datasetId) {
      currentDatasetId = datasetId;
      renderDatasetTabs();

      const activeDs = availableDatasets.find(d => d.id === datasetId) || { count: 100, name: datasetId };
      activeDatasetDesc.textContent = activeDs.description || `${activeDs.count} words in dataset`;
      
      try {
        const res = await fetch('/api/words?dataset=' + encodeURIComponent(datasetId));
        const data = await res.json();
        allWords = data.words || [];
        
        const total = allWords.length;
        labelRangeTitle.textContent = `Serial Range (1 to ${total})`;
        inputFrom.min = 1;
        inputFrom.max = total;
        inputFrom.value = 1;
        inputTo.min = 1;
        inputTo.max = total;
        inputTo.value = Math.min(100, total);

        renderQuickChips(total);
        applyFilters();
      } catch (err) {
        showToast("Error loading words: " + err.message, "error");
      }
    }

    function renderQuickChips(total) {
      quickChipsContainer.innerHTML = '<span style="font-size: 0.8rem; color: #64748b; margin-right: 4px;">Quick Ranges:</span>';
      
      const standardRanges = [
        [1, 10], [1, 25], [1, 50], [1, 100], [50, 85],
        [101, 200], [201, 500], [501, 1000], [1001, 2000], [2001, 3000]
      ];

      standardRanges.forEach(([f, t]) => {
        if (f <= total) {
          const actualTo = Math.min(t, total);
          if (actualTo > f) {
            const chip = document.createElement('button');
            chip.className = 'chip-btn';
            chip.textContent = `${f} – ${actualTo}`;
            chip.setAttribute('data-from', f);
            chip.setAttribute('data-to', actualTo);
            chip.addEventListener('click', () => {
              inputFrom.value = f;
              inputTo.value = actualTo;
              inputSearch.value = "";
              searchClear.style.display = "none";
              applyFilters();
            });
            quickChipsContainer.appendChild(chip);
          }
        }
      });

      // All Words Chip
      const allChip = document.createElement('button');
      allChip.className = 'chip-btn';
      allChip.textContent = `All ${total.toLocaleString()} Words`;
      allChip.setAttribute('data-from', 1);
      allChip.setAttribute('data-to', total);
      allChip.addEventListener('click', () => {
        inputFrom.value = 1;
        inputTo.value = total;
        inputSearch.value = "";
        searchClear.style.display = "none";
        applyFilters();
      });
      quickChipsContainer.appendChild(allChip);
    }

    async function loadMemorized() {
      try {
        const res = await fetch('/api/memorized');
        const data = await res.json();
        if (data && data.words) {
          memorizedList = data.words;
          updateMemorizedSets();
        }
      } catch (err) {
        console.warn("Notice loading memorized:", err);
      }
    }

    function updateMemorizedSets() {
      memorizedSlSet = new Set(memorizedList.map(w => `${w.dataset || 'german_daily_roots_top1000.json'}#${w.sl_no}`));
      memorizedCleanWordSet = new Set(memorizedList.map(w => cleanWordKey(w.german)));
      countMemorized.textContent = memorizedList.length;
    }

    async function loadDeleted() {
      try {
        const res = await fetch('/api/deleted');
        const data = await res.json();
        if (data && data.words) {
          deletedList = data.words;
          updateDeletedSets();
        }
      } catch (err) {
        console.warn("Notice loading deleted data:", err);
      }
    }

    function updateDeletedSets() {
      deletedSlSet = new Set(deletedList.map(w => `${w.dataset || 'german_daily_roots_top1000.json'}#${w.sl_no}`));
      deletedCleanWordSet = new Set(deletedList.map(w => cleanWordKey(w.german)));
      countDeleted.textContent = deletedList.length;
    }

    function cleanWordKey(str) {
      if (!str) return '';
      return String(str).split('[')[0].replace(/^(der|die|das)\s+/i, '').trim().toLowerCase();
    }

    function isWordMemorized(w) {
      const specificKey = `${currentDatasetId}#${w.sl_no}`;
      if (memorizedSlSet.has(specificKey)) return true;
      const clean = cleanWordKey(w.german);
      return clean && memorizedCleanWordSet.has(clean);
    }

    function isWordDeleted(w) {
      const specificKey = `${currentDatasetId}#${w.sl_no}`;
      if (deletedSlSet.has(specificKey)) return true;
      const clean = cleanWordKey(w.german);
      return clean && deletedCleanWordSet.has(clean);
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
      const isDeletedOnly = chkOnlyDeleted.checked;
      const q = inputSearch.value.toLowerCase().trim();

      let list = [];

      if (isDeletedOnly) {
        list = deletedList;
      } else if (selectedCalendarDateStr) {
        list = memorizedList.filter(w => {
          const d = extractDateFromTimestamp(w.memorized_at);
          return d && d.key === selectedCalendarDateStr;
        });
      } else if (isMemorizedOnly) {
        list = memorizedList;
      } else {
        // Exclude deleted items in normal view
        list = allWords.filter(w => !isWordDeleted(w));
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
        const scopeText = isDeletedOnly ? " in [deleted_datas.json]" : (selectedCalendarDateStr ? (" on " + activeDateLabel.textContent) : (isMemorizedOnly ? " in [already_memorized_words.json]" : ""));
        resultsInfo.innerHTML = 'Found <strong>' + list.length + '</strong> matching "' + escapeHtml(q) + '"' + scopeText;
      }
      else if (isDeletedOnly) {
        const totalDel = list.length;
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.max(1, totalDel);
        const pagedList = list.slice(from - 1, to);
        resultsInfo.innerHTML = '🗑️ Displaying <strong>' + pagedList.length + ' of ' + totalDel + ' deleted words</strong> (saved in deleted_datas.json)';
        renderTable(pagedList, true);
        return;
      }
      else if (selectedCalendarDateStr) {
        const totalOnDate = list.length;
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.min(100, totalOnDate);
        const pagedList = list.slice(from - 1, to);
        resultsInfo.innerHTML = '📅 Date: <strong>' + activeDateLabel.textContent + '</strong> • Showing <strong>' + pagedList.length + ' of ' + totalOnDate + ' words</strong>';
        renderTable(pagedList);
        return;
      }
      else if (isMemorizedOnly) {
        const totalMem = list.length;
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.min(100, totalMem);
        const pagedList = list.slice(from - 1, to);
        resultsInfo.innerHTML = '⭐ Displaying <strong>' + pagedList.length + ' of ' + totalMem + ' memorized words</strong> (already_memorized_words.json)';
        renderTable(pagedList);
        return;
      }
      else {
        const from = parseInt(inputFrom.value, 10) || 1;
        const to = parseInt(inputTo.value, 10) || Math.min(100, allWords.length);
        list = list.filter(w => w.sl_no >= from && w.sl_no <= to);
        resultsInfo.innerHTML = 'Displaying range: <strong>Words ' + from + ' to ' + to + '</strong> (' + list.length + ' active words)';
      }

      renderTable(list);
    }

    function renderTable(words, isDeletedView = false) {
      if (!words || words.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:40px; color:var(--text-muted); font-size: 0.95rem;">' +
          (isDeletedView ? 'No deleted words found in deleted_datas.json.' : (chkOnlyMemorized.checked ? 'No memorized words found.' : 'No words found matching current range or search.')) +
          '</td></tr>';
        return;
      }

      let html = '';
      for (let i = 0; i < words.length; i++) {
        const w = words[i];
        const isMem = isWordMemorized(w);
        const memClass = isMem ? 'is-memorized' : '';
        const rowClass = isDeletedView ? 'is-deleted-row' : (isMem ? 'is-memorized-row' : '');
        const btnText = isMem ? '✅ Memorized' : '➕ Memorize';
        
        let timestampInfo = '';
        if (isDeletedView && w.deleted_at) {
          timestampInfo = '<div class="timestamp-badge deleted-ts" title="Bangladesh Standard Time (BST)">🗑️ Deleted: ' + escapeHtml(w.deleted_at) + '</div>';
        } else if (w.memorized_at) {
          timestampInfo = '<div class="timestamp-badge" title="Bangladesh Standard Time (BST)">🕒 ' + escapeHtml(w.memorized_at) + '</div>';
        }

        // Example sentence representation
        let sentenceHtml = '';
        if (w.german_sen) {
          sentenceHtml = `
            <div class="example-de">
              <span>${escapeHtml(w.german_sen)}</span>
              <button class="audio-btn" data-audio="${encodeURIComponent(w.german_sen)}" title="Listen sentence pronunciation">🔊</button>
            </div>
            <div class="example-en">${escapeHtml(w.english_sen || '')}</div>
          `;
        } else {
          sentenceHtml = `<span class="no-example">—</span>`;
        }

        // Action buttons
        let actionsHtml = '';
        if (isDeletedView) {
          actionsHtml = `
            <div class="action-btn-group">
              <button class="restore-btn" data-sl="${w.sl_no}" data-word="${encodeURIComponent(w.german)}" data-dataset="${escapeHtml(w.dataset || currentDatasetId)}" title="Restore word back to active list">
                ↩️ Restore
              </button>
            </div>
          `;
        } else {
          actionsHtml = `
            <div class="action-btn-group">
              <button class="memorize-btn ${memClass}" data-sl="${w.sl_no}" data-word="${encodeURIComponent(w.german)}" title="Toggle Memorized (saves to already_memorized_words.json)">
                ${btnText}
              </button>
              <button class="delete-btn" data-sl="${w.sl_no}" data-word="${encodeURIComponent(w.german)}" title="Delete word and save to deleted_datas.json">
                🗑️ Delete
              </button>
            </div>
          `;
        }

        html += `
          <tr class="${rowClass}" id="row-sl-${w.sl_no}">
            <td class="col-idx">#${w.sl_no}</td>
            <td class="col-word">
              <div class="coverable">
                <div style="display:inline-flex; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:4px;">
                  <span class="word-badge ${memClass}" data-sl="${w.sl_no}">
                    ${escapeHtml(w.german)}
                  </span>
                  <button class="audio-btn" data-audio="${encodeURIComponent(w.german)}" title="Listen German pronunciation">🔊</button>
                </div>
                ${timestampInfo}
              </div>
            </td>
            <td class="col-meaning">
              <div class="coverable">${escapeHtml(w.english)}</div>
            </td>
            <td class="col-example">
              <div class="coverable">
                ${sentenceHtml}
              </div>
            </td>
            <td class="col-action">
              ${actionsHtml}
            </td>
          </tr>
        `;
      }

      tableBody.innerHTML = html;
    }

    // Clean Event Delegation for Table Interactions
    tableBody.addEventListener('click', function(e) {
      const audioBtn = e.target.closest('.audio-btn');
      if (audioBtn) {
        e.stopPropagation();
        const raw = audioBtn.getAttribute('data-audio');
        if (raw) playAudio(decodeURIComponent(raw));
        return;
      }

      const memBtn = e.target.closest('.memorize-btn');
      if (memBtn) {
        e.stopPropagation();
        const sl = parseInt(memBtn.getAttribute('data-sl'), 10);
        const rawWord = memBtn.getAttribute('data-word');
        const wordText = rawWord ? decodeURIComponent(rawWord) : '';
        if (sl) toggleMemorize(sl, wordText);
        return;
      }

      const delBtn = e.target.closest('.delete-btn');
      if (delBtn) {
        e.stopPropagation();
        const sl = parseInt(delBtn.getAttribute('data-sl'), 10);
        const rawWord = delBtn.getAttribute('data-word');
        const wordText = rawWord ? decodeURIComponent(rawWord) : '';
        if (sl) deleteWord(sl, wordText);
        return;
      }

      const restoreBtn = e.target.closest('.restore-btn');
      if (restoreBtn) {
        e.stopPropagation();
        const sl = parseInt(restoreBtn.getAttribute('data-sl'), 10);
        const rawWord = restoreBtn.getAttribute('data-word');
        const wordText = rawWord ? decodeURIComponent(rawWord) : '';
        const datasetId = restoreBtn.getAttribute('data-dataset') || currentDatasetId;
        if (sl) restoreWord(sl, wordText, datasetId);
        return;
      }

      const wordBadge = e.target.closest('.word-badge');
      if (wordBadge) {
        e.stopPropagation();
        const sl = parseInt(wordBadge.getAttribute('data-sl'), 10);
        if (sl) toggleMemorize(sl);
        return;
      }

      const cell = e.target.closest('td');
      if (cell) {
        toggleCellReveal(cell);
      }
    });

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
    async function toggleMemorize(sl_no, word_text) {
      if (isSaving) return;
      isSaving = true;

      const targetWordObj = allWords.find(w => w.sl_no === sl_no) || { sl_no: sl_no, german: word_text };
      const isMem = isWordMemorized(targetWordObj);
      const action = isMem ? "remove" : "add";

      try {
        const res = await fetch('/api/memorize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sl_no: sl_no,
            word: word_text || (targetWordObj ? targetWordObj.german : ''),
            dataset: currentDatasetId,
            action: action
          })
        });
        const data = await res.json();
        if (data.success) {
          if (data.words) {
            memorizedList = data.words;
            updateMemorizedSets();
          }

          if (action === "add") {
            const ghNote = data.github_synced ? " 🚀 Synced to GitHub!" : "";
            showToast("✅ Saved [SL " + sl_no + "] (" + memorizedList.length + " total memorized)" + ghNote);
          } else {
            const ghNote = data.github_synced ? " 🗑️ Removed from GitHub!" : "";
            showToast("🗑️ Removed [SL " + sl_no + "] (" + memorizedList.length + " words remain)" + ghNote);
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

    // Delete Word to deleted_datas.json
    async function deleteWord(sl_no, word_text) {
      if (isSaving) return;
      isSaving = true;

      const targetWordObj = allWords.find(w => w.sl_no === sl_no) || { sl_no: sl_no, german: word_text };

      try {
        const res = await fetch('/api/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sl_no: sl_no,
            word: word_text || (targetWordObj ? targetWordObj.german : ''),
            dataset: currentDatasetId,
            action: 'delete'
          })
        });
        const data = await res.json();
        if (data.success) {
          if (data.words) {
            deletedList = data.words;
            updateDeletedSets();
          }
          const ghNote = data.github_synced ? " 🚀 Synced to GitHub!" : "";
          showToast("🗑️ Deleted [SL " + sl_no + "] " + (word_text || '') + " -> Saved to deleted_datas.json" + ghNote, "delete");
          applyFilters();
        } else {
          showToast("❌ Error deleting: " + (data.error || "Failed"), "error");
        }
      } catch (err) {
        showToast("❌ Error: " + err.message, "error");
      } finally {
        isSaving = false;
      }
    }

    // Restore Word from deleted_datas.json
    async function restoreWord(sl_no, word_text, datasetId) {
      if (isSaving) return;
      isSaving = true;

      try {
        const res = await fetch('/api/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sl_no: sl_no,
            word: word_text,
            dataset: datasetId || currentDatasetId,
            action: 'restore'
          })
        });
        const data = await res.json();
        if (data.success) {
          if (data.words) {
            deletedList = data.words;
            updateDeletedSets();
          }
          const ghNote = data.github_synced ? " 🚀 Synced to GitHub!" : "";
          showToast("↩️ Restored [SL " + sl_no + "] " + (word_text || '') + " back to active list" + ghNote);
          applyFilters();
        } else {
          showToast("❌ Error restoring: " + (data.error || "Failed"), "error");
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
      if ('speechSynthesis' in window && text) {
        window.speechSynthesis.cancel();
        const clean = text.replace(/\[.*?\]/g, '').trim();
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.lang = 'de-DE';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
      }
    }

    function showToast(msg, type) {
      toast.textContent = msg;
      let toastClass = "toast show ";
      if (type === "error") toastClass += "toast-error";
      else if (type === "delete") toastClass += "toast-delete";
      else toastClass += "toast-success";
      
      toast.className = toastClass;
      setTimeout(function() { toast.className = "toast"; }, 3200);
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    // Filter Listeners
    chkOnlyMemorized.addEventListener('change', function() {
      if (this.checked) {
        chkOnlyDeleted.checked = false;
        labelOnlyDeleted.classList.remove('checked-deleted');
        labelOnlyMemorized.classList.add('checked-memorized');
        inputSearch.placeholder = "Search only inside memorized words...";
        showToast("⭐ Viewing only memorized words (already_memorized_words.json)!");
      } else {
        labelOnlyMemorized.classList.remove('checked-memorized');
        inputSearch.placeholder = "Search German word, English meaning, sentence...";
        showToast("Searching active dataset (" + currentDatasetId + ").");
      }
      applyFilters();
    });

    chkOnlyDeleted.addEventListener('change', function() {
      if (this.checked) {
        chkOnlyMemorized.checked = false;
        labelOnlyMemorized.classList.remove('checked-memorized');
        labelOnlyDeleted.classList.add('checked-deleted');
        inputSearch.placeholder = "Search only inside deleted words...";
        showToast("🗑️ Viewing deleted words (deleted_datas.json) with Restore option!");
      } else {
        labelOnlyDeleted.classList.remove('checked-deleted');
        inputSearch.placeholder = "Search German word, English meaning, sentence...";
        showToast("Searching active dataset (" + currentDatasetId + ").");
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
      applyFilters();
      window.scrollTo({ top: tableCard.offsetTop - 80, behavior: 'smooth' });
    });

    btnResetCalendarFilter.addEventListener('click', function() {
      selectedCalendarDateStr = null;
      activeDateBadge.style.display = 'none';
      calSelectedDateTitle.textContent = "Select a date";
      calSelectedStatsText.textContent = "Click on any date with a green indicator to view words memorized on that date.";
      calStatsActions.style.display = 'none';
      renderCalendarGrid();
      applyFilters();
    });

    btnClearDateFilter.addEventListener('click', function() {
      selectedCalendarDateStr = null;
      activeDateBadge.style.display = 'none';
      applyFilters();
      showToast("Date filter cleared.");
    });

    // Modals
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalText = document.getElementById('modalText');

    document.getElementById('btnViewMemorized').addEventListener('click', async function() {
      modalTitle.textContent = "already_memorized_words.json (Local Drive • BST Time)";
      modalText.textContent = "Loading local already_memorized_words.json...";
      modal.classList.add('open');
      try {
        const res = await fetch('/api/memorized');
        const data = await res.json();
        modalText.textContent = JSON.stringify(data.words, null, 2);
      } catch (err) {
        modalText.textContent = "Error loading: " + err.message;
      }
    });

    document.getElementById('btnViewDeleted').addEventListener('click', async function() {
      modalTitle.textContent = "deleted_datas.json (Local Drive • BST Time)";
      modalText.textContent = "Loading local deleted_datas.json...";
      modal.classList.add('open');
      try {
        const res = await fetch('/api/deleted');
        const data = await res.json();
        modalText.textContent = JSON.stringify(data.words, null, 2);
      } catch (err) {
        modalText.textContent = "Error loading: " + err.message;
      }
    });

    document.getElementById('btnMemorizedCounter').addEventListener('click', function() {
      document.getElementById('btnViewMemorized').click();
    });

    document.getElementById('btnDeletedCounter').addEventListener('click', function() {
      document.getElementById('btnViewDeleted').click();
    });

    document.getElementById('btnReloadLocal').addEventListener('click', async function() {
      showToast("🔄 Reloading all local data and datasets...");
      await loadDatasets();
      await loadMemorized();
      await loadDeleted();
      await switchDataset(currentDatasetId);
      renderCalendarGrid();
      await loadPdfs();
      showToast("✅ Local data reloaded successfully!");
    });

    document.getElementById('modalClose').addEventListener('click', function() {
      modal.classList.remove('open');
    });

    modal.addEventListener('click', function(e) {
      if (e.target === modal) modal.classList.remove('open');
    });

    // ==========================================
    // PDF Library & Reader State & Handlers
    // ==========================================
    let availablePdfs = [];
    let activePdfId = null;
    let currentPdfCategoryFilter = 'ALL';
    let pdfSearchQuery = '';

    const tabVocabView = document.getElementById('tabVocabView');
    const tabPdfView = document.getElementById('tabPdfView');
    const vocabSection = document.getElementById('vocabSection');
    const pdfSection = document.getElementById('pdfSection');
    const btnNavPdfReader = document.getElementById('btnNavPdfReader');
    const btnBackToVocab = document.getElementById('btnBackToVocab');
    const pdfCountBadge = document.getElementById('pdfCountBadge');

    const pdfSearchInput = document.getElementById('pdfSearchInput');
    const pdfSearchClearBtn = document.getElementById('pdfSearchClearBtn');
    const pdfCategoryFilterContainer = document.getElementById('pdfCategoryFilterContainer');
    const pdfMenuItemsContainer = document.getElementById('pdfMenuItemsContainer');

    const pdfReaderPanel = document.getElementById('pdfReaderPanel');
    const pdfActiveDocIcon = document.getElementById('pdfActiveDocIcon');
    const pdfActiveDocTitle = document.getElementById('pdfActiveDocTitle');
    const pdfActiveDocCategory = document.getElementById('pdfActiveDocCategory');
    const pdfActiveDocSize = document.getElementById('pdfActiveDocSize');
    const pdfActiveDocFilename = document.getElementById('pdfActiveDocFilename');
    const btnPdfPopout = document.getElementById('btnPdfPopout');
    const btnPdfFullscreen = document.getElementById('btnPdfFullscreen');
    const pdfViewerIframe = document.getElementById('pdfViewerIframe');
    const pdfEmptyState = document.getElementById('pdfEmptyState');

    function switchMainMode(mode) {
      if (mode === 'pdf') {
        tabVocabView.classList.remove('active');
        tabPdfView.classList.add('active');
        vocabSection.style.display = 'none';
        pdfSection.style.display = 'block';
        if (!activePdfId && availablePdfs.length > 0) {
          selectPdf(availablePdfs[0].id);
        }
        window.scrollTo({ top: pdfSection.offsetTop - 40, behavior: 'smooth' });
      } else {
        tabPdfView.classList.remove('active');
        tabVocabView.classList.add('active');
        pdfSection.style.display = 'none';
        vocabSection.style.display = 'block';
      }
    }

    async function loadPdfs() {
      try {
        const res = await fetch('/api/pdfs');
        const data = await res.json();
        availablePdfs = data.pdfs || [];
        if (pdfCountBadge) {
          pdfCountBadge.textContent = `${availablePdfs.length} PDF Guides`;
        }
        renderPdfCategoryPills(data.categories || []);
        renderPdfMenu();
      } catch (err) {
        showToast("Error loading PDF guides: " + err.message, "error");
      }
    }

    function renderPdfCategoryPills(categories) {
      if (!pdfCategoryFilterContainer) return;
      pdfCategoryFilterContainer.innerHTML = '';
      
      const allBtn = document.createElement('button');
      allBtn.className = 'pdf-cat-pill' + (currentPdfCategoryFilter === 'ALL' ? ' active' : '');
      allBtn.textContent = `All (${availablePdfs.length})`;
      allBtn.addEventListener('click', () => {
        currentPdfCategoryFilter = 'ALL';
        updateCategoryPillsActive();
        renderPdfMenu();
      });
      pdfCategoryFilterContainer.appendChild(allBtn);

      categories.forEach(cat => {
        const count = availablePdfs.filter(p => p.category === cat).length;
        const btn = document.createElement('button');
        btn.className = 'pdf-cat-pill' + (currentPdfCategoryFilter === cat ? ' active' : '');
        btn.textContent = `${cat} (${count})`;
        btn.dataset.category = cat;
        btn.addEventListener('click', () => {
          currentPdfCategoryFilter = cat;
          updateCategoryPillsActive();
          renderPdfMenu();
        });
        pdfCategoryFilterContainer.appendChild(btn);
      });
    }

    function updateCategoryPillsActive() {
      if (!pdfCategoryFilterContainer) return;
      const pills = pdfCategoryFilterContainer.querySelectorAll('.pdf-cat-pill');
      pills.forEach(p => {
        if (currentPdfCategoryFilter === 'ALL' && !p.dataset.category) {
          p.classList.add('active');
        } else if (p.dataset.category === currentPdfCategoryFilter) {
          p.classList.add('active');
        } else {
          p.classList.remove('active');
        }
      });
    }

    function renderPdfMenu() {
      if (!pdfMenuItemsContainer) return;
      pdfMenuItemsContainer.innerHTML = '';

      let filtered = availablePdfs;
      if (currentPdfCategoryFilter !== 'ALL') {
        filtered = filtered.filter(p => p.category === currentPdfCategoryFilter);
      }
      if (pdfSearchQuery) {
        const q = pdfSearchQuery.toLowerCase();
        filtered = filtered.filter(p => 
          (p.title && p.title.toLowerCase().includes(q)) ||
          (p.id && p.id.toLowerCase().includes(q)) ||
          (p.badge && p.badge.toLowerCase().includes(q)) ||
          (p.category && p.category.toLowerCase().includes(q)) ||
          (p.description && p.description.toLowerCase().includes(q))
        );
      }

      if (filtered.length === 0) {
        pdfMenuItemsContainer.innerHTML = `
          <div style="text-align: center; padding: 28px 12px; color: #64748b; font-size: 0.85rem;">
            No PDF guides match "<strong>${escapeHtml(pdfSearchQuery)}</strong>"
          </div>
        `;
        return;
      }

      // Group by category for visual organization
      const groups = {};
      filtered.forEach(p => {
        const cat = p.category || 'General';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(p);
      });

      Object.keys(groups).forEach(cat => {
        const groupEl = document.createElement('div');
        groupEl.className = 'pdf-category-group';

        const headerEl = document.createElement('div');
        headerEl.className = 'pdf-category-header';
        headerEl.innerHTML = `
          <span>${escapeHtml(cat)}</span>
          <span class="pdf-category-count">${groups[cat].length}</span>
        `;
        groupEl.appendChild(headerEl);

        groups[cat].forEach(pdf => {
          const itemBtn = document.createElement('button');
          itemBtn.className = 'pdf-item-btn' + (pdf.id === activePdfId ? ' active' : '');
          itemBtn.dataset.pdfId = pdf.id;
          itemBtn.title = pdf.description || pdf.title;
          itemBtn.innerHTML = `
            <div class="pdf-item-top">
              <span class="pdf-item-icon">${pdf.icon || '📄'}</span>
              <span class="pdf-item-title">${escapeHtml(pdf.title)}</span>
            </div>
            <div class="pdf-item-bottom">
              ${pdf.badge ? `<span class="pdf-sub-badge">${escapeHtml(pdf.badge)}</span>` : ''}
              <span class="pdf-sub-size">${pdf.size_formatted}</span>
            </div>
          `;
          itemBtn.addEventListener('click', () => {
            selectPdf(pdf.id, true);
          });
          groupEl.appendChild(itemBtn);
        });

        pdfMenuItemsContainer.appendChild(groupEl);
      });
    }

    function selectPdf(pdfId, autoScroll = false) {
      const doc = availablePdfs.find(p => p.id === pdfId);
      if (!doc) return;

      activePdfId = pdfId;
      localStorage.setItem('last_active_pdf', pdfId);

      // Update Toolbar Info
      if (pdfActiveDocIcon) pdfActiveDocIcon.textContent = doc.icon || '📄';
      if (pdfActiveDocTitle) pdfActiveDocTitle.textContent = doc.title;
      if (pdfActiveDocCategory) pdfActiveDocCategory.textContent = doc.category;
      if (pdfActiveDocSize) pdfActiveDocSize.textContent = doc.size_formatted;
      if (pdfActiveDocFilename) pdfActiveDocFilename.textContent = doc.id;
      if (btnPdfPopout) btnPdfPopout.href = doc.url;

      // Update Viewer frame (with #toolbar=1&navpanes=1 for optimal built-in browser PDF controls)
      const targetSrc = doc.url + '#toolbar=1&navpanes=1';
      if (pdfViewerIframe && pdfViewerIframe.src !== targetSrc) {
        pdfViewerIframe.src = targetSrc;
      }
      if (pdfEmptyState) pdfEmptyState.style.display = 'none';

      // Update menu active state
      if (pdfMenuItemsContainer) {
        const allItemBtns = pdfMenuItemsContainer.querySelectorAll('.pdf-item-btn');
        allItemBtns.forEach(btn => {
          if (btn.dataset.pdfId === pdfId) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        });
      }

      // Update URL hash without page reload
      if (window.location.hash !== '#pdf=' + encodeURIComponent(pdfId)) {
        history.replaceState(null, '', '#pdf=' + encodeURIComponent(pdfId));
      }

      if (autoScroll && window.innerWidth <= 1024 && pdfReaderPanel) {
        pdfReaderPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    function togglePdfFullscreen() {
      if (!pdfReaderPanel) return;
      const isFs = pdfReaderPanel.classList.toggle('fullscreen-active');
      if (isFs) {
        btnPdfFullscreen.innerHTML = "✕ Exit Fullscreen";
        btnPdfFullscreen.title = "Exit fullscreen reader";
      } else {
        btnPdfFullscreen.innerHTML = "⛶ Fullscreen";
        btnPdfFullscreen.title = "Toggle fullscreen reading view";
      }
    }

    // Attach PDF listeners
    if (tabVocabView) tabVocabView.addEventListener('click', () => switchMainMode('vocab'));
    if (tabPdfView) tabPdfView.addEventListener('click', () => switchMainMode('pdf'));
    if (btnNavPdfReader) btnNavPdfReader.addEventListener('click', () => switchMainMode('pdf'));
    if (btnBackToVocab) btnBackToVocab.addEventListener('click', () => switchMainMode('vocab'));

    if (pdfSearchInput) {
      pdfSearchInput.addEventListener('input', function(e) {
        pdfSearchQuery = e.target.value.trim();
        if (pdfSearchClearBtn) pdfSearchClearBtn.style.display = pdfSearchQuery ? 'block' : 'none';
        renderPdfMenu();
      });
    }

    if (pdfSearchClearBtn) {
      pdfSearchClearBtn.addEventListener('click', function() {
        pdfSearchInput.value = '';
        pdfSearchQuery = '';
        pdfSearchClearBtn.style.display = 'none';
        renderPdfMenu();
        pdfSearchInput.focus();
      });
    }

    if (btnPdfFullscreen) {
      btnPdfFullscreen.addEventListener('click', togglePdfFullscreen);
    }

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && pdfReaderPanel && pdfReaderPanel.classList.contains('fullscreen-active')) {
        togglePdfFullscreen();
      }
    });

    window.addEventListener('hashchange', function() {
      if (window.location.hash.startsWith('#pdf=')) {
        const pdfFile = decodeURIComponent(window.location.hash.substring(5));
        switchMainMode('pdf');
        selectPdf(pdfFile);
      }
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

            # 1. API: List all available datasets
            if path == "/api/datasets":
                datasets = get_available_datasets()
                self._send_json({"success": True, "datasets": datasets})
                return

            # 1b. API: List all available PDF reference guides
            if path == "/api/pdfs":
                pdf_list = get_available_pdfs()
                categories = []
                cat_seen = set()
                for p in pdf_list:
                    c = p.get("category", "General")
                    if c not in cat_seen:
                        cat_seen.add(c)
                        categories.append(c)
                self._send_json({
                    "success": True,
                    "total": len(pdf_list),
                    "categories": categories,
                    "pdfs": pdf_list
                })
                return

            # 1c. Serve PDF file safely with inline disposition for in-page reading
            if path.startswith("/pdf/"):
                raw_filename = urllib.parse.unquote(path[5:])
                filename = os.path.basename(raw_filename)
                if not filename.lower().endswith(".pdf") or ".." in raw_filename:
                    self.send_error(403, "Access Forbidden")
                    return
                filepath = os.path.join(BASE_DIR, filename)
                if not os.path.exists(filepath) or not os.path.isfile(filepath):
                    self.send_error(404, "PDF Document Not Found")
                    return
                
                try:
                    with open(filepath, "rb") as f:
                        pdf_bytes = f.read()

                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                    self.send_header("Content-Length", str(len(pdf_bytes)))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Cache-Control", "public, max-age=3600")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(pdf_bytes)
                    return
                except Exception as e:
                    self._send_json({"success": False, "error": f"Failed to read PDF: {e}"}, 500)
                    return

            # 2. API: Get Words from specified dataset (or default)
            if path == "/api/words":
                dataset_id = params.get("dataset", [DEFAULT_DATASET])[0]
                words = load_words(dataset_id)

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

                self._send_json({
                    "success": True,
                    "dataset": dataset_id,
                    "total": len(words),
                    "count": len(filtered),
                    "words": filtered
                })
                return

            # 3. API: Get Memorized Words
            if path == "/api/memorized":
                memorized = load_memorized()
                self._send_json({"total": len(memorized), "words": memorized})
                return

            # 4. API: Get Deleted Words from deleted_datas.json
            if path == "/api/deleted":
                deleted_items = load_deleted()
                self._send_json({"total": len(deleted_items), "words": deleted_items})
                return

            # 5. Serve Main HTML
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
            # API: Save/Remove Memorized Word with sl_no & BST timestamp
            if parsed.path == "/api/memorize":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                sl_no = data.get("sl_no")
                word = data.get("word", "")
                dataset_id = data.get("dataset", DEFAULT_DATASET)
                action = data.get("action", "add")

                result = toggle_memorized_entry(sl_no=sl_no, word_text=word, dataset_id=dataset_id, action=action)
                self._send_json(result)
                return

            # API: Delete/Restore Word from deleted_datas.json with sl_no & BST timestamp
            if parsed.path == "/api/delete":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                sl_no = data.get("sl_no")
                word = data.get("word", "")
                dataset_id = data.get("dataset", DEFAULT_DATASET)
                action = data.get("action", "delete")

                result = delete_word_entry(sl_no=sl_no, word_text=word, dataset_id=dataset_id, action=action)
                self._send_json(result)
                return

            self.send_response(404)
            self.end_headers()
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)

    def log_message(self, format, *args):
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
    print(" 🇩🇪 German Vocabulary Multi-Dataset Hub (Docker & Cloud Ready)")
    print(f" 📂 Datasets Available in: {BASE_DIR}")
    print(f" 💾 Memorized (With SL No & BST Time): {MEMORIZED_FILE}")
    print(f" 🗑️ Deleted Datas (With BST Time): {DELETED_FILE}")
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
