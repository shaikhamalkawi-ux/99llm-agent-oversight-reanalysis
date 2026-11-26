import hashlib,html.parser,io,json,re,urllib.parse,urllib.request,zipfile
from pathlib import Path
OUT=Path('/tmp/g19_template');OUT.mkdir(exist_ok=True)
URL='https://www.mdpi.com/authors/latex'
class Links(html.parser.HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.current=[dict(attrs).get('href',''),'']
    def handle_data(self,data):
        if self.current is not None:self.current[1]+=data
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:self.links.append(self.current);self.current=None
def get(u):
    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (compatible; academic template retrieval)'})
    with urllib.request.urlopen(req,timeout=25) as r:
        if not urllib.parse.urlsplit(r.url).hostname.endswith(('.mdpi.com','.overleaf.com')):raise ValueError('unexpected redirect')
        return r.read(40_000_001),r.url
status={'status':'HOLD','publisher_page':URL,'attempts':[]}
candidates=[]
try:
    page,actual=get(URL);p=Links();p.feed(page.decode('utf-8','replace'))
    status['publisher_page_sha256']=hashlib.sha256(page).hexdigest()
    for h,label in p.links:
        u=urllib.parse.urljoin(actual,h)
        if 'zip' in u.lower() and ('latex' in u.lower() or 'template' in u.lower()) and urllib.parse.urlsplit(u).hostname and urllib.parse.urlsplit(u).hostname.endswith('.mdpi.com'):
            candidates.append((u,label.strip()))
except Exception as e:status['page_error']=type(e).__name__+': '+str(e)[:150]
# The publisher listing must identify an ACS/default archive; do not download arbitrary third-party mirrors.
status['publisher_archive_links']=candidates
for u,label in candidates:
    if any(s in (u+' '+label).lower() for s in ('apa','chicago','lyx','word')):continue
    try:
        b,actual=get(u)
        if len(b)>40_000_000:raise ValueError('size limit')
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            if z.testzip() is not None:raise ValueError('bad CRC')
            names=z.namelist()
            cls=[n for n in names if n.lower().endswith('/mdpi.cls') or n=='mdpi.cls']
            tex=[n for n in names if n.lower().endswith('/template.tex') or n=='template.tex']
            if len(cls)!=1 or len(tex)!=1:raise ValueError('missing or ambiguous class/template')
            c=z.read(cls[0]);t=z.read(tex[0])
            if not re.search(rb'\bbdcc\b',c+t):raise ValueError('BDCC not supported')
            status.update({'status':'ACQUIRED_OFFICIAL_PUBLISHER_LINK','source':u,'final_url':actual,'zip_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'class_sha256':hashlib.sha256(c).hexdigest(),'class_header':c[:3500].decode('utf-8','replace'),'files':names})
            (OUT/'MDPI_official_ACS_template.zip').write_bytes(b)
            break
    except Exception as e:status['attempts'].append({'url':u,'error':type(e).__name__+': '+str(e)[:200]})
(OUT/'TEMPLATE_ACQUISITION.json').write_text(json.dumps(status,indent=2)+'\n')
print('G19_TEMPLATE',json.dumps({k:v for k,v in status.items() if k not in ('class_header','files')},sort_keys=True))
