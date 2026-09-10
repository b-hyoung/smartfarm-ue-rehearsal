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


PROJECT = os.environ.get("SF_UE_PROJECT", "SF_Rehearsal")


def connect(timeout=15.0):
    """⚠ 에디터가 두 개(예: UEFN + UE) 떠 있으면 둘 다 같은 멀티캐스트에
    응답한다. 첫 노드를 무조건 잡으면 명령이 엉뚱한 프로젝트에 들어간다
    (실제로 UEFN TestProject 에 에어컨이 스폰되는 사고가 났다).
    → project_name 이 SF_UE_PROJECT(기본 SF_Rehearsal)인 노드를 고른다."""
    cfg = remote.RemoteExecutionConfig()
    cfg.multicast_bind_address = "127.0.0.1"
    cfg.multicast_group_endpoint = ("239.0.0.1", 6766)
    r = remote.RemoteExecution(cfg)
    r.start()
    deadline = time.time() + timeout
    node = None
    while time.time() < deadline:
        nodes = list(r.remote_nodes)
        for n in nodes:
            if n.get("project_name") == PROJECT:
                node = n
                break
        if node:
            break
        # 원하는 프로젝트가 아직 안 보이면 다른 노드가 있어도 좀 더 기다린다
        time.sleep(0.3)
    if node is None:
        nodes = list(r.remote_nodes)
        r.stop()
        if nodes:
            names = ", ".join(str(n.get("project_name")) for n in nodes)
            raise RuntimeError(
                "프로젝트 '%s' 노드가 없습니다 (발견된 노드: %s). "
                "SF_UE_PROJECT 환경변수로 대상을 바꿀 수 있습니다." % (PROJECT, names))
        raise RuntimeError(
            "UE 노드를 찾지 못했습니다. 에디터가 떠 있고 "
            "Python > Enable Remote Execution 이 켜져 있는지 확인하세요.")
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
