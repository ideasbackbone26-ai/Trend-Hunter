import os, re
from datetime import datetime, timedelta, timezone
import httpx
from dotenv import load_dotenv
load_dotenv()
BASE='https://www.googleapis.com/youtube/v3'

def youtube_get(client, endpoint, params):
    try: response = client.get(BASE+endpoint,params=params)
    except httpx.RequestError as exc: raise RuntimeError(f'YouTube connection failed ({type(exc).__name__})') from None
    if response.is_error:
        try:
            error=response.json().get('error',{})
            reason=(error.get('errors') or [{}])[0].get('reason','unknown')
        except (ValueError,TypeError,KeyError,IndexError): reason='unknown'
        raise RuntimeError(f'YouTube API HTTP {response.status_code} (reason: {reason})') from None
    return response.json()

def duration_seconds(iso):
    m=re.fullmatch(r'P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?',iso or '')
    if not m:return None
    d,h,minute,sec=(int(x or 0) for x in m.groups())
    return 86400*d+3600*h+60*minute+sec

def fetch(query,region=None,limit=35,days=7):
    key=os.getenv('YOUTUBE_API_KEY')
    if not key or key.startswith('YOUR_'):raise RuntimeError('YOUTUBE_API_KEY is missing')
    after=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat().replace('+00:00','Z')
    params={'key':key,'part':'snippet','q':query if 'shorts' in query.lower() else query + ' shorts','type':'video','videoDuration':'short','publishedAfter':after,'order':'viewCount','maxResults':min(limit,50),'safeSearch':'moderate'}
    if region:params['regionCode']=region
    with httpx.Client(timeout=35) as client:
        data=youtube_get(client,'/search',params)
        ids=[x['id']['videoId'] for x in data.get('items',[]) if x.get('id',{}).get('videoId')]
        if not ids:return []
        data=youtube_get(client,'/videos',{'key':key,'part':'snippet,statistics,contentDetails','id':','.join(ids)})
    result=[]
    for item in data.get('items',[]):
        s=item.get('snippet',{});stats=item.get('statistics',{})
        seconds=duration_seconds(item.get('contentDetails',{}).get('duration'))
        if seconds is None or not 1<=seconds<=180:continue
        vid=item['id']
        result.append({'video_id':vid,'title':s.get('title',''),'description':s.get('description',''),'channel':s.get('channelTitle',''),'published_at':s.get('publishedAt',''),'url':f'https://www.youtube.com/watch?v={vid}','duration_seconds':seconds,'views':int(stats.get('viewCount',0)),'likes':int(stats.get('likeCount',0)),'comments':int(stats.get('commentCount',0))})
    return result
