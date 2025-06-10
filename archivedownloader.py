import os
import sys
import json
import argparse
import requests
from colorama import Fore, Style, init
from tqdm import tqdm

init(autoreset=True)
CDX_API = "http://web.archive.org/cdx/search/cdx?url={url}&output=json"
WAYBACK_BASE = "https://web.archive.org/web/"

def get_snapshots(url):
    try:
        response = requests.get(CDX_API.format(url=url))
        response.raise_for_status()
        data = response.json()
        return [
            f"{WAYBACK_BASE}{entry[1]}/{entry[2]}"
            for entry in data[1:]  # Skip headers
        ]
    except Exception as e:
        print(Fore.RED + f"❌ Error fetching snapshots for {url}: {e}")
        return []

def download_snapshot(snapshot_url, folder="snapshots"):
    os.makedirs(folder, exist_ok=True)
    filename = snapshot_url.split("/")[-1]
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(Fore.YELLOW + f"⚠️ Skipped (already exists): {filename}")
        return

    try:
        r = requests.get(snapshot_url, timeout=10)
        if r.ok:
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(Fore.GREEN + f"✅ Downloaded: {filename}")
        else:
            print(Fore.RED + f"❌ Failed: {snapshot_url}")
    except Exception as e:
        print(Fore.RED + f"❌ Exception: {e}")

def process_url(url):
    print(Fore.CYAN + f"\n🌐 Fetching snapshots for: {url}")
    snapshots = get_snapshots(url)
    if not snapshots:
        print(Fore.RED + "No snapshots found.")
        return
    print(Fore.BLUE + f"📦 Found {len(snapshots)} snapshots. Starting download...\n")
    for snap in tqdm(snapshots, desc="⏬ Downloading", colour="green"):
        download_snapshot(snap)

def main():
    parser = argparse.ArgumentParser(description="Wayback Archive Snapshot Downloader")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Single URL to fetch snapshots from")
    group.add_argument("-l", "--list", help="File with list of URLs")
    args = parser.parse_args()

    if args.url:
        process_url(args.url)
    elif args.list:
        if not os.path.isfile(args.list):
            print(Fore.RED + f"File not found: {args.list}")
            sys.exit(1)
        with open(args.list, "r") as f:
            for line in f:
                url = line.strip()
                if url:
                    process_url(url)

if __name__ == "__main__":
    main()
