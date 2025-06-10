import argparse
import os
import requests
from urllib.parse import urlparse, quote, unquote, urlunparse
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()

def smart_encode_url(url):
    parsed = urlparse(url.strip())
    safe_path = quote(unquote(parsed.path), safe="/:")
    return urlunparse((parsed.scheme, parsed.netloc, safe_path, parsed.params, parsed.query, parsed.fragment))

def get_wayback_url(original_url):
    query_url = f"https://archive.org/wayback/available?url={original_url}"
    try:
        resp = requests.get(query_url, timeout=10)
        data = resp.json()
        archived_snap = data.get("archived_snapshots", {}).get("closest")
        if archived_snap and archived_snap.get("available"):
            return archived_snap.get("url")
    except Exception as e:
        pass
    return None

def download_file(original_url, output_dir):
    try:
        wayback_url = get_wayback_url(original_url)
        file_name = os.path.basename(unquote(urlparse(original_url).path))

        if wayback_url:
            response = requests.get(wayback_url, stream=True, timeout=30)
            if response.status_code == 200:
                file_path = os.path.join(output_dir, file_name)
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return (file_name, True, "")
            else:
                return (file_name, False, f"{response.status_code}")
        else:
            return (file_name, False, "No archive found")
    except Exception as e:
        return (file_name, False, str(e))

def load_urls_from_file(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="📦 Wayback Archive Downloader Tool (Multithreaded)")
    parser.add_argument('-u', '--url', type=str, help="Single URL to download from archive")
    parser.add_argument('-l', '--list', type=str, help="Path to .txt file containing list of URLs")
    parser.add_argument('-o', '--output', type=str, default='downloads', help="Output directory to save files")
    parser.add_argument('-t', '--threads', type=int, default=8, help="Number of download threads (default: 8)")
    args = parser.parse_args()

    urls = []
    if args.url:
        urls = [args.url]
    elif args.list:
        urls = load_urls_from_file(args.list)
    else:
        console.print("[red]❌ Please provide either a single URL (-u) or a list file (-l)[/red]")
        return

    os.makedirs(args.output, exist_ok=True)

    total = len(urls)
    console.print(f"\n[bold cyan]📥 Starting Archive Download: {total} file{'s' if total != 1 else ''}[/bold cyan]\n")

    success_count = 0
    failed_urls = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading archived files...", total=total)

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {executor.submit(download_file, url, args.output): url for url in urls}

            for future in as_completed(futures):
                url = futures[future]
                try:
                    filename, success, error = future.result()
                    if success:
                        console.print(f"[green]✅ Downloaded:[/green] {filename}")
                        success_count += 1
                    else:
                        console.print(f"[red]❌ Not Found:[/red] {filename}")
                        failed_urls.append(url)
                except Exception as e:
                    console.print(f"[red]❌ Exception:[/red] {str(e)}")
                    failed_urls.append(url)
                progress.update(task, advance=1)

    if failed_urls:
        failed_file = os.path.join(args.output, 'failed_urls.txt')
        with open(failed_file, 'w') as f:
            for url in failed_urls:
                f.write(url + "\n")

    console.print("\n[bold magenta]─────────────────────────────── Download Summary ───────────────────────────────[/bold magenta]\n")
    summary = Table(show_header=True, header_style="bold blue")
    summary.add_column("Status", justify="center")
    summary.add_column("Count", justify="center")
    summary.add_row("✅ Successful", str(success_count))
    summary.add_row("❌ Failed", str(len(failed_urls)))
    console.print(summary)

    if failed_urls:
        console.print(f"\n📄 [yellow]Failed URLs saved to:[/yellow] {failed_file}\n")

if __name__ == "__main__":
    main()
