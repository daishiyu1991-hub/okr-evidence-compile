#!/usr/bin/env python3
import json
import sys


def has_text(value):
    return isinstance(value, str) and value.strip() != ""


def main() -> int:
    payload = json.load(sys.stdin)
    krs = payload.get("krs", [])
    projects = payload.get("projects", [])
    tasks = payload.get("tasks", [])

    project_by_kr = {}
    for project in projects:
        for kr in project.get("linked_krs", []):
            project_by_kr.setdefault(kr, []).append(project)

    tasks_by_project = {}
    for task in tasks:
        for project in task.get("linked_projects", []):
            tasks_by_project.setdefault(project, []).append(task)

    inconsistencies = []

    for kr in krs:
        kr_id = kr.get("record_id")
        linked_projects = project_by_kr.get(kr_id, [])
        if kr.get("status") == "1-进行中" and not linked_projects:
            inconsistencies.append({
                "type": "kr_without_project_movement",
                "severity": "medium",
                "message": f"KR {kr.get('title', kr_id)} 正在进行中，但没有关联项目快照。"
            })

    for project in projects:
        project_id = project.get("record_id")
        if project.get("progress") == "1-进行中" and not has_text(project.get("weekly_update", "")):
            inconsistencies.append({
                "type": "project_missing_weekly_update",
                "severity": "medium",
                "message": f"项目 {project.get('title', project_id)} 已进行中，但缺少本周更新。"
            })
        overdue_tasks = [
            task for task in tasks_by_project.get(project_id, [])
            if task.get("task_progress") in {"0-未开始", "1-进行中", "3-阶段性暂停", "4-未完成"}
            and task.get("is_overdue")
        ]
        if overdue_tasks and not has_text(project.get("blocker", "")):
            inconsistencies.append({
                "type": "overdue_task_without_blocker",
                "severity": "high",
                "message": f"项目 {project.get('title', project_id)} 存在逾期任务，但阻塞字段为空。"
            })

    json.dump({"inconsistencies": inconsistencies}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

