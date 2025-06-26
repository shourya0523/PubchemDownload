import json
import os
from datetime import datetime

def check_status():
    """Check download progress"""
    if os.path.exists("progress.json"):
        with open("progress.json", 'r') as f:
            data = json.load(f)
        
        last_cid = data.get('last_cid', 0)
        completed = len(data.get('completed', []))
        updated = data.get('updated', 'Unknown')
        
        print("📊 PubChem Download Status")
        print("=" * 40)
        print(f"📍 Last CID processed: {last_cid:,}")
        print(f"✅ Total downloaded: {completed:,}")
        print(f"📅 Last updated: {updated}")
        
        # Estimate completion
        if last_cid > 0:
            # Assuming we want to download up to CID 16,000,000
            total_target = 16_000_000 - 8_000_000
            progress_pct = ((last_cid - 8_000_000) / total_target) * 100
            print(f"📈 Progress: {progress_pct:.1f}%")
            
            # Estimate time remaining
            # Each run does 5000 CIDs, runs every 6 hours
            remaining = 16_000_000 - last_cid
            runs_needed = remaining / 5000
            days_needed = (runs_needed * 6) / 24
            print(f"⏱️  Estimated days remaining: {days_needed:.1f}")
    else:
        print("❌ No progress file found. Has the workflow run yet?")

if __name__ == "__main__":
    check_status()