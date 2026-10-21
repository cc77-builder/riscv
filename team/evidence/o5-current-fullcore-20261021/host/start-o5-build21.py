from pathlib import Path
import json,os,subprocess,time
base=Path('/home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021');root=base/'repo'
subprocess.run(['git','-C',str(root),'fetch','origin','James_Hotten'],check=True)
subprocess.run(['git','-C',str(root),'checkout','--detach','e2dfda78875d10d03f0ed37203a42b9613f1d5b0'],check=True)
tools=base/'tools';tools.mkdir()
for name,target in {'mill':'/home/amesotten/.cache/codex-rvinno/t06/tools/mill-0.12.3','clang++':'/usr/bin/clang++-19'}.items():(tools/name).symlink_to(target)
(base/'inputs/xs-env/NEMU').symlink_to(base/'inputs/t12/nemu/reference',target_is_directory=True)
env={k:v for k,v in os.environ.items() if k in ('HOME','PATH')}
env.update(PATH=str(tools)+':'+env['PATH'],JAVA_HOME='/usr/lib/jvm/java-21-openjdk-amd64',JAVA_OPTS='-Xmx1g -XX:ActiveProcessorCount=2',JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2',COURSIER_REPOSITORIES='https://repo.maven.apache.org/maven2',TEAM_XS_ENV_ROOT=str(base/'inputs/xs-env'))
(base/'native-environment.json').write_text(json.dumps(env,indent=2)+'\n')
command=['python3','-B','team/optimizations/o2/fullcore/build_fullcore.py','--output',str(base/'build-01')]
(base/'build-launch.json').write_text(json.dumps(dict(command=command,cwd=str(root),started=time.time(),environment=env),indent=2)+'\n')
with (base/'build-launch.log').open('wb') as log:
    rc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
(base/'build-launch.exit').write_text(str(rc)+'\n')
print('FULLCORE_BUILD_EXIT',rc,flush=True)
raise SystemExit(rc)
