"""Validate authored textbook, source identities, CPU labs, and Chrome rendering."""
from pathlib import Path
import argparse,ast,json,hashlib,re,sys,subprocess,xml.etree.ElementTree as ET
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[1];Q=R/"_qa";Q.mkdir(exist_ok=True)
sys.path.insert(0,str(R/"labs"))
import run as labs
def static():
    stats=json.loads((R/"_book/build.json").read_text(encoding="utf-8"))
    idx=json.loads((R/"_research/source-index.json").read_text(encoding="utf-8"))
    refs=json.loads((R/"_book/references.json").read_text(encoding="utf-8"))
    ch=json.loads((R/"_book/chapters.json").read_text(encoding="utf-8"))
    for path,f in idx["files"].items():
        raw=(R/"_source/snapshot-ced6857"/path).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==f["sha256"],path
        assert (R/"_book/source"/(path+".html")).exists(),path
    for ref in refs:
        sy=idx["files"][ref["path"]]["symbols"][ref["symbol"]]
        assert (ref["start"],ref["end"])==(sy["start"],sy["end"])
    assert len(ch)==23 and stats["exercises"]==69 and len(refs)==77
    for c in ch:
        assert c["html"].count('class="exercise"')==3,c["n"]
        assert len(c["html"])>2000,c["n"]
        assert c["html"].count("<h3>")>=4,c["n"]
    for p in [R/"labs/run.py",R/"labs/a100_offline.py",R/"_tools/build_textbook.py",R/"_tools/book_diagrams.py"]:
        ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    # Validate internal links and fragment IDs without depending on lxml.
    from html.parser import HTMLParser
    class Page(HTMLParser):
        def __init__(self,text):
            super().__init__(convert_charrefs=True);self.ids=set();self.links=[];self.feed(text)
        def handle_starttag(self,tag,attrs):
            d=dict(attrs)
            if "id" in d:
                assert d["id"] not in self.ids,("duplicate",d["id"])
                self.ids.add(d["id"])
            if tag=="a" and d.get("href"):self.links.append(d["href"])
            if tag=="img" and d.get("src"):self.links.append(d["src"])
    files=[R/"index.html",R/"source.html"]+list((R/"_book/source").rglob("*.html"))
    pages={p.resolve():Page(p.read_text(encoding="utf-8")) for p in files};link_count=0
    for p,page in pages.items():
        for href in page.links:
            if href.startswith("#"):
                assert unquote(href[1:]) in page.ids,(p,href)
                link_count+=1
                continue
            u=urlsplit(href)
            if u.scheme or u.netloc:continue
            dest=(p.parent/unquote(u.path)).resolve() if u.path else p
            assert dest.exists(),(p,href,dest)
            if u.fragment and dest.suffix==".html" and dest in pages:
                assert unquote(u.fragment) in pages[dest].ids,(p,href)
            link_count+=1
    for p in (R/"_book/figures").glob("*.svg"):
        root=ET.parse(p).getroot();assert root.attrib["viewBox"]=="0 0 1200 850"
    old=(R/"_tools/build_vllm.py").read_text(encoding="utf-8")
    assert "(R/'index.html').write_text" not in old and "(R/'README.md').write_text" not in old
    return dict(status="passed",source_files_verified=len(idx["files"]),
        source_symbols_verified=len(refs),internal_links_verified=link_count,
        chapters=len(ch),exercises=stats["exercises"],figures=stats["figures"],
        labs=labs.check(),gpu_script="AST syntax only; not executed")
def browser(page,width=1440,height=1100,png=None):
    return narrow_browser(page,width,height,png)

