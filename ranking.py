"""Niche-first, explainable filtering with creator and title diversity."""
import re
from collections import Counter
from difflib import SequenceMatcher
import pandas as pd
from config import CATEGORIES, NEGATIVE_TERMS

TOPICS = {
 'GRWM & beauty': ('schminken','hautpflege','maquillaje','maquiagem','化粧','grwm','get ready with me','makeup','skincare','skin care','hair tutorial','hair routine','beauty routine','glow up'),
 'Dance & lip sync': ('tanz','tanzen','dança','baile','ダンス','dance challenge','dance trend','dance cover','choreography','lip sync','lipsync','lip syncing','dance tutorial'),
 'Fashion & accessories': ('mode','kleidung','schmuck','moda','tenue','ファッション','outfit','ootd','styling','fashion','jewellery','jewelry','accessories','earrings','handbag','saree','kurti','streetwear'),
 'Festivals & decor': ('deko','dekoration','weihnachtsdeko','zimmer deko','decoração','decoración','décoration','diwali decor','diwali decoration','navratri decoration','festive decor','festival decoration','christmas decor','room decor','home decor','festive diy','rangoli','diy decoration','decorating for christmas','diwali lights','home decoration','room decoration','decor ideas','decoration diy','festival decor'),
 'Gen Z comedy & POV': ('lustig','witzig','humor','comédia','comedia','pov','relatable','comedy skit','funny skit','girl math','girlhood','meme','comedy','funny'),
 'Friendship & lifestyle': ('freunde','freundschaft','alltag','amizade','amigos','bestie','best friend','friendship','girls night','girls day','girls trip','daily vlog','day in my life','mini vlog'),
 'Gaming GTA & Free Fire': ('gta 5','gta v','gta online','grand theft auto','free fire','freefire'),
 'Photo poses & transitions': ('foto posen','foto pose','posen ideen','poses fotos','photo pose','photo poses','posing ideas','outfit transition','transition trend','photo dump','reel transition','pose ideas','transition video'),
}
BLOCK = set(NEGATIVE_TERMS) | {'mukbang','politician','prompt engineering','ai model tutorial'}

def norm(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', str(value or '').lower())).strip()

def has_term(text, term):
    return re.search(r'(?<!\w)' + re.escape(norm(term)) + r'(?!\w)', text) is not None

def classify(title, description='', requested_category=None):
    text = norm(title + ' ' + (description or '')[:350])
    if any(has_term(text, term) for term in BLOCK): return None
    hits = {cat: sum(has_term(text, term) for term in terms) for cat,terms in TOPICS.items()}
    if requested_category:
        if requested_category not in hits or not hits[requested_category]: return None
        # Avoid assigning a weak match to a category when another niche is clearly stronger.
        if hits[requested_category] < max(hits.values()): return None
        cat = requested_category
    else:
        cat = max(hits, key=hits.get)
        if not hits[cat]: return None
    return {'category': cat, 'relevance': hits[cat], 'evidence': ', '.join(t for t in TOPICS[cat] if has_term(text,t))[:100]}

def curate(df, limit=10, niche=None, sort_by='Most viewed'):
    if df.empty: return df.copy()
    df = df.copy()
    # Validate niche against the actual video title; a search query label alone isn't proof.
    df['match'] = df.title.fillna('').map(lambda x: classify(x, requested_category=niche))
    df = df[df['match'].notna()].copy()
    if df.empty: return df
    df['matched_category'] = df['match'].map(lambda m:m['category'])
    df['relevance'] = df['match'].map(lambda m:m['relevance'])
    df['why'] = df['match'].map(lambda m:m['evidence'])
    df['views'] = pd.to_numeric(df.views, errors='coerce').fillna(0)
    df['likes'] = pd.to_numeric(df.likes, errors='coerce').fillna(0)
    df['comments'] = pd.to_numeric(df.comments, errors='coerce').fillna(0)
    df['engagement'] = (df.likes + df.comments) / df.views.clip(lower=1)
    df['published_at_sort'] = pd.to_datetime(df.published_at, utc=True, errors='coerce')
    df = df.sort_values('observed_at').drop_duplicates('video_id', keep='last')
    if sort_by == 'Newest':
        df = df.sort_values(['published_at_sort','relevance','views'], ascending=[False,False,False])
    elif sort_by == 'Engagement rate':
        df = df.sort_values(['engagement','views'], ascending=[False,False])
    else:
        df = df.sort_values(['views','relevance'], ascending=[False,False])
    selected=[]; creator_counts=Counter(); titles=[]
    for idx,r in df.iterrows():
        creator = norm(r.channel)
        title = norm(re.sub(r'#\w+', '', str(r.title)))
        if creator_counts[creator] >= 1: continue
        if any(SequenceMatcher(None, title, previous).ratio() >= .78 for previous in titles): continue
        selected.append(idx); creator_counts[creator] += 1; titles.append(title)
        if len(selected) >= limit: break
    return df.loc[selected].drop(columns=['match','published_at_sort'],errors='ignore')
