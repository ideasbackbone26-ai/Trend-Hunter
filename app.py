import os
import pandas as pd
import streamlit as st
from database import connect
from config import CATEGORIES, MARKETS
from ranking import classify, curate
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='Aanya Trend Hunter | Culture Radar',page_icon='✦',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 85% 0%,#163c65 0%,transparent 43%),radial-gradient(ellipse at 4% 75%,#0d3557 0%,transparent 40%),#06101e;color:#eaf4ff}
[data-testid="stSidebar"]{background:linear-gradient(160deg,#102c4b,#081626);border-right:1px solid #4e789955}
h1,h2,h3{letter-spacing:-.035em}h1{color:#f2d7a2!important}
[data-testid="stMetric"]{background:linear-gradient(140deg,#224b72aa,#10203999);border:1px solid #c7a56b66;border-radius:22px;padding:17px;backdrop-filter:blur(16px)}
[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(135deg,#20436355,#081b2caa);border:1px solid #719ac04a!important;border-radius:22px!important;backdrop-filter:blur(18px)}
.stButton button,.stLinkButton a{border-radius:14px;border:1px solid #c8a56a88;background:#173452bb;color:#f8e2b8}
[data-testid="stImage"] img{border-radius:16px;object-fit:cover}
</style>''',unsafe_allow_html=True)

PUBLIC=os.getenv('PUBLIC_MODE','false').lower()=='true'
admin_key=os.getenv('ADMIN_KEY','')
with st.sidebar:
    st.markdown('### ✦ AANYA / CONTROL ROOM')
    page=st.radio('Navigate',['✦ Discover','▥ Trend signals','♡ Saved archive','◎ Instagram references','⚙ Sources'])
    market=st.selectbox('Market',['All','India','Germany','Global'])
    niche=st.selectbox('Niche',['All']+list(CATEGORIES))
    min_views=st.number_input('Minimum public views',min_value=0,value=10000,step=10000)
    st.caption('10 curated picks. No food, politics, or AI influencer content.')
    can_edit=not PUBLIC
    if PUBLIC:
        st.caption('Public view mode · edits require an admin password')
        typed=st.text_input('Admin password (optional)',type='password')
        can_edit=bool(admin_key and typed==admin_key)
    if not PUBLIC:st.caption('Local editing mode')

st.title('✦ AANYA / TREND HUNTER')
st.caption('GEN Z CULTURE RADAR   /   BLUE + GOLD EDITION   /   YOUTUBE SIGNALS + INSTAGRAM REFERENCES')
with connect() as db:
    rows=[dict(r) for r in db.execute('''SELECT v.video_id,v.title,v.channel,v.url,v.published_at,v.duration_seconds,o.market,o.category,o.views,o.likes,o.comments,o.observed_at FROM observations o JOIN videos v ON v.video_id=o.video_id ORDER BY o.observed_at DESC''')]
    saved={r['video_id'] for r in db.execute('SELECT video_id FROM saved')}
    refs=[dict(r) for r in db.execute('SELECT * FROM external_reels ORDER BY created_at DESC')]

df=pd.DataFrame(rows)
if not df.empty:
    df['observed_at']=pd.to_datetime(df.observed_at,utc=True,errors='coerce')
    df=df.sort_values('observed_at').drop_duplicates(['video_id','market','category'],keep='last')
    if market!='All':df=df[df.market==market]
    if niche!='All':df=df[df.category==niche]
    df=df[df.views>=min_views]
    df=curate(df,limit=10)

def toggle(vid):
    if not can_edit:st.warning('Admin access required to change the shared archive.');return
    with connect() as db:
        if vid in saved:db.execute('DELETE FROM saved WHERE video_id=?',(vid,))
        else:db.execute('INSERT OR IGNORE INTO saved(video_id) VALUES(?)',(vid,))
    st.rerun()

def card(r):
    vid=r['video_id']
    with st.container(border=True):
        st.image(f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',use_container_width=True)
        st.markdown('**'+str(r['title'])[:100]+'**')
        st.caption(f"{r.get('matched_category',r['category'])}  ·  {r['market']}  ·  {r['channel']}")
        st.markdown(f"**{int(r['views']):,} views**  ·  {int(r['duration_seconds'] or 0)} sec")
        if r.get('why'):st.caption('Match: '+r['why'])
        st.caption('Audience demographics not verified; market = search region')
        if can_edit and st.button('♥ Saved' if vid in saved else '♡ Save',key='s_'+vid):toggle(vid)
        with st.expander('▶ Play preview'):
            st.video(f'https://www.youtube.com/watch?v={vid}')
            st.link_button('View original',f'https://www.youtube.com/watch?v={vid}')

def gallery(data):
    if data.empty:st.info('No matching candidates. Try lowering minimum views or collecting another batch.');return
    for i in range(0,len(data),3):
        cols=st.columns(3)
        for col,(_,r) in zip(cols,data.iloc[i:i+3].iterrows()):
            with col:card(r)

if page=='✦ Discover':
    a,b,c=st.columns(3)
    a.metric('Curated picks',len(df));b.metric('Saved trends',len(saved));c.metric('Markets',3)
    st.subheader('The Edit · Your top 10')
    st.caption('Ranked primarily by observed public views, with strong niche matching and category variety. Not verified platform-wide trends.')
    gallery(df)
elif page=='▥ Trend signals':
    st.subheader('Niche pulse')
    if df.empty:st.info('Collect data first.')
    else:
        st.bar_chart(df.groupby('matched_category')['views'].sum().sort_values(ascending=False))
        st.caption('Views summed over currently selected videos; not measured growth or demographic reach.')
        st.dataframe(df[['title','matched_category','market','views','relevance']],hide_index=True,use_container_width=True)
elif page=='♡ Saved archive':
    st.subheader('Your inspiration vault')
    # Saved videos should be visible regardless of current market, niche, or minimum views.
    with connect() as db:
        archive=[dict(r) for r in db.execute('''SELECT v.video_id,v.title,v.channel,v.url,v.published_at,v.duration_seconds,COALESCE(MAX(o.views),0) views,MAX(o.market) market,MAX(o.category) category FROM saved s JOIN videos v ON s.video_id=v.video_id LEFT JOIN observations o ON o.video_id=v.video_id GROUP BY v.video_id,s.saved_at ORDER BY s.saved_at DESC''')]
    archive_df=pd.DataFrame(archive)
    if archive_df.empty:st.info('No saved videos yet.')
    else:
        archive_df['why']='Saved by your team'
        gallery(archive_df)
elif page=='◎ Instagram references':
    st.subheader('Instagram inspiration')
    st.info('Free reference mode only: Instagram-wide trend rankings and view counts are not automatically collected.')
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
    st.subheader('Collection & deployment')
    st.write('YouTube: API-key collection. Instagram: manually curated references (no unrestricted API trend feed).')
    st.write('Storage: Supabase PostgreSQL when SUPABASE_DB_URL is set; otherwise local SQLite.')
    st.warning('For public hosting, set PUBLIC_MODE=true and configure ADMIN_KEY privately. Use Supabase for persistent shared storage.')
    st.code('python collect.py --batch morning\npython collect.py --batch evening\nstreamlit run app.py')
