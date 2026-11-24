import re,sys
p=sys.argv[1]; names=sys.argv[2:]
L=open(p,encoding="utf-8",newline="").read().split("\n")
for n in names:
    i=next((k for k,l in enumerate(L) if re.match(rf"\s*def {n}\(",l)),None)
    if i is None: print("MISSING",n); continue
    ind=len(L[i])-len(L[i].lstrip())
    a=i
    while a>0 and L[a-1].lstrip().startswith("@") and len(L[a-1])-len(L[a-1].lstrip())==ind: a-=1
    j=i+1
    while j<len(L) and (L[j].strip()=="" or len(L[j])-len(L[j].lstrip())>ind): j+=1
    # keep blank line separation: drop trailing blanks belonging to removed block
    while j>i and L[j-1].strip()=="": j-=1
    del L[a:j]
    # collapse blank lines left (3+ blank -> 2 / class-level)
open(p,"w",encoding="utf-8",newline="").write("\n".join(L))
