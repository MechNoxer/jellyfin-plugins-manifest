#!/usr/bin/env python3
"""
Stamps a new plugin version into manifest.json.
Usage: python3 update_manifest.py <version> <zip_name> <repo_base_url> [<guid> [<plugin_name> [<tag_name>]]]

<tag_name> is the full git tag used for the GitHub Release (e.g. "drive-status-v1.0.0").
Defaults to "v<version>" when omitted (correct for the media-requests plugin).

Examples:
  python3 update_manifest.py 1.0.0 jellyfin-plugin-mediarequests_1.0.0.zip https://github.com/owner/repo
  python3 update_manifest.py 1.0.0 jellyfin-plugin-drivestatus_1.0.0.zip   https://github.com/owner/repo \
      6b3c5d2e-8f4a-4b1c-9e7d-0a2f5c8e1b4d "Drive Status" drive-status-v1.0.0
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

TARGET_ABI = "10.9.0.0"

PLUGIN_DEFAULTS = {
    "8b2b77d8-ba7a-4c69-8d6b-a55e55af9aa4": {
        "name": "Media Requests",
        "description": "Let users request movies and shows. Admins manage the list from the dashboard.",
        "overview": "User-facing media request system for Jellyfin.",
    },
    "6b3c5d2e-8f4a-4b1c-9e7d-0a2f5c8e1b4d": {
        "name": "Drive Status",
        "description": "Shows attached hard drive statuses and storage capacity on the server.",
        "overview": "Hard drive status dashboard for Jellyfin admins.",
    },
}

MEDIA_REQUESTS_GUID = "8b2b77d8-ba7a-4c69-8d6b-a55e55af9aa4"


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    version  = sys.argv[1]
    zip_name = sys.argv[2]
    repo_url = sys.argv[3].rstrip("/")
    guid          = sys.argv[4] if len(sys.argv) > 4 else MEDIA_REQUESTS_GUID
    name_override = sys.argv[5] if len(sys.argv) > 5 else None
    tag_name      = sys.argv[6] if len(sys.argv) > 6 else f"v{version}"

    defaults    = PLUGIN_DEFAULTS.get(guid, {})
    plugin_name = name_override or defaults.get("name", "Unknown Plugin")
    description = defaults.get("description", "")
    overview    = defaults.get("overview", "")

    filename  = os.path.basename(zip_name)
    checksum  = md5(zip_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    parts = version.split(".")
    while len(parts) < 4:
        parts.append("0")
    four_part = ".".join(parts[:4])

    source_url = f"{repo_url}/releases/download/{tag_name}/{filename}"

    manifest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    entry = next((p for p in manifest if p.get("guid") == guid), None)
    if entry is None:
        entry = {
            "category": "General",
            "description": description,
            "guid": guid,
            "imageUrl": "",
            "name": plugin_name,
            "overview": overview,
            "owner": "MechNoxer",
            "versions": [],
        }
        manifest.append(entry)

    entry["versions"] = [v for v in entry["versions"] if v.get("version") != four_part]
    entry["versions"].insert(0, {
        "changelog": f"Release {version}",
        "checksum": checksum,
        "sourceUrl": source_url,
        "targetAbi": TARGET_ABI,
        "timestamp": timestamp,
        "version": four_part,
    })

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
        f.write("\n")

    print(f"manifest.json updated — {plugin_name} {four_part}, checksum {checksum}")


if __name__ == "__main__":
    main()
