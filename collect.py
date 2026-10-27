import argparse
from datetime import datetime,timezone
from config import CATEGORIES,MARKETS
from ranking import classify
from collectors.youtube import fetch
from database import connect

def eligible(video):
    return classify(video['title'],video.get('description','')) is not None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--batch',choices=['morning','evening'],required=True);args=parser.parse_args()
    pairs=[(market,code,category,terms) for market,code in MARKETS.items() for category,terms in CATEGORIES.items()]
    selected=pairs[::2] if args.batch=='morning' else pairs[1::2]
    conn=connect();now=datetime.now(timezone.utc).isoformat();total=0
    for market,code,category,terms in selected:
        try:
            query=terms[0] if args.batch=='morning' else terms[-1]
            rows=[v for v in fetch(query,code) if eligible(v)]
            with conn:
                for v in rows:
                    conn.execute('''INSERT INTO videos(video_id,title,channel,published_at,url,duration_seconds,last_seen) VALUES(?,?,?,?,?,?,?) ON CONFLICT(video_id) DO UPDATE SET title=excluded.title,channel=excluded.channel,last_seen=excluded.last_seen''',(v['video_id'],v['title'],v['channel'],v['published_at'],v['url'],v['duration_seconds'],now))
                    conn.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?)',(v['video_id'],market,category,now,v['views'],v['likes'],v['comments']))
            total+=len(rows);print(f'{market} / {category}: {len(rows)} relevant candidates')
        except Exception as exc:
            print(f'ERROR {market} / {category}: {exc}')
            if any(x in str(exc).lower() for x in ('api key not valid','keyinvalid','accessnotconfigured','quotaexceeded','dailylimitexceeded','api_key_invalid','permission_denied')):
                print('Stopping batch because the API configuration or quota needs attention.')
                break
    conn.close();print(f'Collected {total} category matches; dashboard curates top ten.')
if __name__=='__main__':main()
