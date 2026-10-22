from pathlib import Path
import datetime,hashlib,json,subprocess,time
w=Path(__file__).resolve().parent
while json.loads((w/'runs/jade-build/build.json').read_text())['status']=='RUNNING':
    time.sleep(5)
for variant in ('shishui','redoop'):
    repo=w/'variants'/variant;out=w/'runs'/(variant+'-build');out.mkdir(exist_ok=False)
    script='export JAVA_HOME=/opt/graalvm-jdk-21\nexport PATH=$JAVA_HOME/bin:/usr/local/llvm/bin:$PATH\nexport NOOP_HOME='+str(repo)+'\nexport DRAMSIM3_HOME=/home/riscv/riscv-lab/xs-env/DRAMsim3\nexport VDOT_T13_TRACE=1\nmake emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G OPT_FAST=-O3 OPT_SLOW=-O0 -j8'
    cmd=['bash','-c',script]
    d={'command':cmd,'cwd':str(repo),'started':datetime.datetime.now().astimezone().isoformat(),'status':'RUNNING'}
    (out/'build.json').write_text(json.dumps(d,indent=2))
    with (out/'build.log').open('w') as log:
        proc=subprocess.Popen(cmd,cwd=repo,stdout=log,stderr=subprocess.STDOUT)
        collected=set()
        while proc.poll() is None:
            processes={}
            for stat in Path('/proc').glob('[0-9]*/status'):
                try:
                    values=dict(line.split(':',1) for line in stat.read_text().splitlines())
                    processes[int(stat.parent.name)]=(int(values['PPid']),values['Name'].strip())
                except (OSError,ValueError,KeyError):pass
            for pid,(parent,name) in processes.items():
                if name!='firtool':continue
                lineage=[];at=parent
                while at in processes and at!=proc.pid:
                    lineage.append(at);at=processes[at][0]
                if at!=proc.pid:continue
                for java in reversed(lineage):
                    if processes[java][1]=='java' and java not in collected:
                        collected.add(java)
                        try:subprocess.run(['/opt/graalvm-jdk-21/bin/jcmd',str(java),'GC.run'],stdout=log,stderr=subprocess.STDOUT,timeout=60)
                        except (OSError,subprocess.TimeoutExpired) as exc:log.write('GC housekeeping: '+repr(exc)+'\n')
            time.sleep(5)
        r=proc
    d.update(status='PASS' if r.returncode==0 else 'FAIL',exit_code=r.returncode,finished=datetime.datetime.now().astimezone().isoformat())
    if r.returncode==0:d['emu_sha256']=hashlib.sha256((repo/'build/emu').read_bytes()).hexdigest()
    (out/'build.json').write_text(json.dumps(d,indent=2));print(variant,d['status'],flush=True)
