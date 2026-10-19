from verify_textbook import R,Q,browser
p=Q/"textbook-architecture-shot.html"
p.write_text('<meta charset="utf-8"><style>body{margin:0}</style>'+(R/"_book/figures/architecture.svg").read_text(encoding="utf-8"),encoding="utf-8")
browser(p,width=1200,height=850,png=Q/"textbook-architecture.png")
print("Architecture preview saved")
