#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone


USER_FIELDS = {"执行人", "负责人", "干系人"}
LINK_FIELDS = {"关联KR", "所属项目", "关联团队项目", "关联个人OKR"}


def is_valid_user_value(value) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, dict) and str(item.get("id", "")).startswith("ou_") for item in value)


def is_valid_link_value(value) -> bool:
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, dict) and str(item.get("id", "")).startswith("rec") for item in value)


def main() -> int:
    payload = json.load(sys.stdin)
    source_packet = payload.get("source_packet", {})
    target_resolutions = payload.get("target_resolutions", [])
    proposed_changes = payload.get("proposed_changes", [])

    confidences = [item.get("confidence", "low") for item in proposed_changes + target_resolutions]
    validation_notes = []
    has_unresolved_user_field = False
    has_unresolved_link_field = False
    for item in proposed_changes:
        field = item.get("field", "")
        if field in USER_FIELDS and not is_valid_user_value(item.get("after")):
            has_unresolved_user_field = True
            validation_notes.append(
                f"{field} must be resolved to Feishu open_id and written as user cells before write."
            )
        if field in LINK_FIELDS and not is_valid_link_value(item.get("after")):
            has_unresolved_link_field = True
            validation_notes.append(
                f"{field} must be resolved to Base record_id and written as link cells before write."
            )

    has_new_or_unresolved_target = any(
        not item.get("record_id")
        or str(item.get("record_id")).startswith("__new")
        or item.get("operation") in {"create", "create_candidate"}
        for item in target_resolutions
    )
    if has_new_or_unresolved_target or has_unresolved_user_field or has_unresolved_link_field:
        write_mode = "preview_only"
    elif "high" in confidences and all(c in {"high", "medium"} for c in confidences):
        write_mode = "write_formal"
    elif "medium" in confidences:
        write_mode = "write_helper_only"
    else:
        write_mode = "preview_only"

    preview = {
        "source_packet": source_packet,
        "target_resolutions": target_resolutions,
        "proposed_changes": proposed_changes,
        "audit_payload": {
            "最近更新原因": payload.get("reason", ""),
            "最近更新来源": source_packet.get("source_url", ""),
            "最近更新时间": datetime.now(timezone.utc).isoformat(),
            "AI编译摘要": payload.get("summary", ""),
            "待人工确认": write_mode != "write_formal",
        },
        "validation_notes": validation_notes,
        "write_mode": write_mode,
    }
    json.dump(preview, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
