from pathlib import Path
import json,math,collections,xml.etree.ElementTree as ET,subprocess,sys
R=Path(__file__).resolve().parents[1];Q=R/'_qa';Q.mkdir(exist_ok=True)
D=json.loads((R/'_data/transformer_case.json').read_text(encoding='utf-8'))
T=json.loads((R/'_data/serving_trace.json').read_text(encoding='utf-8'))
C=json.loads((R/'_data/chapters.json').read_text(encoding='utf-8'))
REPORT={'numerical':{},'svg':[],'reader':{}}
checks=0;error=0
def near(a,b):
    global checks,error
    if isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):near(x,y)
    else:
        checks+=1;error=max(error,abs(a-b));assert abs(a-b)<1e-11,(a,b)
prev={};total=0
for t in T['rounds']:
    assert sum(t['schedule'].values())==len(t['input_ids'])<=T['budget']
    assert t['query_start_loc'][0]==0 and t['query_start_loc'][-1]==len(t['input_ids'])
    all_ids=[];all_pos=[];all_slots=[]
    current_fin={e['request'] for e in t['entries'] if e['finished']}
    refs=collections.Counter()
    for name,st in t['states'].items():
        if not st['finished'] or name in current_fin:refs.update(st['blocks'])
    for bid,b in t['pool_before_release'].items():
        assert b['ref']==refs[int(bid)]
        assert not b['hash'] or len(b['tokens'])==T['block_size']
    arrival={a['request']:a for a in t['arrivals']}
    for e in t['entries']:
        name=e['request'];st=t['states'][name];old=prev.get(name);hit=arrival.get(name,{}).get('cached',0)
        assert e['start']==(old['computed'] if old else hit)
        known=(old['ids'] if old else T['requests'][name]['prompt'])
        assert e['input_ids']==known[e['start']:e['end']]
        assert e['positions']==list(range(e['start'],e['end']))
        for p,tok,slot in zip(e['positions'],e['input_ids'],e['slots']):
            phys=e['blocks'][p//2];assert slot==phys*2+p%2
            assert t['pool_before_release'][str(phys)]['tokens'][p%2]==tok
        assert st['computed']==e['end'];assert 1 not in st['ids']
        if e['output'] is not None:assert e['end']==len(known)
        if e['finished']:assert e['output']==1
        all_ids+=e['input_ids'];all_pos+=e['positions'];all_slots+=e['slots']
    assert all_ids==t['input_ids'] and all_pos==t['positions'] and all_slots==t['slot_mapping']
    total+=len(all_ids);prev=t['states']
assert total==14 and prev['B']['hit']==2
assert all(st['finished'] for st in prev.values())
assert [prev[n]['computed'] for n in ('A','B','C')]==[4,4,8]
assert T['rounds'][1]['slot_mapping']==[3,14,6,7]
assert D['first']==8 and D['second']==1
assert max(range(12),key=lambda i:D['prefill']['logits'][-1][i])==8
assert max(range(12),key=lambda i:D['decode']['logits'][0][i])==1
# Reconstruct two-head paged storage independently from per-token K/V.
page_errors=[]
for head in range(2):
    ks=D['prefill']['cache']['K'][head]+D['decode']['k'][head]
    vs=D['prefill']['cache']['V'][head]+D['decode']['v'][head]
    pages={5:(ks[:2],vs[:2]),1:(ks[2:],vs[2:])}
    q=D['decode']['q'][head][0]
    scores=[];values=[];summaries=[]
    for bid in [5,1]:
        K,V=pages[bid];ss=[sum(a*b for a,b in zip(q,k))/math.sqrt(2) for k in K]
        m=max(ss);weights=[math.exp(x-m) for x in ss]
        summaries.append((m,sum(weights),[sum(w*v[j] for w,v in zip(weights,V)) for j in range(2)]))
        scores+=ss;values+=V
    m=max(scores);ww=[math.exp(x-m) for x in scores];prob=[w/sum(ww) for w in ww]
    out=[sum(a*v[j] for a,v in zip(prob,values)) for j in range(2)]
    M=max(c[0] for c in summaries);den=sum(math.exp(c[0]-M)*c[1] for c in summaries)
    merge=[sum(math.exp(c[0]-M)*c[2][j] for c in summaries)/den for j in range(2)]
    near(scores,D['decode']['score'][head][0]);near(prob,D['decode']['A'][head][0])
    near(out,D['decode']['O'][head][0]);near(merge,out)
    near(D['decode']['O'][head][0],D['full']['O'][head][-1])
near(D['decode']['logits'][0],D['full']['logits'][-1])
REPORT['numerical']={'status':'passed','rounds':5,'new_tokens':total,'scalar_checks':checks,'max_abs_error':error,'EOS_not_forwarded':True,'prefix_reuse_tokens':2,'both_attention_heads_verified':True}
files=sorted(R.glob('*.svg'))
assert len(files)==15
for p in files:
    tree=ET.parse(p);root=tree.getroot();ids=[e.attrib['id'] for e in root.iter() if 'id'in e.attrib]
    assert len(ids)==len(set(ids)),p.name
    assert int(root.attrib['width'])==1600
if '--numeric-only' in sys.argv:
    print(json.dumps(REPORT['numerical'],ensure_ascii=True));sys.exit(0)
from lxml import html as LH
from PIL import Image
chrome=Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
profile=Q/'vllm-browser-profile'
def browser(page,width=1600,height=1000,png=None):
    args=[str(chrome),'--headless','--disable-gpu','--disable-background-networking','--no-first-run','--no-default-browser-check','--hide-scrollbars','--force-device-scale-factor=1','--allow-file-access-from-files',f'--user-data-dir={profile}',f'--window-size={width},{height}','--dump-dom','--virtual-time-budget=1800']
    if png:args.append(f'--screenshot={png}')
    p=subprocess.run(args+[page.as_uri()],capture_output=True,timeout=55)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='replace')[-1000:]
    return LH.fromstring(p.stdout.decode('utf-8',errors='replace'))
