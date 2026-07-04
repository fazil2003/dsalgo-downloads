import os
import tarfile
import urllib.request
import zipfile
import shutil

RUNTIMES_DIR = os.path.dirname(os.path.abspath(__file__))

def download_pyodide():
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
        # Use filter='fully_trusted' if supported to avoid warnings
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

def generate_cpp_placeholder():
    # Keep the 19MB placeholder for C++ to bypass jsDelivr limits during release testing
    zip_path = os.path.join(RUNTIMES_DIR, "cpp.zip")
    print("Generating C++ placeholder zip (19 MB)...")
    temp_file = os.path.join(RUNTIMES_DIR, "temp.bin")
    chunk_size = 1024 * 1024
    with open(temp_file, "wb") as f:
        for _ in range(19):
            f.write(b'\x00' * chunk_size)
            
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as z:
        z.write(temp_file, "runtime_data.bin")
        
    os.remove(temp_file)
    print(f"C++ placeholder size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB\n")

def main():
    print("Starting download and packaging of production runtimes...\n")
    download_pyodide()
    download_teavm()
    generate_cpp_placeholder()
    print("All tasks finished successfully.")

if __name__ == "__main__":
    main()
