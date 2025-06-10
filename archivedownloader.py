import os
import time
import requests
from urllib.parse import urlparse, unquote
from rich.console import Console
from rich.progress import track
from rich.panel import Panel

console = Console()

def download_file(url, output_dir, retries=3, timeout=60):
    parsed_url = urlparse(url)
    filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file"
    output_path = os.path.join(output_dir, filename)

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            console.print(f"✅ [bold green]Downloaded:[/bold green] {filename}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                console.print(f"❌ [bold red]Not Found (404):[/bold red] {filename}")
                return False
            else:
                console.print(f"❌ [red]HTTP Error:[/red] {e}")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            console.print(f"⚠️ [yellow]Retrying {filename} ({attempt}/{retries})...[/yellow]")
            time.sleep(2)
        except Exception as e:
            console.print(f"❌ [red]Error downloading {filename}:[/red] {e}")
            return False
    console.print(f"❌ [red]Failed after {retries} retries:[/red] {filename}")
    return False


def download_from_list(file_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    failed_urls = []
    success_count = 0

    console.print(Panel.fit(f"📥 Starting Download: {len(urls)} files", style="bold blue"))

    for url in track(urls, description="[cyan]Downloading files..."):
        success = download_file(url, output_dir)
        if not success:
            failed_urls.append(url)
        else:
            success_count += 1

    # Summary
    console.print()
    console.rule("[bold blue]Download Summary")
    console.print(f"✅ [green]Successfully downloaded:[/green] {success_count}")
    console.print(f"❌ [red]Failed downloads:[/red] {len(failed_urls)}")

    if failed_urls:
        fail_log_path = os.path.join(output_dir, "failed_urls.txt")
        with open(fail_log_path, "w") as f:
            f.write("\n".join(failed_urls))
        console.print(f"📄 [yellow]Failed URLs saved to:[/yellow] {fail_log_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download files from a list of URLs")
    parser.add_argument("-l", "--list", required=True, help="Path to the URL list file")
    parser.add_argument("-o", "--output", default="downloads", help="Output directory for downloaded files")

    args = parser.parse_args()
    download_from_list(args.list, args.output)
