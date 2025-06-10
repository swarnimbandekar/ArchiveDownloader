import argparse
import os
import requests
from urllib.parse import urlparse, urlunparse, quote
from rich.progress import Progress, BarColumn, TimeElapsedColumn, TextColumn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def smart_encode_url(url):
    parsed = urlparse(url.strip())
    encoded_path = quote(parsed.path)
    return urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment))

def download_file(url, output_dir):
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            filename = os.path.basename(urlparse(url).path)
            filename = filename.strip().rstrip('.')  # Sanitize
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True, filename
        else:
            return False, os.path.basename(url), response.status_code
    except Exception as e:
        return False, os.path.basename(url), str(e)

def main():
    parser = argparse.ArgumentParser(description="📥 Archive Downloader Tool")
    parser.add_argument("-l", "--link-file", required=True, help="Path to the .txt file containing URLs")
    parser.add_argument("-o", "--output", required=True, help="Output directory to save the files")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    with open(args.link_file, "r") as f:
        links = [line.strip() for line in f if line.strip()]

    console.print(Panel.fit(f"📥 [bold cyan]Starting Download: {len(links)} files[/bold cyan]", title="Archive Downloader", style="bold green"))

    success_count = 0
    fail_count = 0
    failed_urls = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading files...", total=len(links))

        for link in links:
            url = smart_encode_url(link)
            result = download_file(url, args.output)
            if result[0]:
                console.print(f"✅ [green]Downloaded:[/green] {result[1]}")
                success_count += 1
            else:
                status = result[2] if len(result) > 2 else "Unknown error"
                console.print(f"❌ [red]Not Found ({status}):[/red] {result[1]}")
                failed_urls.append(link)
                fail_count += 1
            progress.update(task, advance=1)

    # Summary
    summary = Table(title="Download Summary", title_style="bold magenta")
    summary.add_column("Status", justify="center", style="cyan", no_wrap=True)
    summary.add_column("Count", justify="center", style="bold yellow")
    summary.add_row("✅ Successful", str(success_count))
    summary.add_row("❌ Failed", str(fail_count))
    console.print(summary)

    if failed_urls:
        failed_file_path = os.path.join(args.output, "failed_urls.txt")
        with open(failed_file_path, "w") as f:
            f.write("\n".join(failed_urls))
        console.print(f"📄 [italic yellow]Failed URLs saved to:[/italic yellow] {failed_file_path}")

if __name__ == "__main__":
    main()