JS=r'''
addEventListener('load',async()=>{
 await document.fonts.ready;
 const svg=document.querySelector('svg'),r=svg.getBoundingClientRect(),errors=[];
 const nodes=[...svg.querySelectorAll('text')].map(t=>{const b=t.getBoundingClientRect();return {text:t.textContent,x:b.x-r.x,y:b.y-r.y,w:b.width,h:b.height}});
 const height=Number(svg.getAttribute('height'));
 for(const t of nodes)if(t.x<0||t.y<0||t.x+t.w>1600.2||t.y+t.h>height+.2)errors.push({kind:'outside',t});
 for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
  const a=nodes[i],b=nodes[j],ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
  if(ix>3&&iy>3)errors.push({kind:'text-overlap',a:a.text,b:b.text,intersection:[ix,iy]});
 }
 const p=document.createElement('pre');p.id='report';p.style.display='none';p.textContent=JSON.stringify({texts:nodes.length,errors});document.body.append(p);
});'''
for ch in C:
    p=R/ch['file'];fixture=Q/'layout.html'
    fixture.write_text('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}svg{display:block}</style>'+p.read_text(encoding='utf-8')+'<script>'+JS+'</script>',encoding='utf-8')
    dom=browser(fixture,height=ch['height'],png=Q/(p.stem+'.png'))
    rep=json.loads(dom.xpath('//*[@id="report"]/text()')[0]);rep['file']=p.name;REPORT['svg'].append(rep)
    print(json.dumps({'file':p.name,'texts':rep['texts'],'errors':len(rep['errors'])},ensure_ascii=True),flush=True)
reader=(R/'图解版.html').read_text(encoding='utf-8')
TEST=r'''
addEventListener('load',async()=>{
 await document.fonts.ready;
 const report={chapters:document.querySelectorAll('section.chapter').length,nav:document.querySelectorAll('aside a').length,rounds:[]};
 for(const button of document.querySelectorAll('.rounds button')){button.click();report.rounds.push({title:document.getElementById('roundtitle').textContent,packed:document.getElementById('packed').textContent,cards:document.querySelectorAll('.card').length})}
 document.querySelectorAll('.rounds button')[1].click();report.r2=document.getElementById('packed').textContent;
 document.getElementById('zoom').click();report.actualWidth=document.querySelector('.chapter svg').getBoundingClientRect().width;
 document.getElementById('next').click();report.nextHash=location.hash;
 document.getElementById('play').click();report.playStarted=document.getElementById('play').textContent==='暂停';document.getElementById('play').click();
 const p=document.createElement('pre');p.id='report';p.style.display='none';p.textContent=JSON.stringify(report);document.body.append(p);
});'''
fixture=Q/'reader_test.html'
fixture.write_text(reader.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">').replace('</body>','<script>'+TEST+'</script></body>'),encoding='utf-8')
dom=browser(fixture,width=1440,height=1100)
REPORT['reader']=json.loads(dom.xpath('//*[@id="report"]/text()')[0])
# Screenshot the unmodified live reader at desktop and narrow viewport.
browser(R/'图解版.html',width=1440,height=1100,png=Q/'reader_desktop.png')
browser(R/'图解版.html',width=740,height=1100,png=Q/'reader_mobile.png')
assert REPORT['reader']['chapters']==REPORT['reader']['nav']==14
assert len(REPORT['reader']['rounds'])==5 and all(r['cards']==3 for r in REPORT['reader']['rounds'])
assert '[3,14,6,7]' in REPORT['reader']['r2']
assert REPORT['reader']['actualWidth']==1600 and REPORT['reader']['nextHash']=='#fig2'
assert REPORT['reader']['playStarted']
REPORT['status']='passed' if all(not s['errors'] for s in REPORT['svg']) else 'layout-repair-required'
(Q/'validation.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':REPORT['status'],'numerical':REPORT['numerical'],'reader':REPORT['reader']},ensure_ascii=True),flush=True)
assert REPORT['status']=='passed','Inspect _qa/validation.json'
