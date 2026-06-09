#!/usr/bin/env python3
import json
import os
import hashlib
import tarfile
from pathlib import Path

RELEASES_DIR = Path("releases")
OUTPUT_FILE = Path("index.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def get_root_hash(lgx_path):
    """Compute root hash from tar content"""
    h = hashlib.sha256()
    with tarfile.open(lgx_path, 'r:gz') as tar:
        for member in sorted(tar.getmembers(), key=lambda m: m.name):
            f = tar.extractfile(member)
            if f:
                h.update(f.read())
    return h.hexdigest()

def extract_manifest(lgx_path):
    with tarfile.open(lgx_path, 'r:gz') as tar:
        for member in tar.getmembers():
            if member.name == 'manifest.json':
                return json.loads(tar.extractfile(member).read())
    return None

def build_index():
    packages = []
    
    for lgx_file in sorted(RELEASES_DIR.glob("*.lgx")):
        print(f"Processing {lgx_file.name}...")
        
        manifest = extract_manifest(lgx_file)
        if not manifest:
            print(f"  Warning: No manifest found in {lgx_file.name}")
            continue
        
        sha256 = compute_sha256(lgx_file)
        root_hash = get_root_hash(lgx_file)
        
        # Build variant hashes (simplified - just using root for now)
        hashes = {
            "root": root_hash,
            "variants": compute_sha256(lgx_file),  # Placeholder
        }
        
        # Add platform-specific hashes
        main = manifest.get("main", {})
        for platform in main.keys():
            hashes[f"variants/{platform}"] = compute_sha256(lgx_file)
        
        package = {
            "name": manifest["name"],
            "versions": [{
                "releasedAt": "2026-06-09T10:00:00Z",
                "publisherRef": f"{manifest['name']}-{manifest['version']}",
                "url": f"https://github.com/KindaInsecureBot/keeper-modules/releases/download/v1.0.0/{lgx_file.name}",
                "size": lgx_file.stat().st_size,
                "sha256": sha256,
                "rootHash": root_hash,
                "manifest": manifest,
                "hashes": hashes
            }]
        }
        
        packages.append(package)
    
    index = {
        "schemaVersion": 2,
        "repositoryName": "keeper-modules",
        "generatedAt": "2026-06-09T10:00:00Z",
        "packages": packages
    }
    
    return index

if __name__ == "__main__":
    index = build_index()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(index, f, indent=2)
    print(f"Written {OUTPUT_FILE}")
    print(f"Total packages: {len(index['packages'])}")