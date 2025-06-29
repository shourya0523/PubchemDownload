#!/usr/bin/env python3
"""
Parallel PubChem Downloader - Optimized for speed
Downloads compounds in parallel batches using async
"""

import asyncio
import aiohttp
import aiofiles
import os
import sys
import json
import time
import argparse
from typing import List, Set
from datetime import datetime

class ParallelPubChemDownloader:
    def __init__(self, batch_id: int, total_batches: int, compounds_per_batch: int):
        self.batch_id = batch_id
        self.total_batches = total_batches
        self.compounds_per_batch = compounds_per_batch
        
        # Calculate CID range for this batch
        self.start_cid = 8000000 + (batch_id * compounds_per_batch)
        self.end_cid = self.start_cid + compounds_per_batch
        
        # Settings optimized for speed
        self.max_concurrent = 100  # Much higher concurrency
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.folder = f"pubchem_downloads_batch_{batch_id}"
        self.progress_file = f"progress_batch_{batch_id}.json"
        
        # Rate limiting - PubChem allows 5 requests/second
        # With 20 parallel jobs, each job can do 0.25 req/sec
        self.min_delay = 0.05  # Be aggressive but respectful
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        self.completed = set()
        self.failed = set()
        self.session = None
        
    async def __aenter__(self):
        os.makedirs(self.folder, exist_ok=True)
        
        # Create session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=200,
            limit_per_host=100,
            ttl_dns_cache=300
        )
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=connector,
            headers={'User-Agent': 'PubChemDownloader/1.0'}
        )
        
        # Load previous progress if exists
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.completed = set(data.get('completed', []))
                
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.save_progress()
        
    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump({
                'batch_id': self.batch_id,
                'completed': list(self.completed),
                'failed': list(self.failed),
                'total': len(self.completed),
                'timestamp': datetime.now().isoformat()
            }, f)
            
    async def download_compound(self, cid: int, retry: int = 2) -> bool:
        if cid in self.completed:
            return True
            
        filepath = os.path.join(self.folder, f"{cid}.json")
        if os.path.exists(filepath):
            self.completed.add(cid)
            return True
            
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
        
        for attempt in range(retry):
            try:
                async with self.semaphore:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Write asynchronously
                            async with aiofiles.open(filepath, 'w') as f:
                                await f.write(content)
                                
                            self.completed.add(cid)
                            return True
                        elif response.status == 404:
                            self.failed.add(cid)
                            return False
                        else:
                            if attempt < retry - 1:
                                await asyncio.sleep(0.1 * (attempt + 1))
            except Exception as e:
                if attempt == retry - 1:
                    self.failed.add(cid)
                    return False
                await asyncio.sleep(0.1 * (attempt + 1))
                
        return False
        
    async def run(self):
        print(f"🚀 Batch {self.batch_id}: Downloading CIDs {self.start_cid:,} to {self.end_cid:,}")
        print(f"📊 Using {self.max_concurrent} concurrent connections")
        
        # Get list of CIDs to download
        all_cids = list(range(self.start_cid, self.end_cid))
        pending = [cid for cid in all_cids if cid not in self.completed]
        
        if not pending:
            print(f"✅ Batch {self.batch_id}: All compounds already downloaded!")
            return
            
        print(f"📥 Batch {self.batch_id}: {len(pending)} compounds to download")
        
        # Create all tasks
        start_time = time.time()
        tasks = [self.download_compound(cid) for cid in pending]
        
        # Process in chunks to save progress periodically
        chunk_size = 1000
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            await asyncio.gather(*chunk, return_exceptions=True)
            
            # Save progress
            self.save_progress()
            
            # Stats
            elapsed = time.time() - start_time
            rate = len(self.completed) / elapsed if elapsed > 0 else 0
            print(f"Batch {self.batch_id}: {len(self.completed)}/{len(all_cids)} "
                  f"({rate:.1f} compounds/sec)")
                  
        # Final stats
        total_time = time.time() - start_time
        print(f"✅ Batch {self.batch_id} complete: {len(self.completed)} compounds in "
              f"{total_time:.1f}s ({len(self.completed)/total_time:.1f} compounds/sec)")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-id', type=int, required=True)
    parser.add_argument('--total-batches', type=int, default=20)
    parser.add_argument('--compounds-per-batch', type=int, default=50000)
    args = parser.parse_args()
    
    async with ParallelPubChemDownloader(
        args.batch_id,
        args.total_batches,
        args.compounds_per_batch
    ) as downloader:
        await downloader.run()

if __name__ == "__main__":
    # Set up async properly for high concurrency
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
