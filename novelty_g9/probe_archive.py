#!/usr/bin/env python3
"""Probe public external archive admission without credentials or access bypass."""
import json,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
runs=['20251209_mini-v1.17.2_devstral-small-2512','20250807_mini-v1.7.0_gpt-5-mini','20250726_mini-v1.0.0_gpt-4.1-2025-04-14']
result={}
for run in runs:
    z={}
    for kind in ('logs','trajs'):
        pref=f'bash-only/{run}/{kind}/'
        url='https://swe-bench-submissions.s3.amazonaws.com/?'+urllib.parse.urlencode({'list-type':'2','prefix':pref,'max-keys':10})
        try:
            with urllib.request.urlopen(url,timeout=25) as r:b=r.read()
            root=ET.fromstring(b)
            keys=[v.text for v in root.findall('.//{*}Key')]
            # Print only structural file types and count, not source task identifiers.
            z[kind]={'list_access':'PASS','sample_count':len(keys),'sample_basenames':[k.rsplit('/',1)[-1] if k.rsplit('/',1)[-1] in ('report.json','test_output.txt','patch.diff','eval.sh','run_instance.log') else '(other)' for k in keys]}
            if keys:
                with urllib.request.urlopen('https://swe-bench-submissions.s3.amazonaws.com/'+urllib.parse.quote(keys[0],safe='/'),timeout=25) as r:
                    raw=r.read(4*1024*1024)
                z[kind]['first_object_access']='PASS';z[kind]['first_object_sample_bytes']=len(raw)
        except Exception as e:z[kind]={'access':'HOLD','reason':type(e).__name__,'http_status':getattr(e,'code',None)}
    result[run]=z
print('G9_ARCHIVE_PROBE',json.dumps(result,sort_keys=True))
Path('/tmp/g9_archive_probe.json').write_text(json.dumps(result,indent=2))
