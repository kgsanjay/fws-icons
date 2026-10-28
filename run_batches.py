"""Supervise finite Codex CLI calls, restarting only when progress was made."""
import argparse,shutil,subprocess,sys
from pathlib import Path
import queue as q
p=argparse.ArgumentParser();p.add_argument('--all',action='store_true',help='Process all eligible batches; consumes Codex/image usage');a=p.parse_args()
if not shutil.which('codex'):sys.exit('Codex CLI is not installed or not on PATH. Open this folder in Codex and paste START-CODEX.txt instead.')
q.init()
while True:
 rows=q.export();pending=[r for r in rows if r['status']!='complete' and r['attempts']<3]
 if not pending:print('No eligible pending icons. Check status for failed items.');break
 b=min(r['batch'] for r in pending);before=[(r['id'],r['status'],r['attempts']) for r in rows]
 prompt=f'Read AGENTS.md and README.md. Process only batch {b} using queue.py and built-in image generation. Save progress after every icon and bundle if complete. If capability/quota/auth blocks you, stop and explain. Do not use paid API fallback.'
 try:r=subprocess.run(['codex','exec','--skip-git-repo-check','--sandbox','workspace-write',prompt],cwd=q.ROOT)
 except KeyboardInterrupt:sys.exit('Stopped; saved queue is ready to resume.')
 after=[(r['id'],r['status'],r['attempts']) for r in q.export()]
 if r.returncode or before==after:sys.exit('Stopped: Codex failed or made no queue progress. Inspect the last response before restarting.')
 if not a.all:break
