#!/usr/bin/env python3
"""
Job Hunter Todoist 集成管理器
基于 LifeOS TodoistManager，共享 LifeOS 配置文件
"""

import json
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, TypedDict
import getpass

# Fix Windows console encoding for CJK characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from todoist_api_python.api import TodoistAPI
    from todoist_api_python.models import Task, Project, Label
except ImportError:
    print("todoist-api-python not installed")
    print("Run: pip install todoist-api-python")
    sys.exit(1)


# Config lookup order:
#   1. LifeOS shared config (avoids maintaining two copies)
#   2. Local config/todoist_config.json (fallback)
LIFEOS_CONFIG = Path.home() / "github" / "LifeOS" / "config" / "todoist_config.json"
PROJECT_ROOT = Path(__file__).parent.parent
LOCAL_CONFIG = PROJECT_ROOT / "config" / "todoist_config.json"


class BatchResult(TypedDict):
    success: int
    failed: int
    tasks: List[Task]


class TodoistManager:
    def __init__(self, config_path=None):
        if config_path is None:
            if LIFEOS_CONFIG.exists():
                self.config_path = LIFEOS_CONFIG
            else:
                self.config_path = LOCAL_CONFIG
        else:
            self.config_path = Path(config_path).expanduser()

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()

        if self.config.get("api_token"):
            try:
                self.api = TodoistAPI(self.config["api_token"])
            except Exception as e:
                print(f"API init failed: {e}")
                self.api = None
        else:
            self.api = None

    def _flatten_paginator(self, paginator):
        results = []
        for page in paginator:
            results.extend(page)
        return results

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Config not found: {self.config_path}")
            return {}

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def setup_todoist(self):
        """Interactive API token setup (saves to local config)."""
        print("Todoist API Setup")
        print("")
        print("Steps to get your API Token:")
        print("1. Go to https://todoist.com/")
        print("2. Settings > Integrations > Developer")
        print("3. Copy 'API Token'")
        print("")

        api_token = getpass.getpass("Enter your Todoist API Token: ").strip()

        if not api_token:
            print("Token cannot be empty")
            return False

        try:
            test_api = TodoistAPI(api_token)
            projects = []
            for page in test_api.get_projects():
                projects.extend(page)

            print(f"Connected! Found {len(projects)} projects")

            # Save to LOCAL config (not LifeOS)
            self.config_path = LOCAL_CONFIG
            self.config["api_token"] = api_token
            self.config["setup_date"] = datetime.now().isoformat()
            self.save_config()
            self.api = test_api

            print(f"Config saved to: {self.config_path}")

            create_projects = input("Initialize default projects and labels? (y/n): ").strip().lower()
            if create_projects in ['y', 'yes']:
                self.initialize_projects()

            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def initialize_projects(self):
        if not self.api:
            print("API not initialized, run setup first")
            return False

        print("Creating default projects...")

        created_count = 0
        for key, project_config in self.config.get("projects", {}).items():
            try:
                existing_projects = self._flatten_paginator(self.api.get_projects())
                existing_project = next(
                    (p for p in existing_projects if p.name == project_config["name"]),
                    None
                )

                if existing_project:
                    print(f"  Project exists: {project_config['name']}")
                    project_config["project_id"] = existing_project.id
                else:
                    project = self.api.add_project(
                        name=project_config["name"],
                        color=project_config.get("color", "grey"),
                        is_favorite=project_config.get("is_favorite", False)
                    )
                    project_config["project_id"] = project.id
                    print(f"  Created project: {project_config['name']}")
                    created_count += 1

            except Exception as e:
                print(f"  Failed to create project {project_config['name']}: {e}")

        print("\nCreating default labels...")
        for key, label_config in self.config.get("labels", {}).items():
            try:
                existing_labels = self._flatten_paginator(self.api.get_labels())
                existing_label = next(
                    (l for l in existing_labels if l.name == label_config["name"]),
                    None
                )

                if existing_label:
                    print(f"  Label exists: {label_config['name']}")
                    label_config["label_id"] = existing_label.id
                else:
                    label = self.api.add_label(
                        name=label_config["name"],
                        color=label_config.get("color", "grey")
                    )
                    label_config["label_id"] = label.id
                    print(f"  Created label: {label_config['name']}")

            except Exception as e:
                print(f"  Failed to create label {label_config['name']}: {e}")

        self.save_config()
        print(f"\nDone! Created {created_count} new projects")
        return True

    def create_task(
        self,
        content: str,
        project: str = None,
        priority: str = "medium",
        due_days: int = 0,
        labels: List[str] = None,
        description: str = "",
        parent_id: str = None
    ) -> Optional[Task]:
        if not self.api:
            print("API not initialized, run setup first")
            return None

        try:
            priority_map = self.config.get("default_settings", {}).get(
                "priority_mapping", {"high": 4, "medium": 2, "low": 1}
            )
            priority_value = priority_map.get(priority, 2)

            project_id = None
            if project:
                project_config = self.config.get("projects", {}).get(project)
                if project_config:
                    project_id = project_config.get("project_id")

            due_string = None
            if due_days == 0:
                due_string = "today"
            elif due_days == 1:
                due_string = "tomorrow"
            elif due_days > 1:
                due_date = datetime.now() + timedelta(days=due_days)
                due_string = due_date.strftime("%Y-%m-%d")

            label_names = []
            if labels:
                for label_key in labels:
                    label_config = self.config.get("labels", {}).get(label_key)
                    if label_config:
                        label_names.append(label_config["name"])

            task_params = {
                "content": content,
                "description": description,
                "project_id": project_id,
                "due_string": due_string,
                "priority": priority_value,
                "labels": label_names
            }

            if parent_id:
                task_params["parent_id"] = parent_id

            task = self.api.add_task(**task_params)
            return task

        except Exception as e:
            print(f"Failed to create task: {e}")
            return None

    def create_tasks_batch(self, tasks: List[Dict]) -> BatchResult:
        if not self.api:
            print("API not initialized")
            return {"success": 0, "failed": 0, "tasks": []}

        results = {"success": 0, "failed": 0, "tasks": []}

        print(f"Creating {len(tasks)} tasks...")

        for i, task_data in enumerate(tasks, 1):
            task_name = task_data.get('name', task_data.get('content', f'Task {i}'))
            print(f"  {i}/{len(tasks)}: {task_name[:40]}...")

            task = self.create_task(
                content=task_name,
                project=task_data.get('project', 'other'),
                priority=task_data.get('priority', 'medium'),
                due_days=task_data.get('due_days', 1),
                labels=task_data.get('labels', []),
                description=task_data.get('body', task_data.get('note', ''))
            )

            if task:
                results["success"] += 1
                results["tasks"].append(task)
            else:
                results["failed"] += 1

        print(f"\nCreated {results['success']}/{len(tasks)} tasks")
        if results["failed"] > 0:
            print(f"Failed: {results['failed']}")

        return results

    def get_all_tasks(self, project: str = None, label: str = None) -> List[Task]:
        if not self.api:
            print("API not initialized")
            return []

        try:
            filters = {}

            if project:
                project_config = self.config.get("projects", {}).get(project)
                if project_config and project_config.get("project_id"):
                    filters["project_id"] = project_config["project_id"]

            if label:
                label_config = self.config.get("labels", {}).get(label)
                if label_config:
                    filters["label"] = label_config["name"]

            tasks_paginator = self.api.get_tasks(**filters)
            tasks = self._flatten_paginator(tasks_paginator)
            return tasks

        except Exception as e:
            print(f"Failed to get tasks: {e}")
            return []

    def export_tasks_to_json(self, output_file: str = None):
        if not output_file:
            data_dir = PROJECT_ROOT / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            output_file = data_dir / f"todoist_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_file = Path(output_file)

        output_path = Path(output_file).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print("Exporting Todoist tasks...")

        tasks = self.get_all_tasks()

        if not tasks:
            print("No tasks found")
            return None

        tasks_data = []
        for task in tasks:
            due_date = None
            if task.due:
                if hasattr(task.due, 'date'):
                    due_date = str(task.due.date) if task.due.date else None
                else:
                    due_date = str(task.due)

            tasks_data.append({
                "id": task.id,
                "content": task.content,
                "description": task.description,
                "project_id": task.project_id,
                "priority": task.priority,
                "due": due_date,
                "labels": task.labels,
                "created_at": task.created_at.isoformat() if hasattr(task.created_at, 'isoformat') else str(task.created_at),
                "is_completed": task.is_completed
            })

        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_tasks": len(tasks_data),
            "tasks": tasks_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(tasks_data)} tasks to: {output_path}")
        return str(output_path)

    def test_connection(self):
        if not self.api:
            print("API not initialized, run setup first")
            return False

        try:
            print("Testing Todoist connection...")
            print(f"Config: {self.config_path}")
            projects = self._flatten_paginator(self.api.get_projects())
            labels = self._flatten_paginator(self.api.get_labels())
            tasks = self._flatten_paginator(self.api.get_tasks())

            print(f"Connected!")
            print(f"  Projects: {len(projects)}")
            print(f"  Labels:   {len(labels)}")
            print(f"  Tasks:    {len(tasks)}")

            return True

        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Job Hunter Todoist Manager')
    parser.add_argument('action', nargs='?',
                       choices=['setup', 'test', 'add', 'init-projects', 'export', 'list'],
                       default='help',
                       help='Action to perform')
    parser.add_argument('task_content', nargs='?', default=None,
                       help='Task content (for "add" action)')
    parser.add_argument('--project', help='Project name')
    parser.add_argument('--priority', default='medium',
                       choices=['high', 'medium', 'low'],
                       help='Task priority (default: medium)')
    parser.add_argument('--due', type=int, default=0,
                       help='Due in N days (default: 0 = today)')
    parser.add_argument('--label', help='Label filter (for list) or label to add (for add)')
    parser.add_argument('--output', help='Export file path')

    args = parser.parse_args()

    manager = TodoistManager()

    if args.action == 'setup':
        manager.setup_todoist()

    elif args.action == 'test':
        manager.test_connection()

    elif args.action == 'add':
        if not args.task_content:
            print("Usage: python todoist_manager.py add \"task content\"")
            sys.exit(1)
        labels = [args.label] if args.label else []
        task = manager.create_task(
            content=args.task_content,
            project=args.project,
            priority=args.priority,
            due_days=args.due,
            labels=labels
        )
        if task:
            print(f"Created: {task.content}")
            if task.due:
                print(f"  Due: {task.due.date if hasattr(task.due, 'date') else task.due}")

    elif args.action == 'init-projects':
        manager.initialize_projects()

    elif args.action == 'export':
        manager.export_tasks_to_json(args.output)

    elif args.action == 'list':
        tasks = manager.get_all_tasks(project=args.project, label=args.label)
        print(f"\n{len(tasks)} tasks:")
        for i, task in enumerate(tasks, 1):
            status = "x" if task.is_completed else "o"
            priority_icons = ["", "!", "!!", "!!!"]
            priority_icon = priority_icons[task.priority - 1] if task.priority > 0 else ""
            due_str = ""
            if task.due:
                due_str = f" [{task.due.date if hasattr(task.due, 'date') else task.due}]"
            print(f"  [{status}] {i}. {priority_icon} {task.content}{due_str}")

    else:
        print("Job Hunter Todoist Manager")
        print(f"Config: {LIFEOS_CONFIG if LIFEOS_CONFIG.exists() else LOCAL_CONFIG}")
        print("")
        print("Usage:")
        print("  python todoist_manager.py setup                    # Setup API token")
        print("  python todoist_manager.py test                     # Test connection")
        print("  python todoist_manager.py init-projects            # Initialize projects & labels")
        print('  python todoist_manager.py add "task content"       # Create a task')
        print('  python todoist_manager.py add "task" --project career --priority high')
        print("  python todoist_manager.py list                     # List all tasks")
        print("  python todoist_manager.py list --project career    # Filter by project")
        print("  python todoist_manager.py export                   # Export tasks to JSON")


if __name__ == "__main__":
    main()
