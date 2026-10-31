import sys
# usage: python addrows.py <file-with-rows>; rows: file|test|rule|reason|covered
out=".scratch/windows-native/issues/10-prune-tests/removed.tsv"
with open(out,"a",encoding="utf-8",newline="") as o:
    for l in open(sys.argv[1],encoding="utf-8"):
        l=l.rstrip("\n")
        if not l: continue
        f,t,r,w,c=l.split("|")
        o.write(f"{f}::{t}\t{r}\t{w}\t{c}\n")
