import os
import zipfile
import urllib.request
import json

def create_stored_zip(filename, size_mb):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    print(f"Generating {filename} of size {size_mb}MB...")
    temp_file = os.path.join(os.path.dirname(__file__), "temp.bin")
    chunk_size = 1024 * 1024 # 1MB
    with open(temp_file, "wb") as f:
        for _ in range(size_mb):
            f.write(b'\x00' * chunk_size)
            
    # Create zip file with ZIP_STORED (no compression)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_STORED) as z:
        z.write(temp_file, "runtime_data.bin")
        
    os.remove(temp_file)
    print(f"Generated {filename} (Size: {os.path.getsize(filepath) / (1024*1024):.2f} MB)")

def purge_cache(filename):
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

if __name__ == "__main__":
    create_stored_zip("python.zip", 18)
    create_stored_zip("java.zip", 12)
    create_stored_zip("cpp.zip", 19)
    print("")
    purge_cache("python.zip")
    purge_cache("java.zip")
    purge_cache("cpp.zip")
