# Web Archive Downloader

A simple Python CLI tool to download files from a list of URLs (e.g., from the Wayback Machine or web archives). Files are saved directly into a specified output folder without creating extra subdirectories.

---

## 📦 Features

- Download files from URLs in a `.txt` file
- Save all files in a single output directory
- Automatically handles missing filenames
- Basic error handling with clean output

---

## 🚀 Installation

1. **Clone this repository or download the script**:
   ```bash
   git clone https://github.com/swarnimbandekar/ArchiveDownloader.git
   cd ArchiveDownloader
   ```
2. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Usage

```bash
   python3 archivedownloader.py -l urls.txt -o output/
   ```
**Arguments**:
- -l, --list: Path to a text file containing URLs (one per line)
- -o, --output: Directory where downloaded files will be saved

---

**Example**:
If urls.txt contains:
```bash
   https://web.archive.org/web/20220101000000/https://example.com/file1.pdf
   https://web.archive.org/web/20220101000000/https://example.com/image.jpg
   ```
The files will be saved in the output/ folder.

---