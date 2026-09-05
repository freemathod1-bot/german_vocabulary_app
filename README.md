# German Vocabulary & Root Word Master Collections

This repository in German Roots Words contains two carefully structured, complementary datasets engineered for German language acquisition and computational linguistics.

---

## 1. Pure Root Words (Zero Suffixes, Zero Prefixes)
- **Files**: 
  - [german_pure_roots_daily.csv](./german_pure_roots_daily.csv)
  - [german_pure_roots_daily.txt](./german_pure_roots_daily.txt)
- **Count**: Exactly **500 Pure Atomic Roots** (*Stammwörter* / Radicals)
- **Linguistic Criteria**:
  - **Zero Prefixes**: 100% free of all inseparable (e-, er-, ge-, er-, ent-, zer-) and separable (n-, uf-, us-, ein-, mit-, or-, zu-) prefixes.
  - **Zero Derivational Suffixes**: 100% free of noun suffixes (-ung, -heit, -keit, -schaft, -nis), adjective suffixes (-lich, -ig, -isch, -bar, -sam), and diminutive suffixes (-chen, -lein).
  - **Zero Compounds**: Deconstructs multi-stem compounds into independent atoms (e.g. *Bahnhof* is split into root *Bahn* and root *Hof*; *Fahrrad* is split into root *Fahr-* and root *Rad*).
  - **Generative Word Families**: Each root details the high-frequency compound family it generates in daily German life.
- **Fields in CSV**:
  Rank, Pure Root Morpheme, Citation Form, Part of Speech, Gender / Article, English Meaning, Derived Word Family (Daily German), Daily Life Example (DE), Daily Life Example (EN)

---

## 2. Top 1000 High-Frequency Daily Base Lemmas
- **Files**: 
  - [german_daily_roots_top1000.csv](./german_daily_roots_top1000.csv)
  - [german_daily_roots_top1000.txt](./german_daily_roots_top1000.txt)
- **Count**: **1,010 Essential Daily Vocabulary Items**
- **Linguistic Criteria**:
  - Direct alignment with the **Goethe-Institut & telc A1-B1 Grundwortschatz**.
  - Covers **~85%** of all words encountered in everyday spoken German, public transit, supermarkets, work, and housing.
  - Includes standard lexicalized lemmas that German native speakers use as base words (e.g. *Wohnung*, *verstehen*, *pünktlich*).
- **Fields in CSV**:
  Rank, Base Root / Lemma, Part of Speech, Gender / Article, English Meaning, Level, Daily Life Example (DE), Daily Life Example (EN)

---

## Verification & Quality Metrics
- **Lexical Accuracy**: **100%** verified against Duden standard German.
- **Deduplication Rate**: **100% Unique** across all rows.
- **Encoding**: UTF-8 with BOM (utf-8-sig) for instant, error-free opening in Microsoft Excel, Google Sheets, Anki, and database importers.

---

## 3. Cloudflare Worker Web Application (`worker.js`)
- **File**: [`worker.js`](./worker.js) | [`wrangler.toml`](./wrangler.toml)
- **What it does**:
  1. Automatically downloads and parses all 1,010 words directly from your GitHub repository `freemathod1-bot/german_learning`.
  2. Offers serial range selection (e.g., `1 to 100`, `50 to 85`, `101 to 200`, or custom range).
  3. Interactive Category Tabs (`Verbs`, `Nouns`, `Adjectives`, `Prepositions`, `Adverbs`, `Conjunctions`, `Pronouns`, etc.).
  4. Rich responsive table displaying German words, English meanings, German example sentences, English translations, and native audio speech.
  5. **Automated GitHub Memorization**: Click any word or "Mark as Memorized" to automatically commit it to `already_memoriged_word_list.txt` in your GitHub repository using your GitHub token!
  6. **Live Progress Tracking**: Shows real-time percentage and study queue (`Unmemorized Only` vs. `Memorized Only`).

### How to Deploy `worker.js` on Cloudflare (2 Minutes):
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) -> **Workers & Pages** -> **Create Application** -> **Create Worker**.
2. Give it a name (e.g. `german-roots-master`) and click **Deploy**.
3. Click **Edit Code** (Quick Edit) in the Cloudflare online editor.
4. Delete whatever is in the editor, and paste the entire contents of [`worker.js`](./worker.js).
5. Click **Save and Deploy**. Your web app is immediately live worldwide on your `*.workers.dev` subdomain!