def narrow_browser(page,width,height,png=None):
    # Chrome on Windows may clamp the native window width. CDP sets CSS viewport exactly.
    import base64,time,urllib.request,websocket
    profile=Q/"textbook-cdp-profile";profile.mkdir(exist_ok=True)
    portfile=profile/"DevToolsActivePort"
    if portfile.exists():portfile.unlink()
    chrome=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    proc=subprocess.Popen([chrome,"--headless","--disable-gpu","--disable-background-networking",
        "--no-first-run","--no-default-browser-check","--allow-file-access-from-files",
        "--remote-debugging-port=0","--user-data-dir="+str(profile),"about:blank"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ws=None
    try:
        deadline=time.monotonic()+15
        while not portfile.exists():
            if time.monotonic()>deadline:raise RuntimeError("Chrome debug port timeout")
            time.sleep(.1)
        port=portfile.read_text().splitlines()[0]
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open("http://127.0.0.1:"+port+"/json/list") as res:targets=json.load(res)
        target=next(x for x in targets if x["type"]=="page")
        ws=websocket.create_connection(target["webSocketDebuggerUrl"],timeout=20,suppress_origin=True)
        seq=0
        def call(method,params=None):
            nonlocal seq
            seq+=1;ws.send(json.dumps(dict(id=seq,method=method,params=params or {})))
            while True:
                msg=json.loads(ws.recv())
                if msg.get("id")==seq:
                    if "error" in msg:raise RuntimeError(msg["error"])
                    return msg.get("result",{})
        call("Page.enable")
        call("Emulation.setDeviceMetricsOverride",dict(width=width,height=height,deviceScaleFactor=1,mobile=True))
        call("Page.navigate",dict(url=page.as_uri()))
        needs_report=page.name.endswith("-test.html") or page.name=="_reader_test.html"
        wait=r"""new Promise(resolve=>{let n=0;function check(){if(document.readyState==='complete'&&(!NEEDS_REPORT||document.getElementById('report'))){setTimeout(()=>resolve(document.documentElement.outerHTML),500)}else if(n++>150){resolve(document.documentElement.outerHTML)}else setTimeout(check,50)}check()})"""
        wait=wait.replace("NEEDS_REPORT","true" if needs_report else "false")
        val=call("Runtime.evaluate",dict(expression=wait,awaitPromise=True,returnByValue=True))
        markup=val["result"]["value"]
        if png:
            image=call("Page.captureScreenshot",dict(format="png",captureBeyondViewport=False))
            Path(png).write_bytes(base64.b64decode(image["data"]))
        from lxml import html
        return html.fromstring(markup)
    finally:
        if ws:ws.close()
        proc.terminate()
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill()

def test_ui():
    html=(R/"index.html").read_text(encoding="utf-8")
    script=r"""
addEventListener('load',async()=>{
 await document.fonts.ready;const errors=[];
 const check=(v,s)=>{if(!v)errors.push(s)};
 check(window.bookReady,'reader script failed');
 check(innerWidth===WIDTH_EXPECTED,'viewport width '+innerWidth);
 if(innerWidth<980){document.getElementById('navtoggle').click();check(document.querySelector('aside nav').getBoundingClientRect().height>0,'mobile navigation')}
 check(document.querySelectorAll('.chapter').length===23,'chapter count');
 check(document.querySelectorAll('.exercise').length===69,'exercise count');
 const sourceCard=document.querySelector('#ch01 details.sourcecard');
 check(!sourceCard.open,'source card initially folded');sourceCard.querySelector('summary').click();
 check(sourceCard.open&&sourceCard.querySelector('a').getBoundingClientRect().height>0,'source details readable');sourceCard.querySelector('summary').click();
 const pause=document.querySelector('#ch01 .reading-pause');pause.querySelector('summary').click();check(pause.open&&pause.querySelector('p').getBoundingClientRect().height>0,'reading pause answer');pause.querySelector('summary').click();
 const cpuGuide=document.getElementById('cpu-guide'),gpuGuide=document.getElementById('a100-guide');
 document.getElementById('open-cpu-guide').click();
 check(cpuGuide.open&&cpuGuide.getBoundingClientRect().height>0,'CPU guide opens');
 check(cpuGuide.textContent.includes('python labs/run.py trace'),'CPU command visible');
 check(cpuGuide.getBoundingClientRect().width<=WIDTH_EXPECTED,'CPU guide width');
 cpuGuide.querySelector('[data-close-guide]').click();check(!cpuGuide.open,'CPU guide closes');
 document.getElementById('open-a100-guide').click();
 check(gpuGuide.open&&gpuGuide.textContent.includes('results/a100.json'),'A100 guide opens with result path');
 check(gpuGuide.getBoundingClientRect().width<=WIDTH_EXPECTED,'A100 guide width');
 document.getElementById('open-a100-chapter').click();await new Promise(r=>setTimeout(r,40));
 check(!gpuGuide.open&&document.querySelector('.chapter.active').id==='ch21','A100 chapter navigation');
 document.getElementById('open-cpu-guide').click();document.getElementById('open-web-trace').click();await new Promise(r=>setTimeout(r,80));
 check(!cpuGuide.open&&document.querySelector('.chapter.active').id==='ch08','CPU web demo navigation');
 const traceRect=document.getElementById('traceplayer').getBoundingClientRect();
 check(traceRect.top>=-2&&traceRect.top<100,'CPU demo scrolled into view '+traceRect.top);
 const nav=[...document.querySelectorAll('nav a')];
 for(const a of nav){location.hash=a.hash;await new Promise(r=>setTimeout(r,2));check(document.querySelector('.chapter.active')?.id===a.hash.slice(1),'nav '+a.hash)}
 location.hash='#ch08';await new Promise(r=>setTimeout(r,8));
 const phases=[];for(const b of document.querySelectorAll('#tracebuttons button')){b.click();phases.push(document.getElementById('tracedetail').textContent)}
 check(phases.length===8,'phase count');check(phases[6].includes('FINISHED_STOPPED'),'finish phase');check(phases[7].includes('REMOVED'),'cleanup phase');
 const input=document.getElementById('search');input.value='num_computed_tokens';input.dispatchEvent(new Event('input'));
 const hits=nav.filter(a=>!a.hidden).length;check(hits>2&&hits<23,'search results');
 input.value='';input.dispatchEvent(new Event('input'));check(nav.every(a=>!a.hidden),'search reset');
 const ex=document.querySelector('#ch08 .exercise');ex.open=true;check(ex.querySelector('p').getBoundingClientRect().height>0,'answer');
 const before=parseFloat(getComputedStyle(document.body).fontSize);document.getElementById('fontup').click();check(parseFloat(getComputedStyle(document.body).fontSize)>before,'font control');document.getElementById('fontdown').click();
 const complete=document.querySelector('#ch08 .complete');complete.click();check(document.querySelector('nav a[href="#ch08"]').classList.contains('done'),'progress');complete.click();
 let overflow=[];for(const c of document.querySelectorAll('.chapter')){location.hash='#'+c.id;await new Promise(r=>setTimeout(r,1));if(document.documentElement.scrollWidth>WIDTH_EXPECTED+2)overflow.push(c.id)}
 check(!overflow.length,'page overflow '+overflow.join(','));
 location.hash='#ch08';await new Promise(r=>setTimeout(r,5));document.querySelectorAll('#tracebuttons button')[1].click();
 const p=document.createElement('pre');p.id='report';p.textContent=JSON.stringify({errors,hits,phases:phases.length,overflow,bookReady:window.bookReady,actualViewport:innerWidth,experimentGuides:true});p.style.display='none';document.body.append(p);
});
"""
    fixture=Q/"textbook-reader-test.html"
    fixture.write_text(html.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">',1).replace("</body>","<script>"+script+"</script></body>"),encoding="utf-8")
    results=[]
    for width in (1440,740,390):
        fixture.write_text(html.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">',1).replace("</body>","<script>"+script.replace("WIDTH_EXPECTED",str(width))+"</script></body>"),encoding="utf-8")
        dom=browser(fixture,width=width)
        rep=json.loads(dom.xpath('//*[@id="report"]/text()')[0]);rep["width"]=width;results.append(rep)
        assert not rep["errors"],rep
    svg_script=r"""
addEventListener('load',async()=>{
 await document.fonts.ready;const results=[];
 for(const svg of document.querySelectorAll('svg')){
  const rect=svg.getBoundingClientRect(),sx=1200/rect.width,sy=850/rect.height;
  const nodes=[...svg.querySelectorAll('text')].map(t=>{const b=t.getBoundingClientRect();return {text:t.textContent,x:(b.x-rect.x)*sx,y:(b.y-rect.y)*sy,w:b.width*sx,h:b.height*sy}});
  const errors=[];
  for(const t of nodes)if(t.x<0||t.y<0||t.x+t.w>1200.2||t.y+t.h>850.2)errors.push({kind:'outside',t});
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
   const a=nodes[i],b=nodes[j],ix=Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x),iy=Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y);
   if(ix>3&&iy>3)errors.push({kind:'overlap',a:a.text,b:b.text});
  }
  results.push({file:svg.dataset.file,texts:nodes.length,errors})
 }
 const p=document.createElement('pre');p.id='report';p.textContent=JSON.stringify(results);p.style.display='none';document.body.append(p)
});
"""
    svgs=[]
    for p in sorted((R/"_book/figures").glob("*.svg")):
        svgs.append(p.read_text(encoding="utf-8").replace("<svg ",f'<svg data-file="{p.name}" ',1))
    fixture=Q/"textbook-svg-test.html"
    fixture.write_text('<!doctype html><meta charset="utf-8"><style>svg{display:block}</style>'+''.join(svgs)+"<script>"+svg_script+"</script>",encoding="utf-8")
    dom=browser(fixture);reps=json.loads(dom.xpath('//*[@id="report"]/text()')[0])
    assert not [r for r in reps if r["errors"]],[r for r in reps if r["errors"]]
    # Source reader exact anchor and dropdown.
    src=R/"_book/source/vllm/v1/engine/core.py.html"
    sourcehtml=src.read_text(encoding="utf-8")
    source_fixture=src.parent/"_reader_test.html"
    src_js="""addEventListener('load',()=>{const s=document.getElementById('symbols');s.value='L589';s.dispatchEvent(new Event('change'));const p=document.createElement('pre');p.id='report';p.textContent=JSON.stringify({hash:location.hash,line:document.getElementById('L589').textContent,options:s.options.length});document.body.append(p)})"""
    source_fixture.write_text(sourcehtml.replace("</html>","<script>"+src_js+"</script></html>"),encoding="utf-8")
    dom=browser(source_fixture);source_report=json.loads(dom.xpath('//*[@id="report"]/text()')[0])
    assert source_report["hash"]=="#L589" and "def step(" in source_report["line"]
    source_fixture.unlink()
    browser(R/"index.html",png=Q/"textbook-desktop.png")
    browser(R/"index.html",width=390,height=1000,png=Q/"textbook-mobile.png")
    shot=Q/"textbook-trace-shot.html"
    shot.write_text(html.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">',1).replace("</body>",'<script>location.hash="#ch08";setTimeout(()=>{document.documentElement.style.scrollBehavior="auto";document.getElementById("traceplayer").scrollIntoView({behavior:"instant"});document.querySelectorAll("#tracebuttons button")[1].click()},300)</script></body>'),encoding="utf-8")
    browser(shot,png=Q/"textbook-trace.png")
    svgshot=Q/"textbook-packing-shot.html"
    svgshot.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0}</style>'+ (R/"_book/figures/packing.svg").read_text(encoding="utf-8"),encoding="utf-8")
    browser(svgshot,width=1200,height=850,png=Q/"textbook-packing.png")
    for guide,width in (("cpu",1440),("a100",390)):
        preview=Q/("textbook-"+guide+"-guide-shot.html")
        fixture_code='<script>addEventListener("load",()=>document.getElementById("open-'+guide+'-guide").click())</script>'
        preview.write_text(html.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">',1).replace("</body>",fixture_code+"</body>"),encoding="utf-8")
        browser(preview,width=width,png=Q/("textbook-"+guide+"-guide.png"))
    return dict(status="passed",viewports=results,svg=reps,source_reader=source_report)
def main():
    p=argparse.ArgumentParser();p.add_argument("--static",action="store_true");args=p.parse_args()
    report={"static":static()}
    if not args.static:report["browser"]=test_ui()
    report["status"]="passed"
    (Q/"textbook-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["static"],ensure_ascii=True),flush=True)
    if not args.static:print("Chrome: 3 viewports, navigation/search/player/answers/progress/source reader and 12 SVG layouts passed.")
if __name__=="__main__":main()
