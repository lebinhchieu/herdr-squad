import re,sys
for p in sys.argv[1:]:
    s=open(p,encoding="utf-8",newline="").read()
    s=re.sub(r"\n{4,}","\n\n\n",s)
    s=re.sub(r"\n\n\n(?=[ \t]+(def|@))","\n\n",s)
    s=re.sub(r"\n+\Z","\n",s)
    open(p,"w",encoding="utf-8",newline="").write(s)
