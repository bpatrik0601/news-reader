import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def save_snapshot(snapshot: Dict[str, Any]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_id = snapshot.get("run_id", timestamp)

    out_dir = Path("data/snapshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{run_id}.json"

    out_file.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[Snapshot] Saved to {out_file}")