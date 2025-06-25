import os
import json
import re
import urllib.request
import urllib.parse

import hiero.core
import hiero.ui

# PySide version check based on Nuke/Nuke Studio major version
try:
    import nuke
    if nuke.NUKE_VERSION_MAJOR >= 16:
        from PySide6 import QtWidgets, QtGui
    else:
        from PySide2 import QtWidgets, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtGui


def get_lucid_link(lucidfullpath):
    print(f"\n[get_lucid_link] Input full path: {lucidfullpath}")
    match = re.search(r"active_projects/.+", lucidfullpath)
    if match:
        lucidShortPath = match.group(0)
    else:
        print(f"[nuke_get_lucidlink] ERROR: Could not extract lucidShortPath from: {lucidfullpath}")
        return "[Error] Invalid path — does not contain /active_projects"

    print(f"[get_lucid_link] Short path: {lucidShortPath}")

    try:
        if os.path.isdir(lucidfullpath):
            lucidParentPath = os.path.dirname(lucidShortPath)
            request_url = f"http://127.0.0.1:8279/files/{lucidParentPath}"
            print(f"[get_lucid_link] Requesting folder listing: {request_url}")
            with urllib.request.urlopen(request_url) as response:
                data = json.load(response)
            print(f"[get_lucid_link] Folder listing returned {len(data)} items")
            lucidFolder = [item for item in data if item['name'] == lucidShortPath]
            fileIDLucid = lucidFolder[0]['id']
        else:
            request_url = f"http://127.0.0.1:8279/v1/sandwich-post.sandwich/files?path=/{lucidShortPath}"
            print(f"[get_lucid_link] Requesting file info: {request_url}")
            with urllib.request.urlopen(request_url) as response:
                data = json.load(response)
            fileIDLucid = data['files'][0]['id']

        lucid_url = f"lucid://sandwich-post.sandwich/file/{fileIDLucid}?reveal=true"
        print(f"[get_lucid_link] SUCCESS: {lucid_url}")
        return lucid_url

    except Exception as e:
        print(f"[get_lucid_link] ERROR: Failed to get LucidLink for {lucidShortPath} — {e}")
        return f"[Error] Failed to get LucidLink for: {lucidShortPath} ({e})"


def is_sequence_path(path):
    match = re.search(r"%\d*d", path)
    if match:
        print(f"[is_sequence_path] Detected sequence pattern in path: {path}")
    return match is not None


def ns_get_lucidlinks():
    print("\n[ns_get_lucidlinks] Running...")
    sequence = hiero.ui.activeSequence()
    if not sequence:
        print("[ns_get_lucidlinks] No active sequence found.")
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No active sequence.")
        return

    timeline_editor = hiero.ui.getTimelineEditor(sequence)
    if not timeline_editor:
        print("[ns_get_lucidlinks] No timeline editor found.")
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No timeline editor available.")
        return

    selected_items = timeline_editor.selection()
    print(f"[ns_get_lucidlinks] Selected track items: {len(selected_items)}")

    if not selected_items:
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No track items selected.")
        return

    links = []

    for item in selected_items:
        if isinstance(item, hiero.core.TrackItem):
            media_source = item.source()
            if not media_source or not media_source.mediaSource():
                print(f"[TrackItem] Skipped — no media source: {item.name()}")
                continue

            file_path = media_source.mediaSource().firstpath()
            print(f"[TrackItem] File path: {file_path}")

            if not file_path:
                print("[TrackItem] Skipped — empty file path")
                continue

            lookup_path = os.path.dirname(file_path) if is_sequence_path(file_path) else file_path
            print(f"[TrackItem] Lookup path: {lookup_path}")

            lucid_url = get_lucid_link(lookup_path)
            if lucid_url.startswith("lucid://"):
                links.append(lucid_url)
            else:
                print(f"[TrackItem] Skipped invalid URL: {lucid_url}")

    if links:
        print(f"[ns_get_lucidlinks] Copying {len(links)} link(s) to clipboard")
        QtGui.QGuiApplication.clipboard().setText('\n'.join(links))
        QtWidgets.QMessageBox.information(None, "Get LucidLink", "Link(s) copied to clipboard")
    else:
        print("[ns_get_lucidlinks] No valid LucidLink URLs found.")
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No valid LucidLink URLs found.")