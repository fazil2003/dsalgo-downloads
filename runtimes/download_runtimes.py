import os
import urllib.request

# Directory where the script is located
DOWNLOADS_DIR = os.path.dirname(os.path.abspath(__file__))

# Official stable release bundle URLs
RUNTIMES = {
    "python.zip": "https://github.com/pyodide/pyodide/releases/download/0.26.1/pyodide-core-0.26.1.zip",
    "java.zip": "https://github.com/konsoletyper/teavm/releases/download/v0.10.0/teavm-cli-0.10.0.zip",
    "cpp.zip": "https://github.com/emscripten-core/emsdk/archive/refs/tags/3.1.64.zip"
}

def download_file(url, dest):
    print(f"Downloading {url} -> {dest}...")
    try:
        # Request with a standard User-Agent header to prevent GitHub rate-limiting or blocks
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if total_size > 0:
                    percent = int(downloaded * 100 / total_size)
                    percent = min(percent, 100)
                    print(f"\rProgress: {percent}%", end="")
                else:
                    print(f"\rDownloaded {downloaded} bytes", end="")
        print("\nDownload complete!\n")
    except Exception as e:
        print(f"\nError downloading: {e}\n")

def main():
    print("Starting download of runtime bundles...\n")
    for filename, url in RUNTIMES.items():
        dest_path = os.path.join(DOWNLOADS_DIR, filename)
        download_file(url, dest_path)
    print("All downloads finished.")

if __name__ == "__main__":
    main()
