"""
Publishes the built runtime bundles (python.zip, java.zip) to the
dsalgo-downloads GitHub repository: pushes to master AND cuts a new
version tag, then purges the jsDelivr cache for both.

Run this AFTER download_runtimes.py has (re)built python.zip/java.zip.

The app itself reads a pinned @vX.Y.Z tag (immutable, never stale), but
@master is kept published and purged too for any other consumer that
still points at @master directly. This script:
  1. Commits and pushes python.zip/java.zip to master.
  2. Purges jsDelivr's @master cache for both files.
  3. Reads the latest vX.Y.Z tag already pushed to origin.
  4. Bumps the patch version (vX.Y.Z -> vX.Y.(Z+1)) and pushes the new tag.
  5. Purges jsDelivr's cache for the new tag (usually a no-op the first
     time a tag is fetched, but harmless/cheap to run).

After running, update DSALGO_DOWNLOADS_TAG in
algorithms-app/app/src/main/java/com/fazil/dsalgo/screen/DownloadManagerScreenController.java
to match the newly printed tag.
"""

import json
import os
import re
import subprocess
import urllib.request

RUNTIMES_DIR = os.path.dirname(os.path.abspath(__file__))

TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

RUNTIME_FILES = ["python.zip", "java.zip"]
VERSIONS_FILENAME = "versions.json"
VERSIONS_FILE = os.path.join(RUNTIMES_DIR, VERSIONS_FILENAME)


def update_versions_json(new_tag):
    """Updates versions.json with the new version for all runtimes."""
    version_str = new_tag.lstrip("v")
    versions = {}
    if os.path.exists(VERSIONS_FILE):
        with open(VERSIONS_FILE, "r") as f:
            versions = json.load(f)
    versions["python"] = version_str
    versions["java"] = version_str
    versions["cpp"] = versions.get("cpp", version_str)
    versions["tag"] = new_tag
    with open(VERSIONS_FILE, "w") as f:
        json.dump(versions, f, indent=2)
        f.write("\n")
    print(f"Updated {VERSIONS_FILENAME}: {versions}")


def push_to_git():
    """Commits and pushes the built zip bundles to the master branch."""
    print("Pushing updates to Git repository...")
    subprocess.run(
        ["git", "add"] + RUNTIME_FILES + [VERSIONS_FILENAME,
         "download_runtimes.py", "publish_runtimes.py"],
        cwd=RUNTIMES_DIR, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Auto-update runtime libraries and placeholders"],
        cwd=RUNTIMES_DIR, check=True)
    subprocess.run(["git", "push", "origin", "master"], cwd=RUNTIMES_DIR, check=True)
    print("Git push to master completed successfully.\n")


def get_latest_tag():
    """Fetches tags from origin and returns the highest vX.Y.Z tag, or None."""
    subprocess.run(["git", "fetch", "origin", "--tags"], cwd=RUNTIMES_DIR, check=True)
    result = subprocess.run(
        ["git", "tag", "-l", "--sort=-v:refname"],
        cwd=RUNTIMES_DIR, check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if TAG_PATTERN.match(line):
            return line
    return None


def bump_patch_version(tag):
    """Bumps the patch component of a vX.Y.Z tag: v1.0.0 -> v1.0.1."""
    match = TAG_PATTERN.match(tag)
    major, minor, patch = match.groups()
    return f"v{major}.{minor}.{int(patch) + 1}"


def purge_cdn_cache(ref, filename):
    """
    Sends a cache purge request to jsDelivr CDN for the given git ref
    (branch or tag), so clients pointed at that ref fetch fresh content.
    """
    url = f"https://purge.jsdelivr.net/gh/fazil2003/dsalgo-downloads@{ref}/runtimes/{filename}"
    print(f"Purging jsDelivr CDN cache for {filename} @ {ref}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            print(f"Purge response for {filename} @ {ref}: {res_data}")
    except Exception as e:
        print(f"Failed to purge cache for {filename} @ {ref}: {e}")


def push_new_tag():
    """Bumps the latest vX.Y.Z tag and pushes it to origin. Returns the new tag name."""
    latest = get_latest_tag()
    if latest is None:
        print("No existing vX.Y.Z tag found - starting at v1.0.0.")
        new_tag = "v1.0.0"
    else:
        new_tag = bump_patch_version(latest)
        print(f"Latest tag: {latest} -> new tag: {new_tag}")

    subprocess.run(
        ["git", "tag", "-a", new_tag, "-m", f"Runtime bundle release {new_tag}"],
        cwd=RUNTIMES_DIR, check=True)
    subprocess.run(["git", "push", "origin", new_tag], cwd=RUNTIMES_DIR, check=True)
    print(f"Pushed tag {new_tag} to origin.\n")
    return new_tag


def main():
    print("Publishing runtime bundles...\n")

    latest = get_latest_tag()
    new_tag = bump_patch_version(latest) if latest else "v1.0.0"
    update_versions_json(new_tag)

    push_to_git()
    for filename in RUNTIME_FILES + [VERSIONS_FILENAME]:
        purge_cdn_cache("master", filename)

    new_tag = push_new_tag()
    for filename in RUNTIME_FILES + [VERSIONS_FILENAME]:
        purge_cdn_cache(new_tag, filename)

    print("All publish tasks finished successfully.")
    print(f"\nUpdate DSALGO_DOWNLOADS_TAG in DownloadManagerScreenController.java to \"{new_tag}\".")


if __name__ == "__main__":
    main()
