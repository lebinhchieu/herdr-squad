import ast,sys
for p in sys.argv[1:]:
    src=open(p,encoding="utf-8").read(); t=ast.parse(src)
    names={}
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names: names[(a.asname or a.name).split(".")[0]]=n.lineno
        elif isinstance(n,ast.ImportFrom):
            for a in n.names: names[a.asname or a.name]=n.lineno
    used={n.id for n in ast.walk(t) if isinstance(n,ast.Name)}|{n.value.id for n in ast.walk(t) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name)}
    for k,l in names.items():
        if k not in used and "noqa" not in src.splitlines()[l-1]: print(p,l,"unused",k)
