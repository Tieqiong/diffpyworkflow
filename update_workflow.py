import os
import yaml
import requests
from pathlib import Path

CENTRAL_REPO_OWNER = "Tieqiong"
CENTRAL_REPO_NAME = "diffpyworkflow"
CENTRAL_WORKFLOW_DIR = ".github/workflows/templates"
LOCAL_WORKFLOW_DIR = Path(".github/workflows")

user_input_cache = {}

def get_central_workflows():
    base_url = f"https://api.github.com/repos/{CENTRAL_REPO_OWNER}/{CENTRAL_REPO_NAME}/contents/{CENTRAL_WORKFLOW_DIR}"
    response = requests.get(base_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch central workflows: {response.status_code}")
    
    workflows = {}
    for file in response.json():
        if file['type'] == 'file' and file['name'].endswith('.yml'):
            content_response = requests.get(file['download_url'])
            if content_response.status_code == 200:
                workflows[file['name']] = content_response.text
    return workflows

def get_user_input(prompt, default, param_name):
    if param_name in user_input_cache:
        return user_input_cache[param_name]

    user_value = input(f"{prompt} (default: {default}): ").strip()
    if user_value:
        value = user_value
    else:
        value = default

    user_input_cache[param_name] = value
    return value

def update_workflow_params(workflow):
    if 'jobs' in workflow:
        for job_name, job_content in workflow['jobs'].items():
            if isinstance(job_content, dict) and 'with' in job_content:
                print(f"\nUpdating parameters for job '{job_name}':")
                for key, default_value in job_content['with'].items():
                    user_value = get_user_input(f"Enter value for '{key}'", default_value, key)
                    job_content['with'][key] = user_value
    return workflow

def update_local_workflows(central_workflows):
    local_workflows = set(f.name for f in LOCAL_WORKFLOW_DIR.glob("*.yml"))
    central_workflow_names = set(central_workflows.keys())

    for name, content in central_workflows.items():
        local_file = LOCAL_WORKFLOW_DIR / name
        central_yaml = yaml.safe_load(content)
        
        if local_file.exists():
            with open(local_file, 'r') as file:
                local_yaml = yaml.safe_load(file.read())
            
            if local_yaml.get(True) != central_yaml.get(True):
                local_yaml[True] = central_yaml[True]
                with open(local_file, 'w') as file:
                    yaml.dump(local_yaml, file, sort_keys=False)
                print(f"Updated triggers in {name}")
            else:
                print(f"No changes needed for {name}")

        else:
            central_yaml = update_workflow_params(central_yaml)
            with open(local_file, 'w') as file:
                yaml.dump(central_yaml, file, sort_keys=False)
            print(f"Added new workflow {name}")

    for name in local_workflows - central_workflow_names:
        (LOCAL_WORKFLOW_DIR / name).unlink()
        print(f"Removed workflow {name}")

def main():
    try:
        LOCAL_WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
        central_workflows = get_central_workflows()
        update_local_workflows(central_workflows)
        print("Workflow synchronization completed successfully")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
