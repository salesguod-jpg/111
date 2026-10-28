"""Read-only official RSS diagnostics; no credentials, no source access bypass."""
import json
import requests
import feedparser
SOURCES={
 'fed':'https://www.federalreserve.gov/feeds/press_all.xml',
 'bls':'https://www.bls.gov/feed/bls_latest.rss',
 'bea_apps':'https://apps.bea.gov/rss/rss.xml',
 'bea':'https://www.bea.gov/news/rss.xml',
 'fed_monetary':'https://www.federalreserve.gov/feeds/press_monetary.xml',
 'dol':'https://www.dol.gov/rss/releases.xml',
}
for name,url in SOURCES.items():
    result={'url':url}
    try:
        r=requests.get(url,timeout=20,headers={'User-Agent':'InvestmentIntelligenceHub/1.0 (official public RSS diagnostics)'})
        result.update(http_status=r.status_code,content_type=r.headers.get('Content-Type'),server=r.headers.get('Server'),entries=len(feedparser.parse(r.content).entries) if r.ok else 0)
        # Do not log potentially hostile HTML or follow a challenge/permission barrier.
    except requests.RequestException as exc:result['error']=type(exc).__name__
    print(f'::notice title=Official RSS probe {name}::{json.dumps(result)}')
