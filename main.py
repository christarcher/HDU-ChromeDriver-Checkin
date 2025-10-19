from flask import Flask, request, Response, render_template_string # 不使用jsonify是因为utf-8支持有问题
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time
import json
import base64

app = Flask(__name__)

# 全局变量来存储子进程信息
processes = {}
usernames = ['1', '2', '3']

def run_script(username, index, attempts=0):
    while attempts < 2:
        try:
            process = subprocess.Popen(
                ['python', 'checkin.py', username, str(index)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 如果启动成功直接结束整个函数
            if "200 OK" in process.stdout.readline():
                processes[username] = process
                return "Process started successfully"

            # 未启动成功的情况重新执行
            if (process.returncode == 1 or process.poll() is not None):
                raise Exception(f"子进程启动失败: {process.stderr.readline()}")

        except Exception as e:
            attempts += 1
            time.sleep(2)
            continue
    return str(e)

@app.route("/hducheckin/preload", methods=['GET'])
def preload():
    with ThreadPoolExecutor(max_workers=len(usernames)) as executor:
        results = list(executor.map(run_script, [username for username in usernames if username not in processes], range(len([username for username in usernames if username not in processes]))))
    failed_loads = [username for username, result in zip(usernames, results) if "Process started successfully" not in result]
    response_data = {"error": []}
    for username in failed_loads:
        response_data["error"].append(f"failed to load {username}'s process")
    
    return Response(json.dumps(response_data, ensure_ascii=False), mimetype='application/json; charset=utf-8')

@app.route("/hducheckin/checkin", methods=['GET'])
def checkin():
    code = request.args.get('code')
    response_data = {"error": []}
    for username in usernames:
        process = processes.get(username)
        if process and process.poll() is None:
            process.stdin.write(code + '\n')
            process.stdin.flush()
        else:
            response_data["error"].append(f"{username} not loaded")

    return Response(json.dumps(response_data, ensure_ascii=False), mimetype='application/json; charset=utf-8')

@app.route("/hducheckin/getlog", methods=['GET'])
def log():
    response_data = {}
    for username in usernames:
        try:
            with open(f"./log/{username}.log", 'r', encoding='UTF-8')as file:
                response_data[username] = file.read()
        except FileNotFoundError:
            response_data[username] = '日志文件未找到'
    return Response(json.dumps(response_data, ensure_ascii=False), mimetype='application/json; charset=utf-8')

@app.route('/hducheckin/getresults')
def show_all_pictures():
    image_html = []
    for username in usernames:
        with open(f"./results/{username}.png", 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        img_tag = f'<img src="data:image/png;base64,{encoded_string}">'
        image_html.append(img_tag)

    return f"<div>{''.join(image_html)}</div>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5000')
