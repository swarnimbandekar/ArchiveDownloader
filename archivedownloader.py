import argparse
import os
import requests
from urllib.parse import urlparse, quote, unquote, urlunparse
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

console = Console()

def smart_encode_url(url):
    parsed = urlparse(url.strip())
    safe_path = quote(unquote(parsed.path), safe="/:")
    return urlunparse((parsed.scheme, parsed.netloc, safe_path, parsed.params, parsed.query, parsed.fragment))

def get_wayback_snapshot_url(original_url):
    cdx_url = "http://web.archive.org/cdx/search/cdx"
    params = {
        "url": original_url,
        "output": "json",
        "fl": "timestamp,original",
        "filter": "statuscode:200",
        "limit": 1,
        "collapse": "digest"
    }
    try:
        response = requests.get(cdx_url, params=params, timeout=10)
        if response.status_code == 200 and len(response.json()) > 1:
            snapshot = response.json()[1]  # First item is header
            timestamp = snapshot[0]
            return f"https://web.archive.org/web/{timestamp}if_/{original_url}"
    except:
        pass
    return None

def download_file(url, output_dir):
    file_name = os.path.basename(unquote(urlparse(url).path))
    try:
        archive_url = get_wayback_snapshot_url(url)
        if not archive_url:
            return (file_name, False, "Not Found")

        response = requests.get(archive_url, stream=True, timeout=10)
        if response.status_code == 200:
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return (file_name, True, "")
        else:
            return (file_name, False, "Not Found")
    except:
        return (file_name, False, "Not Found")

def load_urls_from_file(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    parser = argparse.ArgumentParser(description="📦 Archive Downloader Tool (Wayback Version)")
    parser.add_argument('-u', '--url', type=str, help="Single URL to download")
    parser.add_argument('-l', '--list', type=str, help="Path to .txt file containing list of URLs")
    parser.add_argument('-o', '--output', type=str, default='downloads', help="Output directory to save files")
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
    console.print(f"\n[bold cyan]🌐 Downloading from Internet Archive: {total} file{'s' if total != 1 else ''}[/bold cyan]\n")

    success_count = 0
    failed_urls = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading files...", total=total)
        for url in urls:
            filename, success, _ = download_file(url, args.output)
            if success:
                console.print(f"[green]✅ Downloaded:[/green] {filename}")
                success_count += 1
            else:
                console.print(f"[red]❌ Not Found:[/red] {filename}")
                failed_urls.append(url)
            progress.update(task, advance=1)

    # Save failed URLs
    if failed_urls:
        failed_file = os.path.join(args.output, 'failed_urls.txt')
        with open(failed_file, 'w') as f:
            for url in failed_urls:
                f.write(url + "\n")

    # Summary table
    console.print("\n[bold magenta]──────────────────────────────────────────────────── Download Summary ────────────────────────────────────────────────────[/bold magenta]\n")
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
