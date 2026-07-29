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
    ecj_url = "https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/3.12.3/ecj-3.12.3.jar"
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
                String relStr = rel.toString().replace('\\\\', '/');
                if (relStr.startsWith("javax/tools/")) {
                    return;
                }
                Path dest = destDir.resolve(rel.toString().replace("/", FileSystems.getDefault().getSeparator()));
                try {
                    Files.createDirectories(dest.getParent());
                    Files.copy(path, dest, StandardCopyOption.REPLACE_EXISTING);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });

        Path baseModule = fs.getPath("/modules/java.base");
        Files.walk(baseModule).forEach(path -> {
            if (Files.isRegularFile(path) && path.toString().endsWith(".class")) {
                Path rel = baseModule.relativize(path);
                String relStr = rel.toString().replace('\\\\', '/');
                if (relStr.startsWith("java/lang/") || relStr.startsWith("java/util/") ||
                    relStr.startsWith("java/io/") || relStr.startsWith("java/math/") ||
                    relStr.startsWith("java/text/")) {
                    
                    // Skip subpackages we don't need to keep it small
                    if (relStr.contains("/concurrent/") || relStr.contains("/function/") || 
                        relStr.contains("/stream/") || relStr.contains("/spi/") || 
                        relStr.contains("/regex/") || relStr.contains("/jar/") || 
                        relStr.contains("/zip/") || relStr.contains("/logging/")) {
                        return;
                    }

                    Path dest = destDir.resolve(rel.toString().replace("/", FileSystems.getDefault().getSeparator()));
                    try {
                        Files.createDirectories(dest.getParent());
                        Files.copy(path, dest, StandardCopyOption.REPLACE_EXISTING);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
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

    # 2. Overwrite/add custom safe mock classes
    javax_src_model_dir = os.path.join(temp_dir, "javax_src", "javax", "lang", "model")
    javax_src_tools_dir = os.path.join(temp_dir, "javax_src", "javax", "tools")
    os.makedirs(javax_src_model_dir, exist_ok=True)
    os.makedirs(javax_src_tools_dir, exist_ok=True)

    # 2a. SourceVersion mock
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

    # 2b. javax.tools stubs (Java 8 compatible stubs to satisfy compiler signatures without jrt lookup trigger)
    stubs = {
        "FileObject.java": "package javax.tools;\npublic interface FileObject {\n    java.net.URI toUri();\n    String getName();\n    java.io.InputStream openInputStream() throws java.io.IOException;\n    java.io.OutputStream openOutputStream() throws java.io.IOException;\n    java.io.Reader openReader(boolean ignoreEncodingErrors) throws java.io.IOException;\n    CharSequence getCharContent(boolean ignoreEncodingErrors) throws java.io.IOException;\n    java.io.Writer openWriter() throws java.io.IOException;\n    long getLastModified();\n    boolean delete();\n}",
        "JavaFileObject.java": "package javax.tools;\npublic interface JavaFileObject extends FileObject {\n    enum Kind { SOURCE, CLASS, HTML, OTHER }\n}",
        "JavaFileManager.java": """package javax.tools;
import java.io.IOException;
import java.util.Set;
public interface JavaFileManager extends java.io.Closeable, java.io.Flushable, OptionChecker {
    interface Location {
        default String getName() { return ""; }
        default boolean isOutputLocation() { return false; }
    }
    default ClassLoader getClassLoader(Location location) { return null; }
    default Iterable<JavaFileObject> list(Location location, String packageName, Set<JavaFileObject.Kind> kinds, boolean recurse) throws IOException { return null; }
    default String inferBinaryName(Location location, JavaFileObject file) { return null; }
    default boolean isSameFile(FileObject a, FileObject b) { return false; }
    default boolean handleOption(String current, java.util.Iterator<String> remaining) { return false; }
    default boolean hasLocation(Location location) { return false; }
    default JavaFileObject getJavaFileForInput(Location location, String className, JavaFileObject.Kind kind) throws IOException { return null; }
    default JavaFileObject getJavaFileForOutput(Location location, String className, JavaFileObject.Kind kind, FileObject sibling) throws IOException { return null; }
    default FileObject getFileForInput(Location location, String packageName, String relativeName) throws IOException { return null; }
    default FileObject getFileForOutput(Location location, String packageName, String relativeName, FileObject sibling) throws IOException { return null; }
    default void close() throws IOException {}
    default void flush() throws IOException {}
}""",
        "StandardJavaFileManager.java": """package javax.tools;
import java.io.File;
import java.io.IOException;
public interface StandardJavaFileManager extends JavaFileManager {
    default Iterable<? extends JavaFileObject> getJavaFileObjectsFromFiles(Iterable<? extends File> files) { return null; }
    default Iterable<? extends JavaFileObject> getJavaFileObjects(File... files) { return null; }
    default Iterable<? extends JavaFileObject> getJavaFileObjectsFromStrings(Iterable<String> names) { return null; }
    default Iterable<? extends JavaFileObject> getJavaFileObjects(String... names) { return null; }
    default void setLocation(Location location, Iterable<? extends File> path) throws IOException {}
    default Iterable<? extends File> getLocation(Location location) { return null; }
}""",
        "OptionChecker.java": """package javax.tools;
public interface OptionChecker {
    default boolean handleOption(String current, java.util.Iterator<String> remaining) { return false; }
    default int isSupportedOption(String option) { return -1; }
}""",
        "Tool.java": "package javax.tools;\npublic interface Tool {}",
        "JavaCompiler.java": "package javax.tools;\npublic interface JavaCompiler extends Tool, OptionChecker {\n    interface CompilationTask extends java.util.concurrent.Callable<Boolean> {}\n}",
        "DocumentationTool.java": "package javax.tools;\npublic interface DocumentationTool extends Tool, OptionChecker {}",
        "StandardLocation.java": "package javax.tools;\npublic enum StandardLocation implements JavaFileManager.Location {\n    CLASS_OUTPUT, SOURCE_OUTPUT, CLASS_PATH, SOURCE_PATH, ANNOTATION_PROCESSOR_PATH, PLATFORM_CLASS_PATH, NATIVE_HEADER_OUTPUT;\n}",
        "SimpleJavaFileObject.java": """package javax.tools;
import java.net.URI;
public class SimpleJavaFileObject implements JavaFileObject {
    protected final URI uri;
    protected final Kind kind;
    protected SimpleJavaFileObject(URI uri, Kind kind) {
        this.uri = uri;
        this.kind = kind;
    }
    public URI toUri() { return uri; }
    public String getName() { return uri.getPath(); }
    public java.io.InputStream openInputStream() throws java.io.IOException { throw new UnsupportedOperationException(); }
    public java.io.OutputStream openOutputStream() throws java.io.IOException { throw new UnsupportedOperationException(); }
    public java.io.Reader openReader(boolean ignoreEncodingErrors) throws java.io.IOException { throw new UnsupportedOperationException(); }
    public CharSequence getCharContent(boolean ignoreEncodingErrors) throws java.io.IOException { throw new UnsupportedOperationException(); }
    public java.io.Writer openWriter() throws java.io.IOException { throw new UnsupportedOperationException(); }
    public long getLastModified() { return 0; }
    public boolean delete() { return false; }
}"""
    }

    stub_files = []
    for filename, code in stubs.items():
        filepath = os.path.join(javax_src_tools_dir, filename)
        with open(filepath, "w") as f:
            f.write(code)
        stub_files.append(filepath)

    print("Compiling safe SourceVersion and javax.tools stub classes...")
    subprocess.run(["javac", "-source", "8", "-target", "8", "-d", javax_out_dir, source_version_file] + stub_files, check=True)

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
        zipf.write(source_version_jar, "rt.jar")
        
    shutil.rmtree(temp_dir)
    print(f"Java package size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB\n")

def main():
    """
    Main orchestration function to download and package all
    development/production runtimes into python.zip / java.zip.

    Publishing (git push + jsDelivr version tag) is a separate step -
    run publish_runtimes.py afterward to push these bundles live.
    """
    print("Starting download and packaging of production runtimes...\n")
    download_pyodide()
    download_teavm()
    print("\nAll build tasks finished successfully.")
    print("Run publish_runtimes.py to push these bundles to GitHub and cut a new jsDelivr tag.")

if __name__ == "__main__":
    main()
