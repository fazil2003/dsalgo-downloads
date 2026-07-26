import os
import tarfile
import urllib.request
import zipfile
import shutil
import subprocess

RUNTIMES_DIR = os.path.dirname(os.path.abspath(__file__))

def download_pyodide():
    """
    Downloads the Python runtime (Pyodide core) tarball, extracts it,
    and packages the extracted compiler files into a single python.zip.
    """
    url = "https://github.com/pyodide/pyodide/releases/download/0.26.1/pyodide-core-0.26.1.tar.bz2"
    tar_path = os.path.join(RUNTIMES_DIR, "pyodide-core.tar.bz2")
    print("Downloading production Pyodide core tarball...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(tar_path, 'wb') as out:
        out.write(response.read())
        
    extract_dir = os.path.join(RUNTIMES_DIR, "pyodide_temp")
    os.makedirs(extract_dir, exist_ok=True)
    print("Extracting Pyodide core...")
    with tarfile.open(tar_path, "r:bz2") as tar:
        try:
            tar.extractall(path=extract_dir, filter='fully_trusted')
        except TypeError:
            tar.extractall(path=extract_dir)
        
    zip_path = os.path.join(RUNTIMES_DIR, "python.zip")
    print("Creating python.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)
                zipf.write(file_path, arcname)
                
    os.remove(tar_path)
    shutil.rmtree(extract_dir)
    print(f"Pyodide package size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB\n")

def download_teavm():
    """
    Downloads the Java compiler and class library dependencies (TeaVM),
    and packages them into a single java.zip bundle.
    """
    urls = {
        "teavm-cli.jar": "https://repo1.maven.org/maven2/org/teavm/teavm-cli/0.10.0/teavm-cli-0.10.0.jar",
        "teavm-classlib.jar": "https://repo1.maven.org/maven2/org/teavm/teavm-classlib/0.10.0/teavm-classlib-0.10.0.jar"
    }
    
    temp_dir = os.path.join(RUNTIMES_DIR, "teavm_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    for filename, url in urls.items():
        print(f"Downloading {filename}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(os.path.join(temp_dir, filename), 'wb') as out:
            out.write(response.read())
            
    zip_path = os.path.join(RUNTIMES_DIR, "java.zip")
    print("Creating java.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(os.path.join(temp_dir, file), file)
            
    shutil.rmtree(temp_dir)
    print(f"TeaVM package size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB\n")

def push_to_git():
    """
    Pushes the newly compiled/updated zip bundles to the dsalgo-downloads
    GitHub repository master branch.
    """
    print("Pusing updates to Git repository...")
    try:
        # Stage files relative to RUNTIMES_DIR
        subprocess.run(["git", "add", "python.zip", "java.zip", "download_runtimes.py"], cwd=RUNTIMES_DIR, check=True)
        # Commit files
        subprocess.run(["git", "commit", "-m", "Auto-update runtime libraries and placeholders"], cwd=RUNTIMES_DIR, check=True)
        # Push to origin
        subprocess.run(["git", "push", "origin", "master"], cwd=RUNTIMES_DIR, check=True)
        print("Git push completed successfully.\n")
    except Exception as e:
        print(f"Git operations failed: {e}\n")

def purge_cdn_cache(filename):
    """
    Sends a cache purge request to jsDelivr CDN to ensure mobile clients
    fetch the newly uploaded runtime zip file immediately.
    """
    url = f"https://purge.jsdelivr.net/gh/fazil2003/dsalgo-downloads@master/runtimes/{filename}"
    print(f"Purging jsDelivr CDN cache for {filename}...")
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode('utf-8')
            print(f"Purge response for {filename}: {res_data}")
    except Exception as e:
        print(f"Failed to purge cache for {filename}: {e}")

def main():
    """
    Main orchestration function to download, package, publish, and purge
    all development/production runtimes.
    """
    print("Starting download and packaging of production runtimes...\n")
    download_pyodide()
    download_teavm()
    
    # Automate git push and CDN purge
    push_to_git()
    purge_cdn_cache("python.zip")
    purge_cdn_cache("java.zip")
    print("\nAll tasks finished successfully.")

if __name__ == "__main__":
    main()
