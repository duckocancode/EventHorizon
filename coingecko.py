import ccxt
import requests
import pandas as pd
import time
import json
import os
import sys

# ==========================================
# 🔧 CONFIG
# ==========================================
API_BASE = "https://api.coingecko.com/api/v3"
API_KEY = "CG-H2mM3QvKvydn1huRAYVG2dMw"
CHUNK_SIZE = 150
OUTPUT_FILE = "sectors.csv"
CACHE_FILE = "cg_cache.json"
BATCH_DELAY = 2.0
RETRY_DELAY = 10
MAX_RETRIES = 3
# ==========================================

headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": API_KEY
}

print("📂 Current working directory:", os.getcwd())

# ---------- handle refresh flag ----------
REFRESH = "--refresh" in sys.argv
if REFRESH and os.path.exists(CACHE_FILE):
    os.remove(CACHE_FILE)
    print("♻️  Cache cleared (refresh mode)")

# ---------- STEP 1. load Binance pairs ----------
print("📡 Loading Binance markets...")
ex = ccxt.binance()
markets = ex.load_markets()
symbols = [s for s in markets if s.endswith('/USDT') and markets[s]['spot']]
coins = [s.split('/')[0].lower() for s in symbols]
print(f"Found {len(symbols)} USDT pairs")

# ---------- STEP 2. get categories with market data ----------
print("📁 Fetching CoinGecko categories (with market data)...")
cat_resp = requests.get(f"{API_BASE}/coins/categories?order=market_cap_desc", headers=headers)
cat_resp.raise_for_status()
all_cats = cat_resp.json()
category_map = {c["id"]: c["name"] for c in all_cats if "id" in c and "name" in c}
print(f"✅ Loaded {len(category_map)} categories with market data")

# ---------- STEP 3. get all coins list ----------
print("📄 Fetching CoinGecko coin list...")
coin_resp = requests.get(f"{API_BASE}/coins/list", headers=headers)
coin_resp.raise_for_status()
all_coins = coin_resp.json()
lookup = {c["symbol"].lower(): c["id"] for c in all_coins if "symbol" in c and "id" in c}

ids = [lookup.get(c) for c in coins if lookup.get(c)]
id_symbol_map = {lookup[c]: s for c, s in zip(coins, symbols) if lookup.get(c)}
print(f"✅ Matched {len(ids)} IDs with CoinGecko")

# ---------- STEP 4. cache ----------
if os.path.exists(CACHE_FILE):
    cache = json.load(open(CACHE_FILE))
    print(f"🧠 Loaded cache with {len(cache)} entries")
else:
    cache = {}

invalid_ids = []


# ---------- helper to fetch & fill categories ----------
def fetch_chunk(id_list):
    if not id_list:
        return []
    joined = ",".join(id_list)
    while len(joined) > 1500 and len(id_list) > 10:
        id_list = id_list[:-10]
        joined = ",".join(id_list)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            url = f"{API_BASE}/coins/markets?vs_currency=usd&ids={joined}"
            r = requests.get(url, headers=headers)
            if r.status_code == 429:
                print(f"⚠️ rate limit hit, waiting {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY)
                continue
            if r.status_code == 400:
                if len(id_list) == 1:
                    bad = id_list[0]
                    cache[bad] = "OTHER"
                    invalid_ids.append(bad)
                    print(f"❌ invalid id: {bad}")
                    return []
                mid = len(id_list)//2
                print(f"⚠️ splitting batch of {len(id_list)}")
                return fetch_chunk(id_list[:mid]) + fetch_chunk(id_list[mid:])
            r.raise_for_status()
            data = r.json()

            for entry in data:
                cg_id = entry.get("id")
                if not cg_id:
                    continue
                if cg_id in cache and cache[cg_id] != "OTHER":
                    continue

                try:
                    detail = requests.get(f"{API_BASE}/coins/{cg_id}", headers=headers)
                    detail.raise_for_status()
                    info = detail.json()
                    cats = info.get("categories", [])
                    if cats:
                        # join multiple categories for CSV readability
                        cache[cg_id] = "; ".join(cats)
                        print(f"🔍 {cg_id}: {cache[cg_id]}")
                    else:
                        cache[cg_id] = "OTHER"
                        print(f"⚪ {cg_id}: no category")
                except Exception as e:
                    print(f"⚠️ Failed to get category for {cg_id}: {e}")
                    cache[cg_id] = "OTHER"
                time.sleep(1.5)

            json.dump(cache, open(CACHE_FILE, "w"))
            return data
        except Exception as e:
            print(f"⚠️ error: {e}")
            time.sleep(RETRY_DELAY)
    return []


# ---------- STEP 5. main batching ----------
for i in range(0, len(ids), CHUNK_SIZE):
    chunk = [cid for cid in ids[i:i + CHUNK_SIZE] if cid and isinstance(cid, str)]
    need = [cid for cid in chunk if cid not in cache or cache[cid] == "OTHER"]
    if not need:
        print(f"⏭️ Batch {i//CHUNK_SIZE+1}: all cached, skipping")
        continue
    print(f"🔹 Batch {i//CHUNK_SIZE+1}: {len(need)} ids")
    fetch_chunk(need)
    print(f"✅ Batch {i//CHUNK_SIZE+1} done ({len(cache)} cached)")
    time.sleep(BATCH_DELAY)

if invalid_ids:
    with open("invalid_ids.txt", "w") as f:
        f.write("\n".join(sorted(set(invalid_ids))))
    print(f"⚠️ Logged {len(invalid_ids)} invalid ids")

# ---------- STEP 6. build sectors.csv ----------
rows = []
for cg_id, symbol in id_symbol_map.items():
    sector = cache.get(cg_id, "UNKNOWN")
    rows.append({"symbol": symbol, "sector": sector})

mapped = {r["symbol"] for r in rows}
for s in symbols:
    if s not in mapped:
        rows.append({"symbol": s, "sector": "UNKNOWN"})

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_FILE, index=False, mode="w")
print(f"\n✅ Done — wrote {len(df)} rows to {os.path.abspath(OUTPUT_FILE)}")

# ---------- STEP 7. summary ----------
sample = list(cache.items())[:10]
print("\n🧾 Sample of cached categories:")
for k, v in sample:
    print(f"• {k}: {v}")
