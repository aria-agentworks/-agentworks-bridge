import os, sys, time, subprocess, requests, base64

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO = "aria-agentworks/-agentworks-bridge"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def get_task():
    url = f"https://api.github.com/repos/{REPO}/contents/task.txt"
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return base64.b64decode(r.json()['content']).decode('utf-8'), r.json()['sha']
        elif r.status_code == 404:
            return None, None  # task.txt doesn't exist
        else:
            print(f"Error checking task: {r.status_code}")
            return None, None
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None

def post_result(output):
    print("Posting results to result.txt...")
    url = f"https://api.github.com/repos/{REPO}/contents/result.txt"
    r = requests.get(url, headers=HEADERS)
    sha = r.json()['sha'] if r.status_code == 200 else None
    data = {"message": "Update result", "content": base64.b64encode(output.encode()).decode(), "sha": sha}
    requests.put(url, headers=HEADERS, json=data)

def execute_task(task):
    """Execute a task, handling both Python scripts with shebang and shell scripts."""
    task_stripped = task.strip()
    if task_stripped.startswith('#!/usr/bin/env python3'):
        lines = task_stripped.split('\n', 1)
        python_code = lines[1].strip() if len(lines) > 1 else ''
        print("Detected Python script with shebang")
        res = subprocess.run(['python3', '-c', python_code], capture_output=True, text=True)
        return res.stdout + res.stderr
    else:
        print("Detected shell script")
        res = subprocess.run(task, shell=True, capture_output=True, text=True)
        return res.stdout + res.stderr

# Single-pass execution - exits after one check
print("Bridge running in single-pass mode")
task, sha = get_task()
if task and task.strip():
    print(f"Executing task: {task[:100]}...")
    result = execute_task(task)
    post_result(result)
    if sha:
        requests.delete(f"https://api.github.com/repos/{REPO}/contents/task.txt", headers=HEADERS, json={"message": "Done", "sha": sha})
    print("Task completed. Exiting.")
    sys.exit(0)
else:
    print("No task.txt file found. Exiting bridge.")
    sys.exit(0)