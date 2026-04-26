import os, time, subprocess, requests, base64
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO = "aria-agentworks/-agentworks-bridge"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
def get_task():
    url = f"https://api.github.com/repos/{REPO}/contents/task.txt"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return base64.b64decode(r.json()['content']).decode('utf-8'), r.json()['sha']
    return None, None
def post_result(output):
    url = f"https://api.github.com/repos/{REPO}/contents/result.txt"
    r = requests.get(url, headers=HEADERS)
    sha = r.json()['sha'] if r.status_code == 200 else None
    data = {"message": "Update result", "content": base64.b64encode(output.encode()).decode(), "sha": sha}
    requests.put(url, headers=HEADERS, json=data)
while True:
    task, sha = get_task()
    if task and task.strip():
        res = subprocess.run(task, shell=True, capture_output=True, text=True)
        post_result(res.stdout + res.stderr)
        requests.delete(f"https://api.github.com/repos/{REPO}/contents/task.txt", headers=HEADERS, json={"message": "Done", "sha": sha})
    time.sleep(30)