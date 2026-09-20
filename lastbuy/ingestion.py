"""Review normalized, hashed source snapshots before changing decision state."""

from .domain import Snapshot, digest


def compare_snapshots(before: Snapshot | None, after: Snapshot):
    previous = {s.id: s for s in before.sources} if before else {}
    current = {s.id: s for s in after.sources}
    changes = []
    for key in sorted(previous.keys() | current.keys()):
        old, new = previous.get(key), current.get(key)
        if old is None:
            kind = "added"
        elif new is None:
            kind = "removed"
        elif digest(old) != digest(new):
            kind = "changed"
        else:
            continue
        changes.append(
            {
                "source_id": key,
                "change": kind,
                "previous_revision": old.revision if old else None,
                "new_revision": new.revision if new else None,
            }
        )
    structured = [
        key
        for key in (
            "cohorts",
            "scenarios",
            "lots",
            "quote",
            "complete",
            "baseline_quantity",
        )
        if not before or digest(getattr(before, key)) != digest(getattr(after, key))
    ]
    return {
        "snapshot_sha256": digest(after),
        "source_changes": changes,
        "structured_changes": structured,
        "source_count": len(after.sources),
        "lot_count": len(after.lots),
        "scenario_count": len(after.scenarios),
        "requires_reanalysis": before is not None and digest(before) != digest(after),
    }
