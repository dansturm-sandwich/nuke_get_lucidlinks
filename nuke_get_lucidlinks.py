import nuke
import os
import json
import re
import urllib.request
import urllib.parse

# Conditional import for PySide based on Nuke version
if nuke.NUKE_VERSION_MAJOR >= 16:
    from PySide6 import QtWidgets, QtGui
else:
    from PySide2 import QtWidgets, QtGui


def get_lucid_link(lucidfullpath):
    lucidfullpath = lucidfullpath.replace("file://", "")
    lucidShortPath = lucidfullpath.replace("/Volumes/sandwich-post/", "")
    lucidShortPath = lucidShortPath.replace(" ", "%20")

    try:
        if os.path.isdir(lucidfullpath):
            lucidParentPath = os.path.dirname(lucidShortPath)
            request_url = f"http://127.0.0.1:8279/files/{lucidParentPath}"
            with urllib.request.urlopen(request_url) as response:
                data = json.load(response)
            lucidFolder = [item for item in data if item['name'] == lucidShortPath]
            fileIDLucid = lucidFolder[0]['id']
        else:
            request_url = f"http://127.0.0.1:8279/v1/sandwich-post.sandwich/files?path=/{lucidShortPath}"
            with urllib.request.urlopen(request_url) as response:
                data = json.load(response)
            fileIDLucid = data['files'][0]['id']

        return f"lucid://sandwich-post.sandwich/file/{fileIDLucid}?reveal=true"

    except Exception as e:
        return f"[Error] Failed to get LucidLink for: {lucidShortPath} ({e})"


def is_sequence_path(path):
    """Check for frame padding expressions like %04d or %08d in the file path."""
    return re.search(r"%\d*d", path) is not None


def get_lucidlink():
    selected_nodes = nuke.selectedNodes()
    if not selected_nodes:
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No nodes selected.")
        return

    valid_nodes = [n for n in selected_nodes if n.Class() == 'Read']
    invalid_nodes = [n for n in selected_nodes if n.Class() != 'Read']

    if invalid_nodes:
        QtWidgets.QMessageBox.critical(None, "Get LucidLink", "Get LucidLink: only Read nodes supported")
        return

    links = []
    for node in valid_nodes:
        file_path = node['file'].value()
        if not file_path:
            continue

        # If it's a sequence path, use the parent folder
        if is_sequence_path(file_path):
            lookup_path = os.path.dirname(file_path)
        else:
            lookup_path = file_path

        lucid_url = get_lucid_link(lookup_path)

        # Filter out error responses that don't contain "lucid://"
        if lucid_url.startswith("lucid://"):
            links.append(lucid_url)

    if links:
        QtGui.QGuiApplication.clipboard().setText('\n'.join(links))
        QtWidgets.QMessageBox.information(None, "Get LucidLink", "Link(s) copied to clipboard")
    else:
        QtWidgets.QMessageBox.warning(None, "Get LucidLink", "No valid LucidLink URLs found.")