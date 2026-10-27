import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import streamlit as st
from dotenv import load_dotenv
from database import connect
from config import CATEGORIES, MARKETS
from ranking import curate

load_dotenv()
st.set_page_config(page_title='Trend Hunter | Culture Radar',page_icon='✦',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 85% 0%,#163c65 0%,transparent 43%),#06101e;color:#eaf4ff}
[data-testid="stSidebar"]{background:linear-gradient(160deg,#102c4b,#081626)}
h1,h2,h3{letter-spacing:-.03em}h1{color:#f2d7a2!important}
[data-testid="stMetric"]{background:#173452aa;border:1px solid #c7a56b66;border-radius:16px;padding:12px}
[data-testid="stVerticalBlockBorderWrapper"]{background:#12294177;border:1px solid #719ac04a!important;border-radius:18px!important}
.stButton button{border-radius:12px}
</style>''',unsafe_allow_html=True)

PUBLIC=os.getenv('PUBLIC_MODE','false').lower()=='true'
admin_key=os.getenv('ADMIN_KEY','')
with st.sidebar:
    st.markdown('### ✦ TREND HUNTER')
    page=st.radio('Navigate',['✦ Discover','▥ Trend signals','♡ Saved archive','◎ Instagram references','⚙ Sources'])
    st.markdown('#### Discovery filters')
    market=st.selectbox('Region (independent of niche)',['All regions']+list(MARKETS))
    niche=st.selectbox('Niche',['All niches']+list(CATEGORIES))
    sort_by=st.selectbox('Sort videos by',['Most viewed','Newest','Engagement rate'])
    st.caption('Up to 10 distinct creators per niche. India, Germany and Global use different searches; viewer geography is not verified.')
    can_edit=not PUBLIC
    if PUBLIC:
        typed=st.text_input('Admin password (for saving)',type='password')
        can_edit=bool(admin_key and typed==admin_key)
        st.caption('Viewing is public. Editing requires admin password.')

st.title('✦ TREND HUNTER')
st.caption('GEN Z CULTURE RADAR / REGIONAL DISCOVERY POOLS / YOUTUBE SHORTS + INSTAGRAM REFERENCES')
with connect() as db:
    rows=[dict(r) for r in db.execute('''SELECT v.video_id,v.title,v.channel,v.url,v.published_at,v.duration_seconds,o.market,o.category,o.views,o.likes,o.comments,o.observed_at FROM observations o JOIN videos v ON v.video_id=o.video_id ORDER BY o.observed_at DESC''')]
    saved={r['video_id'] for r in db.execute('SELECT video_id FROM saved')}
    refs=[dict(r) for r in db.execute('SELECT * FROM external_reels ORDER BY created_at DESC')]

df=pd.DataFrame(rows)
if not df.empty:
    df['observed_at']=pd.to_datetime(df['observed_at'],utc=True,errors='coerce')
    df['published_at']=pd.to_datetime(df['published_at'],utc=True,errors='coerce')
    cutoff=pd.Timestamp.now(tz='UTC')-pd.Timedelta(days=7)
    df=df[(df['published_at']>=cutoff) & (pd.to_numeric(df['duration_seconds'],errors='coerce').between(1,180))].copy()
    if market!='All regions':df=df[df.market==market].copy()
    # Keep latest observation for each video in each niche; don't count snapshots repeatedly.
    df=df.sort_values('observed_at').drop_duplicates(['video_id','category'],keep='last')

def toggle(vid):
    if not can_edit:st.warning('Enter the admin password to edit the shared archive.');return
    with connect() as db:
        if vid in saved:db.execute('DELETE FROM saved WHERE video_id=?',(vid,))
        else:db.execute('INSERT OR IGNORE INTO saved(video_id) VALUES(?)',(vid,))
    st.rerun()

def card(r, prefix):
    vid=r['video_id']
    with st.container(border=True):
        st.image(f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',use_container_width=True)
        st.markdown('**'+str(r['title'])[:110]+'**')
        st.caption(f"{r['channel']} · {r['market']} · {int(r['duration_seconds'] or 0)} sec")
        st.markdown(f"**{int(r['views']):,} views** · {int(r['likes']):,} likes")
        if r.get('why'):st.caption('Niche match: '+r['why'])
        if can_edit and st.button('♥ Saved' if vid in saved else '♡ Save',key=f'{prefix}_{vid}'):
            toggle(vid)
        # Click-to-play directly in the card, without an extra expander.
        st.video(f'https://www.youtube.com/watch?v={vid}')
        st.link_button('Open on YouTube',f'https://www.youtube.com/watch?v={vid}')

def gallery(data,prefix):
    if data.empty:return
    for i in range(0,len(data),3):
        columns=st.columns(3)
        for col,(_,r) in zip(columns,data.iloc[i:i+3].iterrows()):
            with col:card(r,prefix)

def get_niche(category):
    if df.empty:return pd.DataFrame()
    subset=df[df.category==category].copy()
    if subset.empty:return subset
    # This check prevents search-region or keyword-only miscategorization.
    return curate(subset,limit=10,niche=category,sort_by=sort_by)

if page=='✦ Discover':
    st.subheader('Discover · 10 per niche')
    st.caption('Last 7 days · 1–180 sec Shorts candidates · independent niches and region discovery pools. Public views are worldwide totals, not region-specific.')
    categories=list(CATEGORIES) if niche=='All niches' else [niche]
    sections={cat:get_niche(cat) for cat in categories}
    total=sum(len(x) for x in sections.values())
    a,b,c=st.columns(3)
    a.metric('Videos shown',total)
    b.metric('Niches selected',len(categories))
    c.metric('Saved trends',len(saved))
    for category,items in sections.items():
        st.markdown('---')
        st.subheader(f'{category} · {len(items)}/10')
        if items.empty:
            st.info('No qualifying videos collected for this niche and region yet. The next targeted collection may add results; no unrelated videos are substituted.')
        else:
            if len(items)<10:st.caption(f'Only {len(items)} distinct, matching creators available. More targeted collection is needed to reach 10.')
            gallery(items,'discover_'+category)
elif page=='▥ Trend signals':
    st.subheader('Niche coverage')
    categories=list(CATEGORIES) if niche=='All niches' else [niche]
    coverage=pd.DataFrame([{'Niche':cat,'Distinct matching videos':len(get_niche(cat)),'Target':10} for cat in categories])
    st.dataframe(coverage,hide_index=True,use_container_width=True)
    st.bar_chart(coverage.set_index('Niche')['Distinct matching videos'])
    st.caption('This chart counts distinct selected videos, not summed view counts or inferred audience demographics.')
elif page=='♡ Saved archive':
    st.subheader('Your shared inspiration vault')
    with connect() as db:
        archive=[dict(r) for r in db.execute('''SELECT v.video_id,v.title,v.channel,v.url,v.published_at,v.duration_seconds,COALESCE(MAX(o.views),0) views,COALESCE(MAX(o.likes),0) likes,COALESCE(MAX(o.comments),0) comments,MAX(o.market) market,MAX(o.category) category FROM saved s JOIN videos v ON s.video_id=v.video_id LEFT JOIN observations o ON o.video_id=v.video_id GROUP BY v.video_id,s.saved_at ORDER BY s.saved_at DESC''')]
    if not archive:st.info('No saved videos yet.')
    else:gallery(pd.DataFrame(archive),'saved')
elif page=='◎ Instagram references':
    st.subheader('Instagram inspiration')
    st.info('Manual references only; Instagram-wide trend statistics are not automatically collected.')
    if can_edit:
        with st.form('add_reference'):
            url=st.text_input('Instagram Reel URL')
            title=st.text_input('Trend name / description')
            category=st.selectbox('Category',list(CATEGORIES))
            loc=st.selectbox('Market',list(MARKETS))
            submitted=st.form_submit_button('Save reference')
        if submitted:
            if url.startswith(('https://www.instagram.com/reel/','https://instagram.com/reel/')):
                with connect() as db:db.execute('INSERT OR IGNORE INTO external_reels(platform,url,title,category,market) VALUES(?,?,?,?,?)',('Instagram',url,title,category,loc))
                st.rerun()
            else:st.error('Use an Instagram Reel URL.')
    for ref in refs:
        with st.container(border=True):
            st.markdown('**'+(ref['title'] or 'Instagram Reel')+'**')
            st.caption(f"{ref['category']} · {ref['market']}")
            st.link_button('View on Instagram',ref['url'])
else:
    st.subheader('Sources and limitations')
    st.write('YouTube Shorts-oriented search, published in the last 7 days, with a 1–180-second duration limit. YouTube Data API does not expose a definitive Shorts flag; some regular short videos may be included.')
    st.write('India uses India-targeted searches, Germany uses Germany-targeted searches, and Global rotates through US, GB, BR, JP, FR, KR, MX and CA. This is a discovery approximation, not a ranking by viewer geography.')
    st.write('Each morning/evening collection searches all 8 niches for each of 3 pools (24 searches per run; approximately 2,400 YouTube search quota units per run, plus video details).')
    st.write('Saved videos and observations are stored in Supabase when SUPABASE_DB_URL is configured.')
    st.write('Video preview is click-to-play. Browser autoplay on hover is not guaranteed.')
    st.code('python collect.py --batch morning\npython collect.py --batch evening')
