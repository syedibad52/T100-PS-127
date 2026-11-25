"""Human-readable terminal reports. JSON audits remain the authoritative record."""
from __future__ import annotations

from collections import Counter
from typing import Any


def _value(value: Any) -> str:
    if value is None: return "-"
    if isinstance(value, float): return f"{value:.2f}"
    return str(value)


def match_summary(audit: dict, audit_path: str = "") -> str:
    donor = audit["donor"]
    decisions = audit["decisions"]
    eligible = [item for item in decisions if item["eligible"]]
    excluded = [item for item in decisions if not item["eligible"]]
    lines = [
        "\n=== ORGAN ALLOCATION MATCH RUN ===",
        f"Run ID:       {audit['run_id']}",
        f"Run time:     {audit['run_at']}",
        f"Donor offer:  {donor['offer_id']} | {donor['organ']} | Blood group {donor['blood_group']}",
        f"Donor site:   {donor['hospital']} | Cross-clamp: {donor['cross_clamp_at']}",
        "",
        "RESULT",
        f"  Primary candidate:  {audit['primary'] or 'No eligible candidate'}",
        f"  Backup candidate 1: {audit['backups'][0] if len(audit['backups']) > 0 else '-'}",
        f"  Backup candidate 2: {audit['backups'][1] if len(audit['backups']) > 1 else '-'}",
        f"  Eligibility:        {len(eligible)} eligible | {len(excluded)} excluded",
    ]
    if eligible:
        lines.extend(["", "TOP CANDIDATES", "  Rank  Candidate     Tier  Urgency          Score   Wait days  HLA mismatch"])
        for item in sorted(eligible, key=lambda row: row["rank"])[:5]:
            lines.append(f"  {item['rank']:>4}  {item['candidate_id']:<12} {item['tier']:>4}  {item['score'].get('urgency', '-'): <16} {_value(item['score'].get('total')):>7}  {_value(item['waiting_days']):>9}  {item['mismatches']:>12}")
        primary = next((item for item in eligible if item["candidate_id"] == audit["primary"]), None)
        if primary:
            components = ", ".join(f"{key.replace('_', ' ')}={_value(value)}" for key, value in primary["score"].items())
            lines.extend(["", f"WHY THE PRIMARY CANDIDATE RANKED FIRST", f"  {primary['candidate_id']} is eligible in geographic Tier {primary['tier']}. Score details: {components}."])
    if excluded:
        reasons = Counter(item["exclusions"][0] if item["exclusions"] else "unspecified" for item in excluded)
        lines.extend(["", "TOP EXCLUSION REASONS"])
        lines.extend(f"  - {reason}: {count} candidate(s)" for reason, count in reasons.most_common(4))
    if audit_path:
        lines.extend(["", f"Full audit saved to: {audit_path}", "Tip: use `python main.py report --run-id " + audit["run_id"] + " --json` for the complete machine-readable audit."])
    return "\n".join(lines)


def allocation_summary(audit: dict) -> str:
    lines = ["\n=== OFFER OUTCOME ===", f"Run ID: {audit['run_id']}"]
    if audit["allocations"]:
        for item in audit["allocations"]:
            lines.append(f"Allocated: {item['organ']} -> {item['candidate_id']} at {item['at']}")
    else:
        lines.append("No allocation has been completed yet. Process an acceptance event or review the offer history.")
    return "\n".join(lines)
