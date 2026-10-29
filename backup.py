import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
import gridfs

load_dotenv()

SOURCE = "important_files"
BACKUP_ROOT = "backup"
MANIFEST = "manifest.json"


def get_db():
    client = MongoClient(os.environ["MONGO_URI"], tlsCAFile=certifi.where())
    return client["backup_demo"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def backup():
    if not os.path.isdir(SOURCE):
        print(f"Error: '{SOURCE}' folder not found.")
        return

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snap_dir = os.path.join(BACKUP_ROOT, stamp)
    os.makedirs(snap_dir)

    manifest = {}
    db = get_db()
    fs = gridfs.GridFS(db)
    
    cloud_files = []

    for name in os.listdir(SOURCE):
        src = os.path.join(SOURCE, name)
        if os.path.isfile(src):
            # 1. Local backup
            shutil.copy2(src, os.path.join(snap_dir, name))
            file_hash = sha256(src)
            manifest[name] = file_hash
            
            # 2. Cloud backup
            with open(src, "rb") as f:
                file_id = fs.put(f, filename=name, metadata={"snapshot": stamp, "sha256": file_hash})
                cloud_files.append({"name": name, "file_id": file_id, "sha256": file_hash})

    # Save local manifest
    with open(os.path.join(snap_dir, MANIFEST), "w") as f:
        json.dump(manifest, f, indent=2)

    # Save cloud manifest
    db.manifests.insert_one({
        "snapshot": stamp,
        "files": cloud_files,
        "timestamp": datetime.now()
    })

    print(f"Backed up {len(manifest)} files locally to {snap_dir} and to MongoDB cloud.")


def latest_snapshot():
    if not os.path.isdir(BACKUP_ROOT):
        return None
    snaps = sorted(d for d in os.listdir(BACKUP_ROOT)
                   if os.path.isdir(os.path.join(BACKUP_ROOT, d)))
    return os.path.join(BACKUP_ROOT, snaps[-1]) if snaps else None


def restore_local():
    snap = latest_snapshot()
    if snap is None:
        print("No local backups found. Run 'backup' first.")
        return

    with open(os.path.join(snap, MANIFEST)) as f:
        manifest = json.load(f)

    os.makedirs(SOURCE, exist_ok=True)
    verified = 0
    for name, expected in manifest.items():
        dst = os.path.join(SOURCE, name)
        shutil.copy2(os.path.join(snap, name), dst)
        if sha256(dst) == expected:
            verified += 1
        else:
            print(f"Checksum MISMATCH: {name}")

    print(f"Restored locally from {snap}: {verified}/{len(manifest)} files verified")


def restore_cloud():
    print("Connecting to cloud...")
    db = get_db()
    fs = gridfs.GridFS(db)
    
    latest_manifest = db.manifests.find_one(sort=[("timestamp", -1)])
    if not latest_manifest:
        print("No cloud backups found.")
        return
        
    stamp = latest_manifest["snapshot"]
    os.makedirs(SOURCE, exist_ok=True)
    
    verified = 0
    for file_meta in latest_manifest["files"]:
        name = file_meta["name"]
        expected_hash = file_meta["sha256"]
        file_id = file_meta["file_id"]
        
        dst = os.path.join(SOURCE, name)
        
        grid_out = fs.get(file_id)
        with open(dst, "wb") as f:
            f.write(grid_out.read())
            
        if sha256(dst) == expected_hash:
            verified += 1
        else:
            print(f"Checksum MISMATCH on cloud restore: {name}")

    print(f"Restored from cloud snapshot {stamp}: {verified}/{len(latest_manifest['files'])} files verified")


def list_backups():
    print("--- Local Backups ---")
    if not os.path.isdir(BACKUP_ROOT) or not os.listdir(BACKUP_ROOT):
        print("No local backups yet.")
    else:
        for d in sorted(os.listdir(BACKUP_ROOT)):
            print(d)
            
    print("\n--- Cloud Backups ---")
    try:
        db = get_db()
        manifests = list(db.manifests.find().sort("timestamp", 1))
        if not manifests:
            print("No cloud backups yet.")
        else:
            for m in manifests:
                print(m["snapshot"])
    except Exception as e:
        print(f"Error connecting to cloud: {e}")


if __name__ == "__main__":
    commands = {
        "backup": backup, 
        "restore-local": restore_local, 
        "restore-cloud": restore_cloud,
        "list": list_backups
    }
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("Usage: python backup.py [backup | restore-local | restore-cloud | list]")
    else:
        commands[sys.argv[1]]()
