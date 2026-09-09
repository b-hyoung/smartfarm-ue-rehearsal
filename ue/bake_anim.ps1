# SF_Rehearsal: 15프레임 애니메이션을 PNG 로 굽는다. (목적 O3)
#
#   powershell -ExecutionPolicy Bypass -File ue\bake_anim.ps1
#
# UE 의 take_high_res_screenshot 은 비동기라 파일이 안 떨어질 때가 많아,
# 프레임마다 (1) 파이썬으로 그리기 → (2) UE 창 직접 캡처 로 간다.

$ErrorActionPreference = "Stop"
$Repo    = "C:\Users\hunvr\Desktop\bobs_projects\smartfarm-ue-rehearsal"
$OutDir  = "C:\Users\hunvr\Desktop\smartfarm-cfd\out\ue_anim"
$Frames  = 0..14

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Add-Type @"
using System; using System.Runtime.InteropServices;
public class UEWin {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int t,bool r);
}
"@
Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$ue = Get-Process UnrealEditor -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ue) { throw "UnrealEditor 가 실행 중이 아닙니다." }

# 창을 주 모니터에 고정 배치 — 캡처 좌표를 안정시키기 위함
[UEWin]::ShowWindow($ue.MainWindowHandle, 9) | Out-Null      # SW_RESTORE
[UEWin]::MoveWindow($ue.MainWindowHandle, 0, 0, 2560, 1400, $true) | Out-Null
[UEWin]::SetForegroundWindow($ue.MainWindowHandle) | Out-Null
Start-Sleep -Seconds 3

# 뷰포트 영역만 잘라낸다 (좌측 패널·툴바 제외)
$VX, $VY, $VW, $VH = 720, 165, 1800, 1150

function Invoke-UE([string]$code) {
    $out = & py "$Repo\ue\ue_exec.py" -c $code 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Host "  ! $out" }
}

foreach ($i in $Frames) {
    $n = "{0:d2}" -f $i
    $py = "import os; os.environ['SF_FRAME']='$i'; " +
          "exec(open(r'$Repo\ue\sf_animate.py', encoding='utf-8').read())"
    Invoke-UE $py
    Start-Sleep -Milliseconds 1200          # 뷰포트 갱신 대기

    $bmp = New-Object System.Drawing.Bitmap $VW, $VH
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($VX, $VY, 0, 0, $bmp.Size)
    $path = Join-Path $OutDir "anim_$n.png"
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Host "frame $n -> $path"
}

Write-Host "DONE: $($Frames.Count) frames -> $OutDir"
