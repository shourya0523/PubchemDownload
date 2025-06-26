import requests
import os
import time
import json
from datetime import datetime

# Configuration
START_CID = 5000000  # Change this to your starting point
BATCH_SIZE = 5000    # How many to download per GitHub Actions run
PROGRESS_FILE = "progress.json"

def load_progress():
    """Load progress from previous runs"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('last_cid', START_CID), set(data.get('completed', []))
    return START_CID, set()

def save_progress(last_cid, completed):
    """Save progress for next run"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            'last_cid': last_cid,
            'completed': list(completed),
            'updated': datetime.now().isoformat()
        }, f, indent=2)

def download_json_locally(cid, folder="pubchem_downloads"):
    """Download a single compound"""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
    
    os.makedirs(folder, exist_ok=True)
    json_path = os.path.join(folder, f"pubchem_{cid}.json")
    
    # Skip if already exists
    if os.path.exists(json_path):
        return True
        
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ Downloaded CID {cid}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  CID {cid} not found")
            return False
    except Exception as e:
        print(f"❌ Error CID {cid}: {str(e)}")
        return False

def main():
    """Main download function"""
    print(f"🚀 PubChem Downloader - GitHub Actions")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load progress
    last_cid, completed = load_progress()
    start = last_cid
    end = min(start + BATCH_SIZE, 16000000)  # Up to CID 16 million
    
    print(f"📊 Downloading CIDs {start:,} to {end:,}")
    print(f"✓ Previously completed: {len(completed)}")
    
    # Download batch
    download_count = 0
    for cid in range(start, end):
        if download_json_locally(cid):
            completed.add(cid)
            download_count += 1
        
        # Save progress every 100 downloads
        if download_count % 100 == 0:
            save_progress(cid, completed)
            
        time.sleep(0.2)  # Rate limit
    
    # Save final progress
    save_progress(end, completed)
    
    print(f"\n✅ Batch complete!")
    print(f"📈 Downloaded {download_count} compounds in this run")
    print(f"📊 Total completed: {len(completed)}")
    print(f"📍 Next run will start at CID {end}")

if __name__ == "__main__":
    main()
