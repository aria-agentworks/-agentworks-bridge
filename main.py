import os, time, subprocess, requests, base64, sys

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO = "aria-agentworks/-agentworks-bridge"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

print(f"Bridge starting... Monitoring repo: {REPO}")
if not GITHUB_TOKEN:
    print("CRITICAL ERROR: GITHUB_TOKEN not found in environment variables.")

def get_task():
    url = f"https://api.github.com/repos/{REPO}/contents/task.txt"
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return base64.b64decode(r.json()['content']).decode('utf-8'), r.json()['sha']
        elif r.status_code != 404:
            print(f"Error checking task: {r.status_code} - {r.text}")
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

# Check if --once flag is present
if '--once' in sys.argv:
    print("Single-task mode enabled (--once flag)")
    print("Polling for tasks...")
    task, sha = get_task()
    if task and task.strip():
        print(f"Executing task: {task}")
        res = subprocess.run(task, shell=True, capture_output=True, text=True)
        post_result(res.stdout + res.stderr)
        print("Cleaning up task...")
        requests.delete(f"https://api.github.com/repos/{REPO}/contents/task.txt", headers=HEADERS, json={"message": "Done", "sha": sha})
else:
    print("Infinite loop mode enabled (default)")
    while True:
        print("Polling for tasks...")
        task, sha = get_task()
        if task and task.strip():
            print(f"Executing task: {task}")
            res = subprocess.run(task, shell=True, capture_output=True, text=True)
            post_result(res.stdout + res.stderr)
            print("Cleaning up task...")
            requests.delete(f"https://api.github.com/repos/{REPO}/contents/task.txt", headers=HEADERS, json={"message": "Done", "sha": sha})
        time.sleep(30)
