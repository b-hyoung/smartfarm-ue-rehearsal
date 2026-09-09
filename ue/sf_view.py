"""뷰포트 카메라를 옮기고 HighResShot 을 찍는다.

⚠ 함정 두 개
  1. unreal.UnrealEditorSubsystem() 은 **새 객체**를 만든다. 실제 뷰포트를 조종하려면
     반드시 unreal.get_editor_subsystem(...) 으로 살아있는 인스턴스를 가져와야 한다.
  2. HighResShot 은 뷰포트가 실제로 다시 그려질 때 저장된다. 에디터가 백그라운드면
     Slate 가 스로틀링해서 몇 분이 지나도 파일이 안 나온다 → 창을 포그라운드로.

환경변수
  SF_CAM  = "x,y,z,pitch,yaw"   (cm, deg)
"""
import os
import unreal

CAM = os.environ.get("SF_CAM", "-700,-650,700,-20,40")
v = [float(t) for t in CAM.split(",")]

# ⚠ get_editor_subsystem(UnrealEditorSubsystem) 로 받은 인스턴스에 set 을 걸면
#   에러 없이 무시된다 (get 은 되는데 set 만 안 먹음). 생성자 형태는 먹는다.
ues = unreal.UnrealEditorSubsystem()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

ues.set_level_viewport_camera_info(unreal.Vector(v[0], v[1], v[2]),
                                   unreal.Rotator(0.0, v[3], v[4]))
les.editor_set_viewport_realtime(True, "sfshot")
w = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(w, "HighResShot 1600x900")

loc, rot = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_level_viewport_camera_info()
print("SF_VIEW: cam=(%.0f,%.0f,%.0f) pitch=%.0f yaw=%.0f" %
      (loc.x, loc.y, loc.z, rot.pitch, rot.yaw))
