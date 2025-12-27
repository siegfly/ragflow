import os
import sys
import subprocess
import time
import re
from pathlib import Path

# 设置 stdout 自动刷新，防止输出缓冲
sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    print(f"[Launcher] {msg}", flush=True)

def load_env(env_path):
    """加载 .env 文件环境变量"""
    if not env_path.exists():
        log(f"Warning: {env_path} not found.")
        return
    
    log(f"Loading env from {env_path}")
    count = 0
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('\'"')
                
                # Handle ${VAR:-default} substitution
                match = re.match(r'\$\{([^:]+):-(.+)\}', value)
                if match:
                    var_name, default_val = match.groups()
                    value = os.environ.get(var_name, default_val)
                
                if key not in os.environ:
                    os.environ[key] = value
                    count += 1
    log(f"Loaded {count} environment variables.")

def main():
    log("Script starting...")
    root_dir = Path(__file__).parent.absolute()
    log(f"Root directory: {root_dir}")
    
    env_file = root_dir / 'docker' / '.env'
    
    # 1. 加载环境变量
    load_env(env_file)
    
    # 2. 设置必要的环境变量
    os.environ['PYTHONPATH'] = str(root_dir)
    os.environ['NLTK_DATA'] = str(root_dir / 'nltk_data')
    log(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")
    
    # 3. 启动进程
    python_exe = sys.executable
    log(f"Using Python executable: {python_exe}")
    
    processes = []
    
    try:
        # 启动 Task Executor
        log("Starting Task Executor...")
        task_script = root_dir / 'rag' / 'svr' / 'task_executor.py'
        if not task_script.exists():
             log(f"Error: {task_script} does not exist!")
             return

        task_cmd = [python_exe, str(task_script), '1']
        # 使用 shell=False 并继承 stdout/stderr 以便在控制台看到输出
        p_task = subprocess.Popen(task_cmd, cwd=root_dir, stdout=sys.stdout, stderr=sys.stderr)
        processes.append(p_task)
        log(f"Task Executor started with PID {p_task.pid}")
        
        time.sleep(2)
        
        # 启动 API Server
        log("Starting RAGFlow Server...")
        server_script = root_dir / 'api' / 'ragflow_server.py'
        if not server_script.exists():
             log(f"Error: {server_script} does not exist!")
             return

        server_cmd = [python_exe, str(server_script)]
        p_server = subprocess.Popen(server_cmd, cwd=root_dir, stdout=sys.stdout, stderr=sys.stderr)
        processes.append(p_server)
        log(f"RAGFlow Server started with PID {p_server.pid}")
        
        log("\nAll services started. Press Ctrl+C to stop.\n")
        
        # 监控进程
        while True:
            time.sleep(1)
            if p_task.poll() is not None:
                log(f"Task Executor exited unexpectedly with code {p_task.returncode}.")
                break
            if p_server.poll() is not None:
                log(f"Server exited unexpectedly with code {p_server.returncode}.")
                break
                
    except KeyboardInterrupt:
        log("\nStopping services...")
    except Exception as e:
        log(f"An error occurred: {e}")
    finally:
        for p in processes:
            if p.poll() is None:
                log(f"Terminating process {p.pid}...")
                p.terminate()

if __name__ == "__main__":
    main()
