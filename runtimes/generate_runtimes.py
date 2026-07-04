import os
import zipfile

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

if __name__ == "__main__":
    create_stored_zip("python.zip", 18)
    create_stored_zip("java.zip", 12)
    create_stored_zip("cpp.zip", 19)
