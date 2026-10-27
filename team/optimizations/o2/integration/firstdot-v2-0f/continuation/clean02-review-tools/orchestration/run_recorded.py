from pathlib import Path
import datetime,json,subprocess,sys,os
record=Path(sys.argv[1]);cwd=sys.argv[2];command=sys.argv[3:]
record.parent.mkdir(parents=True,exist_ok=True)
value=dict(command=command,cwd=cwd,started=datetime.datetime.now().astimezone().isoformat(),pid=os.getpid())
record.write_text(json.dumps(value,indent=2))
with record.with_suffix(".stdout.log").open("wb") as out, record.with_suffix(".stderr.log").open("wb") as err:
 p=subprocess.Popen(command,cwd=cwd,stdout=out,stderr=err)
 value["child_pid"]=p.pid;record.write_text(json.dumps(value,indent=2))
 rc=p.wait()
value.update(exit_code=rc,finished=datetime.datetime.now().astimezone().isoformat())
record.write_text(json.dumps(value,indent=2))
raise SystemExit(rc)
