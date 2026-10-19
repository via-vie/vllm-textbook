from verify_textbook import R,Q,browser
text=(R/"index.html").read_text(encoding="utf-8")
for name,chapter,heading,width in [
    ("chapter04","ch04",None,1440),
    ("kv-derivation","ch04","4.4",1440),
    ("softmax-derivation","ch14","14.3",1440),
    ("chapter04-mobile","ch04",None,390)]:
    js='addEventListener("load",async()=>{location.hash="#'+chapter+'";await document.fonts.ready;setTimeout(()=>{'
    if heading:
        js+='[...document.querySelectorAll("#'+chapter+' h3")].find(h=>h.textContent.startsWith("'+heading+'")).scrollIntoView({behavior:"instant"});'
    else:js+='window.scrollTo({top:0,behavior:"instant"});'
    js+='},60)});'
    fixture=Q/("readability-"+name+"-shot.html")
    fixture.write_text(text.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="../">',1).replace("</body>","<script>"+js+"</script></body>"),encoding="utf-8")
    browser(fixture,width=width,height=1100,png=Q/("readability-"+name+".png"))
print("Readability previews captured.")
