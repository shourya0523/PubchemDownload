# PubChem Downloader

Automatically downloads PubChem compound data using GitHub Actions.

## 🚀 Quick Start

1. Fork this repository
2. Go to Actions tab
3. Click "Download PubChem Data" workflow
4. Click "Run workflow"

The workflow will then run automatically every 6 hours!

## 📊 Check Progress

```bash
python check_status.py
```

## 📥 Download Your Data

1. Go to Actions tab
2. Click on the latest completed workflow
3. Scroll down to "Artifacts"
4. Download `pubchem-data.zip`

## ⚙️ Configuration

Edit `download_pubchem.py`:
- `START_CID`: Starting compound ID (default: 8000000)
- `BATCH_SIZE`: CIDs per run (default: 5000)

## 📈 Progress Tracking

- Downloads 5,000 compounds every 6 hours
- ~20,000 compounds per day
- Full dataset (8M compounds) in ~400 days

## 💡 Tips

- GitHub Actions is completely free for public repos
- Data is saved as artifacts (90 day retention)
- Workflow runs automatically - no need to keep anything open!
- Check Actions tab to monitor progress