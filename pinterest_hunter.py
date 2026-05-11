#!/usr/bin/env python3
"""
██████╗ ██╗███╗   ██╗████████╗███████╗██████╗ ███████╗███████╗████████╗
██╔══██╗██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██████╔╝██║██╔██╗ ██║   ██║   █████╗  ██████╔╝█████╗  ███████╗   ██║   
██╔═══╝ ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔══╝  ╚════██║   ██║   
██║     ██║██║ ╚████║   ██║   ███████╗██║  ██║███████╗███████║   ██║   
╚═╝     ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   

██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝

Pinterest Expired Username Hunter with Backlink Checker
Author: oelxyz | Version: 1.0.0
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
import time
import random
import re
import csv
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import print as rprint
from rich.style import Style

console = Console()

BANNER = """[bold red]
██████╗ ██╗███╗   ██╗████████╗███████╗██████╗ ███████╗███████╗████████╗
██╔══██╗██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝
██████╔╝██║██╔██╗ ██║   ██║   █████╗  ██████╔╝█████╗  ███████╗   ██║   
██╔═══╝ ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔══╝  ╚════██║   ██║   
██║     ██║██║ ╚████║   ██║   ███████╗██║  ██║███████╗███████║   ██║   
╚═╝     ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝[/bold red]   

[bold yellow]           ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗[/bold yellow]
[bold yellow]           ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗[/bold yellow]
[bold yellow]           ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝[/bold yellow]
[bold yellow]           ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗[/bold yellow]
[bold yellow]           ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║[/bold yellow]
[bold yellow]           ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/bold yellow]
"""

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

DEFAULT_CONCURRENCY = 10
DEFAULT_TIMEOUT = 15
DEFAULT_DELAY = 0.5
DEFAULT_OUTPUT = "results.json"

PINTEREST_BASE = "https://www.pinterest.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Backlink checker APIs (free tiers / open endpoints)
BACKLINK_SOURCES = {
    "wayback": "https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=10&fl=original,timestamp,statuscode&collapse=urlkey",
}

# CommonCrawl indexes to check — dari terbaru ke terlama
# Setiap index = satu snapshot crawl web (~2 bulan sekali)
CC_INDEXES = [
    "CC-MAIN-2024-10",   # Feb/Mar 2024
    "CC-MAIN-2023-50",   # Des 2023
    "CC-MAIN-2023-23",   # Jun 2023
    "CC-MAIN-2022-49",   # Des 2022
    "CC-MAIN-2021-43",   # Okt 2021
]


# ─────────────────────────────────────────────
# USERNAME GENERATOR
# ─────────────────────────────────────────────

def load_wordlist(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]


def generate_usernames(
    wordlist: Optional[str] = None,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    length_min: int = 3,
    length_max: int = 15,
    count: int = 100,
) -> list[str]:
    """Generate candidate usernames to probe."""
    if wordlist:
        names = load_wordlist(wordlist)
        if prefix:
            names = [f"{prefix}{n}" for n in names]
        if suffix:
            names = [f"{n}{suffix}" for n in names]
        return names

    # ── Keyword banks ──────────────────────────────────────────────────────
    # Generic + niche bases (mix popular & obscure for higher expired hit rate)
    bases_common = [
        "design", "art", "photo", "style", "travel", "food", "fashion",
        "beauty", "home", "diy", "craft", "garden", "fitness", "health",
        "baby", "wedding", "decor", "recipe", "nature", "creative",
        "vintage", "modern", "minimal", "boho", "cute", "fun", "life",
        "daily", "inspire", "dream", "love", "happy", "cool", "awesome",
        "tips", "ideas", "hack", "blog", "shop", "store", "brand", "pro",
        "studio", "lab", "hub", "zone", "world", "space", "place",
        "corner", "gallery", "collection", "page", "official", "real",
    ]
    # Old-era internet usernames (2008–2015 style) — higher expired chance
    bases_oldweb = [
        "xoxo", "luv", "pink", "sparkle", "glitter", "butterfly", "angel",
        "princess", "queen", "king", "ninja", "pirate", "wizard", "dragon",
        "tiger", "wolf", "fox", "panda", "bunny", "kitty", "puppy", "bear",
        "flower", "rose", "lily", "daisy", "ivy", "jade", "pearl", "ruby",
        "crystal", "shadow", "storm", "fire", "ice", "thunder", "lightning",
        "sunflower", "moonlight", "stardust", "rainbow", "mystic", "magic",
        "enchanted", "fairy", "pixie", "sprite", "ember", "echo", "nova",
        "comet", "galaxy", "cosmos", "nebula", "aurora", "soleil", "luna",
        "celeste", "violet", "scarlet", "indigo", "azure", "ivory", "ebony",
        "raven", "sage", "willow", "aspen", "birch", "cedar", "maple",
        "olive", "hazel", "clover", "fern", "lavender", "jasmine", "zinnia",
    ]
    # Name-style usernames (first/last combos typical of abandoned accounts)
    bases_names = [
        "sarah", "jessica", "ashley", "emily", "emma", "olivia", "sophia",
        "mia", "chloe", "isabella", "madison", "abigail", "ella", "grace",
        "lily", "natalie", "samantha", "hannah", "victoria", "zoe",
        "mike", "john", "alex", "chris", "david", "james", "ryan",
        "kevin", "daniel", "matt", "tyler", "jake", "josh", "luke",
        "anna", "marie", "kate", "sue", "jen", "beth", "amy", "lisa",
        "mary", "jane", "alice", "helen", "claire", "diana", "elsa",
    ]
    # Blog/brand name patterns from 2010–2017 era
    bases_blog = [
        "thelittle", "mybig", "thereal", "just", "simply", "purely",
        "allabout", "loveof", "passionfor", "adayof", "lifeof", "worldof",
        "talesof", "diaryof", "notesof", "thinkingof", "dreamof",
        "styledbyme", "curated", "inspired", "obsessed", "addicted",
        "devoted", "blessed", "grateful", "wanderer", "explorer",
        "adventurer", "creator", "maker", "builder", "dreamer", "thinker",
        "writer", "artist", "blogger", "vlogger", "curator", "collector",
    ]

    bases = bases_common + bases_oldweb + bases_names + bases_blog

    # ── Modifier banks ─────────────────────────────────────────────────────
    # Pure text suffixes
    mods_text = [
        "", "s", "er", "ed", "ing", "ish", "ify", "ly",
        "hq", "co", "io", "app", "xyz", "us", "uk", "id", "my",
        "official", "real", "original", "daily", "pro", "elite",
        "plus", "hub", "lab", "zone", "world", "space", "place",
        "club", "crew", "squad", "gang", "team", "life", "blog",
        "style", "love", "passion", "vibes", "inspo",
    ]
    # Year suffixes (accounts from 2008–2019 often have year in username)
    mods_years = [str(y) for y in range(2008, 2020)]          # 2008..2019
    # Short random numbers (super common in old accounts)
    mods_nums_short = [str(n) for n in range(1, 100)]          # 1..99
    # Common number patterns
    mods_nums_pattern = [
        "123", "321", "111", "222", "333", "444", "555",
        "666", "777", "888", "999", "000", "007", "101",
        "100", "200", "300", "365", "24", "247", "360",
        "786", "420", "69", "404", "911",
    ]
    # Two-digit birth years (very common pattern)
    mods_birth = [str(y) for y in range(80, 100)] + [f"0{y}" for y in range(0, 10)] + [str(y) for y in range(10, 30)]

    all_mods = mods_text + mods_years + mods_nums_short + mods_nums_pattern + mods_birth

    # ── Build candidate pool ───────────────────────────────────────────────
    candidates = set()

    # Strategy 1: base + modifier (standard combos)
    random.shuffle(bases)
    random.shuffle(all_mods)
    for b in bases:
        for m in all_mods:
            name = f"{b}{m}"
            if length_min <= len(name) <= length_max:
                if prefix:
                    name = f"{prefix}{name}"
                if suffix:
                    name = f"{name}{suffix}"
                candidates.add(name)
            if len(candidates) >= count * 5:
                break
        if len(candidates) >= count * 5:
            break

    # Strategy 2: random short alphanumeric (3–6 chars) — old squatted accounts
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    for _ in range(min(count, 200)):
        length = random.randint(3, 6)
        name = "".join(random.choices(chars, k=length))
        if length_min <= len(name) <= length_max:
            candidates.add(name)

    # Strategy 3: name + birth year combos (very common expired pattern)
    for name_base in random.sample(bases_names, min(20, len(bases_names))):
        for yr in random.sample(mods_birth, 10):
            name = f"{name_base}{yr}"
            if length_min <= len(name) <= length_max:
                candidates.add(name)

    # Strategy 4: underscore patterns (old Pinterest usernames used _ a lot)
    for b in random.sample(bases_common + bases_oldweb, 30):
        for b2 in random.sample(bases_oldweb + bases_names, 5):
            name = f"{b}_{b2}"
            if length_min <= len(name) <= length_max:
                candidates.add(name)

    result = list(candidates)
    random.shuffle(result)
    result = result[:count]
    return result


# ─────────────────────────────────────────────
# PINTEREST CHECKER
# ─────────────────────────────────────────────

async def check_pinterest_username(
    session: aiohttp.ClientSession,
    username: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Returns:
      status: "expired" | "active" | "error" | "redirect"
      username: str
      url: str
      http_code: int
      note: str
    """
    url = f"{PINTEREST_BASE}/{username}/"
    result = {
        "username": username,
        "url": url,
        "status": "unknown",
        "http_code": 0,
        "note": "",
        "checked_at": datetime.utcnow().isoformat(),
    }
    try:
        async with session.get(
            url,
            allow_redirects=True,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            result["http_code"] = resp.status
            final_url = str(resp.url)

            if resp.status == 404:
                result["status"] = "expired"
                result["note"] = "404 Not Found – username available"
            elif resp.status == 410:
                result["status"] = "expired"
                result["note"] = "410 Gone – permanently deleted"
            elif resp.status in (301, 302, 307, 308):
                result["status"] = "redirect"
                result["note"] = f"Redirect → {final_url}"
            elif resp.status == 200:
                text = await resp.text()
                # Pinterest always returns 200 — must detect via body content.
                # Non-existent accounts embed "User not found." in page JSON.
                # Active accounts have '"username":' and '"full_name":' in data.
                has_notfound = "User not found" in text
                has_userdata = ('"username":' in text and '"full_name":' in text)
                if has_notfound and not has_userdata:
                    result["status"] = "expired"
                    result["note"] = "200 – User not found in page data"
                elif any(p in text.lower() for p in [
                    "this account has been deactivated",
                    "account has been suspended",
                    "this profile is not available",
                ]):
                    result["status"] = "expired"
                    result["note"] = "200 – Account deactivated/suspended"
                elif has_userdata:
                    result["status"] = "active"
                    result["note"] = "Active account"
                else:
                    # Ambiguous — could be login wall or bot block
                    result["status"] = "unknown"
                    result["note"] = "200 – could not determine status (possible bot block)"
            else:
                result["status"] = "error"
                result["note"] = f"Unexpected HTTP {resp.status}"
    except asyncio.TimeoutError:
        result["status"] = "error"
        result["note"] = "Request timed out"
    except aiohttp.ClientConnectorError as e:
        result["status"] = "error"
        result["note"] = f"Connection error: {e}"
    except Exception as e:
        result["status"] = "error"
        result["note"] = str(e)
    return result


# ─────────────────────────────────────────────
# BACKLINK CHECKER
# ─────────────────────────────────────────────

async def check_backlinks(
    session: aiohttp.ClientSession,
    username: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    Check multiple sources for backlinks pointing to pinterest.com/<username>.
    - Wayback Machine CDX (semua tahun)
    - CommonCrawl: 5 index dari 2021–2024
    Returns a dict dengan source → list of backlink records.
    """
    profile_url = f"pinterest.com/{username}"
    backlinks = {}

    # ── 1. Wayback Machine (CDX API) ──────────────────────────────────────
    wayback_url = (
        f"https://web.archive.org/cdx/search/cdx"
        f"?url={quote(profile_url)}*&output=json&limit=10"
        f"&fl=original,timestamp,statuscode&collapse=urlkey"
    )
    try:
        async with session.get(
            wayback_url,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                rows = data[1:] if data and len(data) > 1 else []
                backlinks["wayback"] = [
                    {"original": r[0], "timestamp": r[1], "status": r[2]}
                    for r in rows
                ]
            else:
                backlinks["wayback"] = []
    except Exception as e:
        backlinks["wayback"] = []
        backlinks["wayback_error"] = str(e)

    # ── 2. CommonCrawl — cek semua index sekaligus (parallel) ────────────
    encoded_url = quote(f"pinterest.com/{username}") + "*"

    async def fetch_cc_index(index_name: str) -> list:
        cc_url = (
            f"https://index.commoncrawl.org/{index_name}-index"
            f"?url={encoded_url}&output=json&limit=5"
        )
        try:
            async with session.get(
                cc_url,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    records = []
                    for line in text.strip().splitlines():
                        try:
                            rec = json.loads(line)
                            rec["_index"] = index_name   # tandai dari index mana
                            records.append(rec)
                        except Exception:
                            pass
                    return records
        except Exception:
            pass
        return []

    # Jalankan semua CC index secara paralel
    cc_results = await asyncio.gather(*[fetch_cc_index(idx) for idx in CC_INDEXES])

    # Gabungkan semua hasil, deduplicate berdasarkan URL
    seen_urls = set()
    all_cc_records = []
    for idx_name, records in zip(CC_INDEXES, cc_results):
        for rec in records:
            url_key = rec.get("url", "")
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                all_cc_records.append(rec)

    backlinks["commoncrawl"] = all_cc_records[:20]  # max 20 unik

    # Per-index breakdown (untuk info detail)
    backlinks["commoncrawl_by_index"] = {
        idx: len(records)
        for idx, records in zip(CC_INDEXES, cc_results)
        if records
    }

    # ── 3. Hitung total ───────────────────────────────────────────────────
    total_refs = (
        len(backlinks.get("wayback", []))
        + len(backlinks.get("commoncrawl", []))
    )
    backlinks["total_backlinks_found"] = total_refs
    backlinks["has_backlinks"] = total_refs > 0
    return backlinks


# ─────────────────────────────────────────────
# DOMAIN AUTHORITY ESTIMATOR (Moz-free)
# ─────────────────────────────────────────────

async def estimate_value(username: str, backlink_data: dict) -> dict:
    """
    Simple heuristic scoring for how valuable the expired username is.
    Score 0-100.
    """
    score = 0
    reasons = []

    wb    = len(backlink_data.get("wayback", []))
    cc    = len(backlink_data.get("commoncrawl", []))
    total = wb + cc
    # Jumlah index CC yang menemukan data (makin banyak index = makin tua backlink-nya)
    cc_index_hits = len(backlink_data.get("commoncrawl_by_index", {}))

    if total > 0:
        score += min(total * 5, 40)   # max 40 poin dari jumlah backlink
        reasons.append(f"{total} backlink records found (WB:{wb} CC:{cc})")

    # Bonus jika muncul di banyak CC index — artinya backlink sudah lama & stabil
    if cc_index_hits >= 4:
        score += 20
        reasons.append(f"ditemukan di {cc_index_hits}/5 CC index (backlink stabil)")
    elif cc_index_hits >= 2:
        score += 10
        reasons.append(f"ditemukan di {cc_index_hits}/5 CC index")

    # Wayback bonus — banyak snapshot = akun pernah sangat aktif
    if wb >= 8:
        score += 15
        reasons.append(f"{wb} Wayback snapshots (sangat aktif)")
    elif wb >= 4:
        score += 8
        reasons.append(f"{wb} Wayback snapshots")

    # Short usernames are more valuable
    ulen = len(username)
    if ulen <= 5:
        score += 20
        reasons.append("short username (≤5 chars)")
    elif ulen <= 8:
        score += 12
        reasons.append("short username (≤8 chars)")
    elif ulen <= 12:
        score += 5
        reasons.append("medium username (≤12 chars)")

    # Keyword value
    high_value_kw = ["shop", "store", "brand", "official", "fashion", "design",
                     "art", "photo", "travel", "food", "beauty", "fitness"]
    for kw in high_value_kw:
        if kw in username.lower():
            score += 15
            reasons.append(f"high-value keyword '{kw}'")
            break

    score = min(score, 100)

    if score >= 70:
        tier = "🔥 HIGH"
    elif score >= 40:
        tier = "⚡ MEDIUM"
    else:
        tier = "💤 LOW"

    return {"score": score, "tier": tier, "reasons": reasons}


# ─────────────────────────────────────────────
# CORE SCAN ENGINE
# ─────────────────────────────────────────────

async def scan_usernames(
    usernames: list[str],
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout: int = DEFAULT_TIMEOUT,
    delay: float = DEFAULT_DELAY,
    check_backlinks_flag: bool = True,
    output_file: Optional[str] = None,
    verbose: bool = False,
) -> list[dict]:
    """Main scan loop. Returns list of full result dicts."""

    results = []
    expired_found = []
    semaphore = asyncio.Semaphore(concurrency)
    stats = {"total": len(usernames), "checked": 0, "expired": 0, "active": 0, "errors": 0}

    connector = aiohttp.TCPConnector(limit=concurrency * 2, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:

        # ── Progress display ──────────────────────
        with Progress(
            SpinnerColumn(style="bold magenta"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, style="cyan"),
            TaskProgressColumn(),
            TextColumn("[bold green]{task.fields[expired]} expired"),
            console=console,
            transient=False,
        ) as progress:
            task_id = progress.add_task(
                "[cyan]Scanning usernames…",
                total=len(usernames),
                expired=0,
            )

            async def process_one(username: str):
                async with semaphore:
                    # Step 1: Check Pinterest profile
                    pin_result = await check_pinterest_username(session, username, timeout)
                    stats["checked"] += 1

                    full_result = {**pin_result, "backlinks": {}, "value": {}}

                    if pin_result["status"] == "expired":
                        stats["expired"] += 1
                        # Step 2: Check backlinks
                        if check_backlinks_flag:
                            bl_data = await check_backlinks(session, username, timeout)
                            full_result["backlinks"] = bl_data
                        # Step 3: Estimate value
                        full_result["value"] = await estimate_value(
                            username, full_result["backlinks"]
                        )
                        expired_found.append(full_result)

                        if verbose or full_result["backlinks"].get("has_backlinks"):
                            score = full_result["value"].get("score", 0)
                            tier = full_result["value"].get("tier", "")
                            bl_count = full_result["backlinks"].get("total_backlinks_found", 0)
                            console.print(
                                f"  [bold green]✓ EXPIRED[/bold green] "
                                f"[yellow]{username}[/yellow] "
                                f"| backlinks: [cyan]{bl_count}[/cyan] "
                                f"| score: [magenta]{score}[/magenta] {tier}"
                            )
                    elif pin_result["status"] == "active":
                        stats["active"] += 1
                    else:
                        stats["errors"] += 1

                    results.append(full_result)
                    progress.update(task_id, advance=1, expired=stats["expired"])

                    if delay > 0:
                        await asyncio.sleep(delay + random.uniform(0, delay * 0.5))

            await asyncio.gather(*[process_one(u) for u in usernames])

    return results, expired_found, stats


# ─────────────────────────────────────────────
# REPORT PRINTER
# ─────────────────────────────────────────────

def print_summary(results: list[dict], expired: list[dict], stats: dict):
    console.print()
    console.rule("[bold cyan]SCAN COMPLETE")
    console.print()

    # Stats panel
    stat_table = Table.grid(padding=(0, 2))
    stat_table.add_row("[bold white]Total scanned:", f"[cyan]{stats['total']}")
    stat_table.add_row("[bold white]Checked:", f"[cyan]{stats['checked']}")
    stat_table.add_row("[bold green]Expired:", f"[green]{stats['expired']}")
    stat_table.add_row("[bold yellow]Active:", f"[yellow]{stats['active']}")
    stat_table.add_row("[bold red]Errors:", f"[red]{stats['errors']}")
    console.print(Panel(stat_table, title="[bold]Statistics", border_style="cyan"))

    if not expired:
        console.print("[yellow]No expired usernames found.[/yellow]")
        return

    # Sort by score descending
    expired_sorted = sorted(expired, key=lambda x: x.get("value", {}).get("score", 0), reverse=True)

    table = Table(
        title="🎯 Expired Usernames with Backlinks",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        row_styles=["", "dim"],
    )
    table.add_column("Rank", style="bold white", justify="right", width=5)
    table.add_column("Username", style="bold yellow", width=20)
    table.add_column("Pinterest URL", style="cyan", width=38)
    table.add_column("HTTP", justify="center", width=6)
    table.add_column("Backlinks", justify="center", width=10)
    table.add_column("CC Idx", justify="center", width=7)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Tier", width=12)
    table.add_column("Sources", width=20)

    for i, r in enumerate(expired_sorted, 1):
        bl  = r.get("backlinks", {})
        val = r.get("value", {})
        wb  = len(bl.get("wayback", []))
        cc  = len(bl.get("commoncrawl", []))
        cc_idx_hits = len(bl.get("commoncrawl_by_index", {}))
        total_bl = bl.get("total_backlinks_found", 0)
        score = val.get("score", 0)
        tier  = val.get("tier", "")
        sources = f"WB:{wb} CC:{cc}"

        score_style = "green" if score >= 70 else ("yellow" if score >= 40 else "dim")
        cc_idx_style = "green" if cc_idx_hits >= 4 else ("yellow" if cc_idx_hits >= 2 else "dim")

        table.add_row(
            str(i),
            r["username"],
            r["url"],
            str(r["http_code"]),
            str(total_bl),
            f"[{cc_idx_style}]{cc_idx_hits}/5[/{cc_idx_style}]",
            f"[{score_style}]{score}[/{score_style}]",
            tier,
            sources,
        )

    console.print(table)
    console.print()


def save_results(results: list[dict], expired: list[dict], output_file: str):
    """Save full results to JSON and expired-only to CSV."""
    base = output_file.rsplit(".", 1)[0]
    json_path = output_file
    csv_path = f"{base}_expired.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.utcnow().isoformat(),
                   "total": len(results),
                   "expired_count": len(expired),
                   "results": results}, f, indent=2, ensure_ascii=False)

    fieldnames = ["username", "url", "http_code", "status", "note",
                  "backlinks_total", "wayback_count", "commoncrawl_count",
                  "cc_indexes_hit", "cc_index_breakdown",
                  "score", "tier", "reasons", "checked_at"]
    # Strip emoji from tier for clean CSV output
    def clean(s: str) -> str:
        return re.sub(r'[^\x00-\x7F\u00C0-\u024F\u0370-\u03FF]', '', str(s)).strip()

    with open(csv_path, "w", newline="\n", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for r in sorted(expired, key=lambda x: x.get("value", {}).get("score", 0), reverse=True):
            bl  = r.get("backlinks", {})
            val = r.get("value", {})
            tier_raw = val.get("tier", "")
            tier_plain = tier_raw.split(" ", 1)[-1] if " " in tier_raw else tier_raw
            cc_by_index   = bl.get("commoncrawl_by_index", {})
            cc_breakdown  = " | ".join(f"{k}:{v}" for k, v in cc_by_index.items())
            writer.writerow({
                "username":           r["username"],
                "url":                r["url"],
                "http_code":          r["http_code"],
                "status":             r["status"],
                "note":               clean(r.get("note", "")),
                "backlinks_total":    bl.get("total_backlinks_found", 0),
                "wayback_count":      len(bl.get("wayback", [])),
                "commoncrawl_count":  len(bl.get("commoncrawl", [])),
                "cc_indexes_hit":     len(cc_by_index),
                "cc_index_breakdown": cc_breakdown,
                "score":              val.get("score", 0),
                "tier":               tier_plain,
                "reasons":            "; ".join(val.get("reasons", [])),
                "checked_at":         r.get("checked_at", ""),
            })

    console.print(f"[bold green]✔[/bold green] Full results saved → [cyan]{json_path}[/cyan]")
    console.print(f"[bold green]✔[/bold green] Expired CSV saved  → [cyan]{csv_path}[/cyan] ({len(expired)} rows)")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pinterest Expired Username Hunter with Backlink Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick scan with auto-generated usernames
  python pinterest_hunter.py --count 200 --verbose

  # Scan from a custom wordlist
  python pinterest_hunter.py --wordlist mylist.txt

  # Fast scan, no backlink check
  python pinterest_hunter.py --count 500 --no-backlinks --concurrency 20

  # Add prefix/suffix filter
  python pinterest_hunter.py --count 300 --prefix my --suffix shop

  # Save to custom output file
  python pinterest_hunter.py --count 100 --output expired_pins.json
        """,
    )
    parser.add_argument("--wordlist", "-w", metavar="FILE",
                        help="Path to wordlist file (one username per line)")
    parser.add_argument("--count", "-n", type=int, default=100, metavar="N",
                        help="Number of usernames to generate if no wordlist (default: 100)")
    parser.add_argument("--prefix", metavar="STR",
                        help="Add prefix to all candidate usernames")
    parser.add_argument("--suffix", metavar="STR",
                        help="Add suffix to all candidate usernames")
    parser.add_argument("--length-min", type=int, default=3, metavar="N",
                        help="Minimum username length (default: 3)")
    parser.add_argument("--length-max", type=int, default=15, metavar="N",
                        help="Maximum username length (default: 15)")
    parser.add_argument("--concurrency", "-c", type=int, default=DEFAULT_CONCURRENCY, metavar="N",
                        help=f"Concurrent requests (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--timeout", "-t", type=int, default=DEFAULT_TIMEOUT, metavar="SEC",
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--delay", "-d", type=float, default=DEFAULT_DELAY, metavar="SEC",
                        help=f"Delay between requests per worker (default: {DEFAULT_DELAY})")
    parser.add_argument("--no-backlinks", action="store_true",
                        help="Skip backlink checking (faster)")
    parser.add_argument("--output", "-o", metavar="FILE", default=DEFAULT_OUTPUT,
                        help=f"Output JSON file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print all expired hits to console as found")
    return parser.parse_args()


async def main():
    args = parse_args()

    console.print(BANNER)
    console.print(Panel(
        "[bold white]Pinterest Expired Username Hunter[/bold white]\n"
        "[dim]Finds available usernames that still have backlinks — valuable for SEO redirects[/dim]",
        border_style="red",
    ))
    console.print()

    # Build username list
    console.print("[bold cyan]⚙  Preparing username list…[/bold cyan]")
    usernames = generate_usernames(
        wordlist=args.wordlist,
        prefix=args.prefix,
        suffix=args.suffix,
        length_min=args.length_min,
        length_max=args.length_max,
        count=args.count,
    )
    console.print(f"   [green]✓[/green] {len(usernames)} usernames queued\n")

    if not usernames:
        console.print("[red]No usernames to scan. Exiting.[/red]")
        sys.exit(1)

    # Run scan
    console.print("[bold cyan]🚀 Starting scan…[/bold cyan]")
    console.print(
        f"   Concurrency: [cyan]{args.concurrency}[/cyan] | "
        f"Timeout: [cyan]{args.timeout}s[/cyan] | "
        f"Delay: [cyan]{args.delay}s[/cyan] | "
        f"Backlinks: [cyan]{'YES' if not args.no_backlinks else 'NO'}[/cyan]\n"
    )

    start = time.time()
    results, expired, stats = await scan_usernames(
        usernames=usernames,
        concurrency=args.concurrency,
        timeout=args.timeout,
        delay=args.delay,
        check_backlinks_flag=not args.no_backlinks,
        output_file=args.output,
        verbose=args.verbose,
    )
    elapsed = time.time() - start
    stats["elapsed_seconds"] = round(elapsed, 1)

    print_summary(results, expired, stats)
    save_results(results, expired, args.output)

    console.print(f"\n[dim]Completed in {elapsed:.1f}s[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
