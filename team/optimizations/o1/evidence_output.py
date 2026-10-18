"""Write a new audit result without replacing evidence or following aliases."""
import json
from pathlib import Path


def require_new_output(path):
    path = Path(path)
    # exists() alone misses dangling symlinks. Existing hard links, directories
    # and input aliases are rejected regardless of the caller's spelling.
    if path.exists() or path.is_symlink():
        raise FileExistsError('Use a new evidence output: '+str(path))


def write_new_json(path, result):
    text = json.dumps(result, indent=2, sort_keys=True)+'\n'
    # Exclusive creation also closes the race after the early preflight check.
    with Path(path).open('x', encoding='utf-8') as output:
        output.write(text)
