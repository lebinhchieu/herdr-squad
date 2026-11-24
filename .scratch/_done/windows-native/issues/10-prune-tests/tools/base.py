import subprocess,sys,time,os,re
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
for f in sys.argv[1:]:
    t=time.time()
    p=subprocess.run([sys.executable,"-m","unittest","-q","test_"+f],capture_output=True,text=True)
    o=p.stderr+p.stdout
    m=re.search(r"Ran (\d+) tests? in",o); r=o.strip().splitlines()[-1] if o.strip() else ""
    print(f"{f} | {time.time()-t:.1f}s | ran {m.group(1) if m else '?'} | {r}",flush=True)
