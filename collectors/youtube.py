import os, re
from datetime import datetime, timedelta, timezone
import httpx
from dotenv import load_dotenv
load_dotenv()
BASE='https://www.googleapis.com/youtube/v3'

def youtube_get(client, endpoint, params):
    """Never include API keys or request URLs in diagnostic output."""
    try:
        response = client.get(BASE + endpoint, params=params)
    except httpx.RequestError as exc:
        raise RuntimeError(f'YouTube connection failed ({type(exc).__name__})') from None
    if response.is_error:
        try:
            detail = response.json().get('error', {})
            message = detail.get('message', 'No explanation returned')
            errors = detail.get('errors') or []
            reason = errors[0].get('reason', 'unknown') if errors else detail.get('status', 'unknown')
        except (ValueError, TypeError, AttributeError, KeyError):
            message, reason = 'Non-JSON API response', 'unknown'
        # Google error messages should not contain keys, but sanitize defensively.
        key = str(params.get('key', ''))
        if key:
            message = str(message).replace(key, '[REDACTED]')
        raise RuntimeError(f'YouTube API HTTP {response.status_code}: {message} (reason: {reason})') from None
    try:
        return response.json()
    except ValueError:
        raise RuntimeError('YouTube returned invalid JSON') from None

def duration_seconds(iso):
    m=re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?',iso or '')
    if not m:return None
    d,h,minute,sec=(int(x or 0) for x in m.groups())
    return 86400*d+3600*h+60*minute+sec

def fetch(query,region=None,limit=20):
    key=os.getenv('YOUTUBE_API_KEY')
    if not key or key.startswith('YOUR_') or key=='replace_with_your_key':raise RuntimeError('Add YOUTUBE_API_KEY to .env')
    after=(datetime.now(timezone.utc)-timedelta(days=10)).isoformat().replace('+00:00','Z')
    params={'key':key,'part':'snippet','q':query,'type':'video','videoDuration':'short','publishedAfter':after,'order':'viewCount','maxResults':min(limit,50),'safeSearch':'moderate'}
    if region:params['regionCode']=region
    with httpx.Client(timeout=35) as client:
        data=youtube_get(client,'/search',params)
        ids=[i['id']['videoId'] for i in data.get('items',[]) if i.get('id',{}).get('videoId')]
        if not ids:return []
        data=youtube_get(client,'/videos',{'key':key,'part':'snippet,statistics,contentDetails','id':','.join(ids)})
    rows=[]
    for item in data.get('items',[]):
        s=item.get('snippet',{});stats=item.get('statistics',{});seconds=duration_seconds(item.get('contentDetails',{}).get('duration'))
        if seconds is None or seconds>180:continue
        vid=item['id']
        rows.append({'video_id':vid,'title':s.get('title',''),'description':s.get('description',''),'channel':s.get('channelTitle',''),'published_at':s.get('publishedAt',''),'url':f'https://www.youtube.com/watch?v={vid}','thumbnail':f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg','duration_seconds':seconds,'views':int(stats.get('viewCount',0)),'likes':int(stats.get('likeCount',0)),'comments':int(stats.get('commentCount',0))})
    return rows
