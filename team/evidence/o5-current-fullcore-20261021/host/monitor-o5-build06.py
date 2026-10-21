from pathlib import Path
import json,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021')
with (base/'build06-memory.jsonl').open('x') as log:
    while True:
        memory={line.split(':')[0]:line.split(':',1)[1].strip() for line in Path('/proc/meminfo').read_text().splitlines()}
        rows=[]
        for directory in Path('/proc').glob('[0-9]*'):
            try:
                command=(directory/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
                if 'o5-fullcore-20261021' not in command:continue
                values=dict(line.split(':',1) for line in (directory/'status').read_text().splitlines() if ':' in line)
                rows.append(dict(pid=int(directory.name),command=command,rss=values.get('VmRSS','').strip()))
            except OSError:pass
        log.write(json.dumps(dict(time=time.time(),memory=memory,processes=rows))+'\n');log.flush()
        if (base/'build-launch-06.exit').exists():break
        time.sleep(10)
print('MEMORY_LOG_COMPLETE')
