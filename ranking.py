"""Conservative, explainable relevance scoring. Does not infer viewer demographics."""
import re
from datetime import datetime, timezone
from config import NEGATIVE_TERMS

TOPICS = {
    'GRWM & beauty': ('grwm','get ready with me','get ready','makeup','skincare','hair tutorial','hair style','glow up'),
    'Dance & lip sync': ('dance challenge','dance trend','dance cover','lip sync','lipsync','mimicry','mimic','acting trend'),
    'Fashion & accessories': ('outfit','ootd','styling','fashion','jewellery','jewelry','accessories','earrings','handbag','saree','kurti'),
    'Festivals & decor': ('diwali','navratri','holi','festive','festival look','festival outfit','christmas decor','festive decor','oktoberfest'),
    'Gen Z comedy & POV': ('pov','relatable','funny girls','girl math','girlhood','meme trend','comedy skit'),
    'Friendship & lifestyle': ('bestie','best friend','friendship','girls night','girls day','girls trip','daily vlog','day in my life'),
    'Gaming GTA & Free Fire': ('gta 5','gta v','gta online','grand theft auto','free fire','freefire'),
    'Photo poses & transitions': ('photo pose','photo poses','outfit transition','transition trend','photo dump','posing ideas','reel transition'),
}
# Explicit hard exclusions, including common false positives.
BLOCK = tuple(set(NEGATIVE_TERMS) | {'food','cooking','recipe','mukbang','election','political','politician','ai influencers','artificial intelligence influencer','ai model tutorial','prompt engineering'})
# Require a strong category signal, not generic 'girl', 'viral', 'shorts' or 'trend'.

def norm(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', str(value).lower())).strip()

def has_term(text, term):
    return re.search(r'(?<!\w)'+re.escape(norm(term))+r'(?!\w)', text) is not None

def classify(title, description='', requested_category=None):
    text=norm(title+' '+(description or '')[:450])
    if any(has_term(text, term) for term in BLOCK):
        return None
    hits={cat:sum(1 for term in terms if has_term(text,term)) for cat,terms in TOPICS.items()}
    category=max(hits,key=hits.get)
    if hits[category]==0:return None
    # Requested category is a query hint, not evidence of relevance.
    if requested_category in hits and hits[requested_category]>0:category=requested_category
    return {'category':category,'relevance':min(hits[category],5),'evidence':', '.join(t for t in TOPICS[category] if has_term(text,t))[:110]}

def curate(df, limit=10):
    """View count dominates; category diversity prevents repetitive picks."""
    if df.empty:return df
    df=df.copy()
    df['match']=df.title.fillna('').map(lambda x:classify(x))
    df=df[df['match'].notna()].copy()
    if df.empty:return df
    df['matched_category']=df['match'].map(lambda m:m['category'])
    df['relevance']=df['match'].map(lambda m:m['relevance'])
    df['why']=df['match'].map(lambda m:m['evidence'])
    df=df.sort_values(['views','relevance'],ascending=[False,False]).drop_duplicates('video_id')
    # Max two per niche; second pass fills remaining slots if diversity is limited.
    selected=[]; counts={}
    for idx,row in df.iterrows():
        cat=row['matched_category']
        if counts.get(cat,0)<2:
            selected.append(idx);counts[cat]=counts.get(cat,0)+1
        if len(selected)>=limit:break
    if len(selected)<limit:
        selected+= [i for i in df.index if i not in selected][:limit-len(selected)]
    return df.loc[selected]
