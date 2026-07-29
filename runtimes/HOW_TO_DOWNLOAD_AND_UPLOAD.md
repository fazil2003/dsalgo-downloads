# How to Download and Upload Runtimes

Run these from the `runtimes/` folder.

## 1. Build the latest runtimes

```bash
python download_runtimes.py
```

This rebuilds `python.zip` and `java.zip`.

## 2. Publish (push to master + tag + purge jsDelivr)

```bash
python publish_runtimes.py
```

This does everything in one step:
- Commits and pushes `python.zip`/`java.zip` to `master`.
- Purges jsDelivr's `@master` cache.
- Creates and pushes a new version tag (e.g. `v1.0.0` → `v1.0.1`).
- Purges jsDelivr's cache for that new tag.

At the end it prints the new tag, e.g.:

```
Update DSALGO_DOWNLOADS_TAG in DownloadManagerScreenController.java to "v1.0.1".
```

## 3. Update the Android app

Open:

```
algorithms-app/app/src/main/java/com/fazil/dsalgo/screen/DownloadManagerScreenController.java
```

Update this line to the new tag printed in step 2:

```java
private static final String DSALGO_DOWNLOADS_TAG = "v1.0.1";
```

Then rebuild the app.
