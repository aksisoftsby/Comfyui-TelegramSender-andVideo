import subprocess

# Start watcher
watcher = subprocess.Popen(["python", "watcher-modal.py"])
watcher2 = subprocess.Popen(["python", "watcher-collab.py"])

# Start ComfyUI
comfy = subprocess.Popen(["python", "main.py", "--dont-print-server"])

watcher.wait()
watcher2.wait()

comfy.wait()
