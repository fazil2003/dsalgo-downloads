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
    Downloads the Java compiler (ECJ) and Android DX libraries,
    dexes them using d8, and packages them into java.zip.
    """
    ecj_url = "https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/3.26.0/ecj-3.26.0.jar"
    temp_dir = os.path.join(RUNTIMES_DIR, "java_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    ecj_jar = os.path.join(temp_dir, "ecj.jar")
    print("Downloading ECJ...")
    req = urllib.request.Request(ecj_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(ecj_jar, 'wb') as out:
        out.write(response.read())
        
    sdk_dir = "D:\\Softwares\\Android\\Sdk"
    build_tools_dir = os.path.join(sdk_dir, "build-tools")
    
    dx_jar_path = None
    d8_path = None
    
    if os.path.exists(build_tools_dir):
        for version in sorted(os.listdir(build_tools_dir), reverse=True):
            candidate_dx = os.path.join(build_tools_dir, version, "lib", "dx.jar")
            if os.path.exists(candidate_dx):
                dx_jar_path = candidate_dx
                break
        for version in sorted(os.listdir(build_tools_dir), reverse=True):
            candidate_d8 = os.path.join(build_tools_dir, version, "d8.bat")
            if os.path.exists(candidate_d8):
                d8_path = candidate_d8
                break
                
    if not dx_jar_path or not d8_path:
        print("Error: Could not locate dx.jar or d8.bat in Android SDK.")
        shutil.rmtree(temp_dir)
        return
        
    print(f"Found dx.jar: {dx_jar_path}")
    print(f"Found d8.bat: {d8_path}")
    
    ecj_dex_jar = os.path.join(temp_dir, "ecj.dex.jar")
    dx_dex_jar = os.path.join(temp_dir, "dx.dex.jar")
    
    # Extract all official javax compiler classes from host JDK to resolve missing classes at once
    extractor_code = """import java.nio.file.*;
import java.net.URI;
import java.io.IOException;

public class JdkCompilerExtractor {
    public static void main(String[] args) throws Exception {
        Path destDir = Paths.get(args[0]);
        FileSystem fs = FileSystems.getFileSystem(URI.create("jrt:/"));
        Path compilerModule = fs.getPath("/modules/java.compiler");
        
        Files.walk(compilerModule).forEach(path -> {
            if (Files.isRegularFile(path) && path.toString().endsWith(".class")) {
                Path rel = compilerModule.relativize(path);
                Path dest = destDir.resolve(rel.toString().replace("/", FileSystems.getDefault().getSeparator()));
                try {
                    Files.createDirectories(dest.getParent());
                    Files.copy(path, dest, StandardCopyOption.REPLACE_EXISTING);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });
    }
}
"""
    extractor_file = os.path.join(temp_dir, "JdkCompilerExtractor.java")
    with open(extractor_file, "w") as f:
        f.write(extractor_code)
        
    print("Extracting compiler API classes from host JDK...")
    javax_out_dir = os.path.join(temp_dir, "javax_out")
    os.makedirs(javax_out_dir, exist_ok=True)
    subprocess.run(["java", extractor_file, javax_out_dir], check=True)

    # 2. Overwrite the extracted JDK SourceVersion.class with our safe Android-compatible mock SourceVersion
    javax_src_model_dir = os.path.join(temp_dir, "javax_src", "javax", "lang", "model")
    os.makedirs(javax_src_model_dir, exist_ok=True)
    source_version_code = """package javax.lang.model;
public enum SourceVersion {
    RELEASE_0, RELEASE_1, RELEASE_2, RELEASE_3, RELEASE_4, RELEASE_5, RELEASE_6, RELEASE_7, RELEASE_8,
    RELEASE_9, RELEASE_10, RELEASE_11, RELEASE_12, RELEASE_13, RELEASE_14, RELEASE_15, RELEASE_16,
    RELEASE_17, RELEASE_18, RELEASE_19, RELEASE_20, RELEASE_21;
    public static SourceVersion latest() { return RELEASE_21; }
    public static SourceVersion latestSupported() { return RELEASE_21; }
}
"""
    source_version_file = os.path.join(javax_src_model_dir, "SourceVersion.java")
    with open(source_version_file, "w") as f:
        f.write(source_version_code)
    
    print("Compiling safe SourceVersion mock class...")
    subprocess.run(["javac", "-source", "8", "-target", "8", "-d", javax_out_dir, source_version_file], check=True)

    source_version_jar = os.path.join(temp_dir, "source_version.jar")
    with zipfile.ZipFile(source_version_jar, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(javax_out_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, javax_out_dir)
                arcname = arcname.replace('\\', '/')
                zipf.write(file_path, arcname)

    print("Dexing ECJ compiler...")
    subprocess.run([d8_path, "--output", ecj_dex_jar, ecj_jar, source_version_jar], check=True, shell=True)
    
    # Copy resource bundle properties files into ecj.dex.jar
    print("Copying resources to ecj.dex.jar...")
    with zipfile.ZipFile(ecj_jar, 'r') as src_zip:
        with zipfile.ZipFile(ecj_dex_jar, 'a') as dest_zip:
            for item in src_zip.infolist():
                if not item.filename.endswith('.class') and not item.filename.startswith('META-INF/'):
                    dest_zip.writestr(item.filename, src_zip.read(item.filename))

    print("Dexing DX tool...")
    subprocess.run([d8_path, "--output", dx_dex_jar, dx_jar_path], check=True, shell=True)
    
    zip_path = os.path.join(RUNTIMES_DIR, "java.zip")
    print("Creating java.zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(ecj_dex_jar, "ecj.dex.jar")
        zipf.write(dx_dex_jar, "dx.dex.jar")
        
    shutil.rmtree(temp_dir)
    print(f"Java package size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB\n")

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
