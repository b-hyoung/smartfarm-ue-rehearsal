"""UE 에디터에 Python 을 원격 실행시키는 헬퍼.

UE 가 정식 제공하는 Python Remote Execution 프로토콜(UDP 멀티캐스트 + TCP)을 씁니다.
Remote Control(30010) 은 프로젝트 설정에서 객체 접근이 막혀 있어 이쪽을 사용합니다.

전제 (Project Settings > Plugins > Python):
    Enable Remote Execution = True
    Multicast Bind Address  = 127.0.0.1
  → ue/Config/DefaultEngine.ini 에 기록해 둠.

사용:
    py ue/ue_exec.py -c "import unreal; unreal.log('hi')"
    py ue/ue_exec.py -f ue/sf_viz.py
"""
import argparse
import sys
import time
import os

UE_ROOT = os.environ.get(
    "UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")
RE_DIR = os.path.join(
    UE_ROOT, r"Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
if RE_DIR not in sys.path:
    sys.path.append(RE_DIR)

import remote_execution as remote  # noqa: E402


def connect(timeout=15.0):
    cfg = remote.RemoteExecutionConfig()
    cfg.multicast_bind_address = "127.0.0.1"
    cfg.multicast_group_endpoint = ("239.0.0.1", 6766)
    r = remote.RemoteExecution(cfg)
    r.start()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if r.remote_nodes:
            break
        time.sleep(0.3)
    if not r.remote_nodes:
        r.stop()
        raise RuntimeError(
            "UE 노드를 찾지 못했습니다. 에디터가 떠 있고 "
            "Python > Enable Remote Execution 이 켜져 있는지 확인하세요.")
    node = r.remote_nodes[0]
    r.open_command_connection(node["node_id"])
    return r, node


def run(code, exec_file=False):
    r, node = connect()
    try:
        mode = (remote.MODE_EXEC_FILE if exec_file
                else remote.MODE_EXEC_STATEMENT)
        res = r.run_command(code, exec_mode=mode, unattended=True)
        return res
    finally:
        r.close_command_connection()
        r.stop()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("-c", "--command", help="실행할 파이썬 구문")
    g.add_argument("-f", "--file", help="실행할 .py 파일 경로")
    a = ap.parse_args()

    if a.file:
        res = run(os.path.abspath(a.file), exec_file=True)
    else:
        res = run(a.command)

    ok = res.get("success")
    for line in res.get("output") or []:
        print(f"[{line.get('type','Log')}] {line.get('output','').rstrip()}")
    if res.get("result") not in (None, "None", ""):
        print("result:", res["result"])
    print("success:", ok)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
