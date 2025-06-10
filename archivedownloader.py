import os
import argparse
import requests
from urllib.parse import urlparse, unquote

def download_file(url, output_dir):
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filename = unquote(filename)

        if not filename:
            filename = "downloaded_file"

        response = requests.get(url, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        output_path = os.path.join(output_dir, filename)
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url} - {e}")

def main():
    parser = argparse.ArgumentParser(description="Download files from a list of URLs.")
    parser.add_argument("-l", "--list", required=True, help="Path to text file with URLs.")
    parser.add_argument("-o", "--output", required=True, help="Output directory for downloads.")

    args = parser.parse_args()

    # Validate input file
    if not os.path.isfile(args.list):
        print(f"List file '{args.list}' does not exist.")
        return

    # Validate or create output directory
    if not os.path.isdir(args.output):
        os.makedirs(args.output)

    with open(args.list, "r") as file:
        urls = [line.strip() for line in file if line.strip()]

    for url in urls:
        download_file(url, args.output)

if __name__ == "__main__":
    main()
