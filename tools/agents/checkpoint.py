#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
HEADING="## Context checkpoint"; LIST_KEYS={"context_routes","owned_paths","proven","derived","unknown","conflicts","rejected_hypotheses","changed_paths","blockers"}; PLACEHOLDERS={"","none","unknown","pending","n/a","tbd","todo","later"}
def root(): return Path(__file__).resolve().parents[2]
def contract(): return json.loads((root()/"docs/agents/GOVERNANCE_CONTRACT.json").read_text(encoding="utf-8"))["shared_checkpoint_contract"]
def scalar(v):
 v=v.strip(); return v[1:-1] if len(v)>=2 and v[0]==v[-1] and v[0] in {'\"',"'"} else v
def parse(path):
 text=path.read_text(encoding="utf-8"); matches=list(re.finditer(r"(?m)^## Context checkpoint\s*$",text))
 if not matches:return None
 if len(matches)!=1:raise ValueError(f"{path}: expected exactly one {HEADING}")
 rest=text[matches[0].end():]; nxt=re.search(r"(?m)^##\s+",rest); section=rest[:nxt.start()] if nxt else rest; fence=re.search(r"```(?:yaml|yml)\s*\n",section,re.I)
 if not fence:raise ValueError(f"{path}: checkpoint has no fenced YAML block")
 end=section.find("```",fence.end())
 if end<0:raise ValueError(f"{path}: checkpoint fence is not closed")
 data={}; current=None; current_validation=None
 for lineno,raw in enumerate(section[fence.end():end].splitlines(),1):
  if not raw.strip() or raw.lstrip().startswith("#"):continue
  indent=len(raw)-len(raw.lstrip(" ")); line=raw.strip()
  if indent==0:
   if ":" not in line:raise ValueError(f"{path}:{lineno}: invalid checkpoint line")
   key,value=line.split(":",1); key=key.strip(); value=value.strip()
   if key in data:raise ValueError(f"{path}:{lineno}: duplicate key {key}")
   current=key; current_validation=None
   if key in LIST_KEYS or key=="validation":
    if value not in {"","[]"}:raise ValueError(f"{path}:{lineno}: {key} must be a list")
    data[key]=[]
   elif key=="first_failure":
    if value:raise ValueError(f"{path}:{lineno}: first_failure must be a mapping")
    data[key]={}
   else:data[key]=scalar(value)
   continue
  if current in LIST_KEYS:
   if indent!=2 or not line.startswith("- "):raise ValueError(f"{path}:{lineno}: invalid list item")
   data[current].append(scalar(line[2:]))
  elif current=="first_failure":
   if indent!=2 or ":" not in line:raise ValueError(f"{path}:{lineno}: invalid first_failure")
   key,value=line.split(":",1); data[current][key.strip()]=scalar(value)
  elif current=="validation":
   if indent==2 and line.startswith("- "):
    key,value=line[2:].split(":",1); current_validation={key.strip():scalar(value)}; data[current].append(current_validation)
   elif indent==4 and current_validation is not None and ":" in line:
    key,value=line.split(":",1); current_validation[key.strip()]=scalar(value)
   else:raise ValueError(f"{path}:{lineno}: invalid validation item")
  else:raise ValueError(f"{path}:{lineno}: scalar cannot have nested values")
 return data
def validate(data,path):
 cfg=contract(); errors=[]
 for key in cfg["required_fields"]:
  if key not in data:errors.append(f"{path}: missing checkpoint field {key}")
 if str(data.get("checkpoint_version",""))!=str(cfg["version"]):errors.append(f"{path}: wrong checkpoint_version")
 if str(data.get("status","")) not in cfg["allowed_statuses"]:errors.append(f"{path}: unsupported status")
 if str(data.get("next_action","")).strip().casefold() in PLACEHOLDERS:errors.append(f"{path}: next_action must be concrete")
 failure=data.get("first_failure")
 if not isinstance(failure,dict) or not all(str(failure.get(k,"")).strip() for k in ("marker","evidence")):errors.append(f"{path}: invalid first_failure")
 validation=data.get("validation")
 if not isinstance(validation,list):errors.append(f"{path}: validation must be a list")
 else:
  for i,item in enumerate(validation,1):
   if not isinstance(item,dict) or not all(str(item.get(k,"")).strip() for k in ("command","result","evidence")):errors.append(f"{path}: invalid validation item {i}")
   elif item["result"] not in cfg["allowed_validation_results"]:errors.append(f"{path}: unsupported validation result")
 for key,limit in cfg.get("compactness_limits",{}).items():
  value=data.get(key,[])
  if not isinstance(value,list):errors.append(f"{path}: {key} must be a list")
  elif len(value)>limit:errors.append(f"{path}: {key} has {len(value)} items; compactness limit is {limit}")
 fields=list(cfg["evidence_state_fields"].values()); normalized={k:{" ".join(str(x).casefold().split()) for x in data.get(k,[]) if str(x).strip()} for k in fields}
 for i,left in enumerate(fields):
  for right in fields[i+1:]:
   for fact in normalized[left]&normalized[right]:errors.append(f"{path}: evidence fact appears in both {left} and {right}: {fact}")
 return errors
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("task",nargs="?",type=Path); ap.add_argument("--tasks",type=Path); ap.add_argument("--require-checkpoint",action="store_true"); args=ap.parse_args()
 if bool(args.task)==bool(args.tasks):ap.error("provide exactly one task or --tasks directory")
 paths=[args.task] if args.task else sorted(args.tasks.glob("*.md")); errors=[]
 for path in paths:
  try:data=parse(path)
  except (OSError,ValueError) as exc:errors.append(str(exc));continue
  if data is None:
   if args.require_checkpoint:errors.append(f"{path}: missing {HEADING}")
  else:errors.extend(validate(data,path))
 for error in errors:print(f"ERROR: {error}",file=sys.stderr)
 if errors:return 1
 print(f"Validated {len(paths)} checkpoint task(s).");return 0
if __name__=="__main__":raise SystemExit(main())
