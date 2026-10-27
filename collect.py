"""One targeted search per niche per region per run; morning/evening rotate queries."""
import argparse
from datetime import datetime,timezone
from config import CATEGORIES,MARKETS,REGIONAL_QUERIES,GLOBAL_REGION_ROTATION
from ranking import classify
from collectors.youtube import fetch
from database import connect

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--batch',choices=['morning','evening'],required=True)
    args=parser.parse_args()
    now=datetime.now(timezone.utc).isoformat(); total=0; errors=0
    # Rotate global region daily; a global pool is sampled, not a platform-wide ranking.
    global_region=GLOBAL_REGION_ROTATION[datetime.now(timezone.utc).date().toordinal() % len(GLOBAL_REGION_ROTATION)]
    for market,code in MARKETS.items():
        for category,queries in CATEGORIES.items():
            local_queries=REGIONAL_QUERIES[market][category]
            query=local_queries[0] if args.batch=='morning' else local_queries[-1]
            search_region=global_region if market=='Global' else code
            try:
                candidates=fetch(query,search_region)
                rows=[v for v in candidates if classify(v['title'],v.get('description',''),requested_category=category)]
                with connect() as conn:
                    for v in rows:
                        conn.execute('''INSERT INTO videos(video_id,title,channel,published_at,url,duration_seconds,last_seen) VALUES(?,?,?,?,?,?,?) ON CONFLICT(video_id) DO UPDATE SET title=excluded.title,channel=excluded.channel,last_seen=excluded.last_seen''',(v['video_id'],v['title'],v['channel'],v['published_at'],v['url'],v['duration_seconds'],now))
                        conn.execute('INSERT OR IGNORE INTO observations(video_id,market,category,observed_at,views,likes,comments) VALUES(?,?,?,?,?,?,?)',(v['video_id'],market,category,now,v['views'],v['likes'],v['comments']))
                total+=len(rows)
                print(f'{market} (search {search_region}) / {category}: {len(rows)} relevant of {len(candidates)} candidates')
            except Exception as exc:
                errors+=1
                print(f'ERROR {market} / {category}: {type(exc).__name__}: {str(exc)[:160]}')
                if 'quota' in str(exc).lower() or 'dailylimit' in str(exc).lower():
                    raise RuntimeError('YouTube API quota exhausted; collection stopped') from None
    print(f'Collected {total} category matches across 24 niche-region searches; {errors} failed searches.')
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
