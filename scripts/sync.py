import json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,urljoin
import requests
from bs4 import BeautifulSoup
base='https://air.iuav.it/browse'
items={}
for offset in range(0,2000,20):
    params={'authority':'rp02823','type':'author','order':'ASC','sort_by':2,'rpp':20,'offset':offset}
    response=requests.get(base,params=params,timeout=45,headers={'User-Agent':'Academic personal bibliography sync (daily)'})
    response.raise_for_status()
    soup=BeautifulSoup(response.text,'html.parser')
    count=0; new=0
    for row in soup.select('tr'):
        cells=row.find_all('td',recursive=False)
        if len(cells)<3: continue
        a=cells[0].find('a',href=True)
        if not a or '/handle/' not in a['href']: continue
        year=re.search(r'\b(?:19|20)\d{2}\b',cells[1].get_text(' ',strip=True))
        if not year: continue
        url=urljoin(base,a['href']); authors=cells[2].get_text(' ',strip=True)
        if 'casarotto' not in authors.lower(): raise RuntimeError('Unexpected author in AIR response')
        count+=1
        if url not in items: new+=1
        items[url]={'title':a.get_text(' ',strip=True),'year':year.group(),'authors':authors,'url':url}
    if not count or not new: raise RuntimeError('Unexpected empty or repeated AIR page; keeping previous snapshot')
    if count<20: break
    # Stop on a final page whose summary says all results have been shown.
    summary=re.search(r'(?:risultati|results).*?(\d+)\s*(?:a|to|-)\s*(\d+)\s*(?:di|of)\s*(\d+)',soup.get_text(' ',strip=True),re.I)
    if summary and int(summary[2])>=int(summary[3]): break
    time.sleep(2)
else: raise RuntimeError('Pagination limit reached')
path=Path('data/publications.json'); old=json.loads(path.read_text());
if len(items)<len(old['items']): raise RuntimeError('Incomplete snapshot')
path.write_text(json.dumps({'syncedAt':datetime.now(timezone.utc).isoformat(),'items':sorted(items.values(),key=lambda p:(p['year'],p['title']),reverse=True)},ensure_ascii=False,indent=2)+'\n')
