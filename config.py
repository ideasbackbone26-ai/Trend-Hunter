"""Market-specific discovery. Region labels are discovery pools, not verified viewer geography."""
MARKETS = {'India':'IN','Germany':'DE','Global':None}
CATEGORIES = {
 'GRWM & beauty': ['grwm makeup skincare shorts','get ready with me beauty shorts'],
 'Dance & lip sync': ['dance challenge shorts','lip sync trend shorts'],
 'Fashion & accessories': ['outfit styling fashion shorts','jewelry accessories fashion shorts'],
 'Festivals & decor': ['festive home decoration shorts','holiday room decor diy shorts'],
 'Gen Z comedy & POV': ['relatable pov comedy shorts','funny gen z skit shorts'],
 'Friendship & lifestyle': ['best friends lifestyle shorts','day in my life friendship shorts'],
 'Gaming GTA & Free Fire': ['gta 5 gameplay shorts','free fire gameplay shorts'],
 'Photo poses & transitions': ['photo poses posing ideas shorts','outfit transition shorts'],
}
# A single query per region/niche per run. Rotate on morning/evening to control API costs.
REGIONAL_QUERIES = {
 'India': {
  'GRWM & beauty': ['grwm makeup india shorts','get ready with me skincare hindi shorts'],
  'Dance & lip sync': ['bollywood dance challenge shorts','indian dance lip sync shorts'],
  'Fashion & accessories': ['indian outfit styling fashion shorts','saree kurti accessories styling shorts'],
  'Festivals & decor': ['diwali home decoration rangoli shorts','navratri festive decor home shorts'],
  'Gen Z comedy & POV': ['indian relatable pov comedy shorts','hindi funny skit shorts'],
  'Friendship & lifestyle': ['india bestie friendship shorts','indian mini vlog friends shorts'],
  'Gaming GTA & Free Fire': ['gta 5 india gaming shorts','free fire india gameplay shorts'],
  'Photo poses & transitions': ['photo pose ideas india shorts','outfit transition india shorts'],
 },
 'Germany': {
  'GRWM & beauty': ['grwm schminken shorts deutsch','get ready with me skincare germany shorts'],
  'Dance & lip sync': ['tanz challenge shorts deutsch','lip sync trend deutschland shorts'],
  'Fashion & accessories': ['outfit ideen mode shorts deutsch','streetwear styling deutschland shorts'],
  'Festivals & decor': ['herbst deko zimmer shorts','weihnachtsdeko diy shorts deutsch'],
  'Gen Z comedy & POV': ['pov lustig deutsch shorts','relatable comedy deutschland shorts'],
  'Friendship & lifestyle': ['beste freunde vlog shorts deutsch','alltag mini vlog deutschland shorts'],
  'Gaming GTA & Free Fire': ['gta 5 deutsch shorts','free fire deutsch gameplay shorts'],
  'Photo poses & transitions': ['foto posen ideen shorts deutsch','outfit transition deutschland shorts'],
 },
 'Global': CATEGORIES,
}
# Global samples different international discovery markets; never default solely to IN.
GLOBAL_REGION_ROTATION = ('US','GB','BR','JP','FR','KR','MX','CA')
NEGATIVE_TERMS = ('recipe','cooking','street food','mukbang','restaurant','politics','election','minister','president','ai influencer','virtual influencer','ai generated','chatgpt','midjourney','ai tutorial')
