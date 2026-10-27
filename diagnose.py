"""Read-only diagnostics; does not print your API key."""
import os
from dotenv import load_dotenv
from database import connect
from collectors.youtube import youtube_get
import httpx

load_dotenv()
key = os.getenv('YOUTUBE_API_KEY', '').strip()
print('API key configured:', bool(key and not key.startswith('YOUR_')))
with connect() as conn:
    for table in ('videos','observations','saved','external_reels'):
        print(f'{table}:', conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
if not key or key.startswith('YOUR_'):
    print('Add your key to .env before collecting.')
else:
    try:
        with httpx.Client(timeout=20) as client:
            data = youtube_get(client, '/search', {
                'key': key, 'part': 'snippet', 'q': 'grwm shorts',
                'type': 'video', 'maxResults': 1, 'regionCode': 'IN'
            })
        print('YouTube API connection: OK; results:', len(data.get('items', [])))
    except RuntimeError as exc:
        print('YouTube API connection:', exc)
