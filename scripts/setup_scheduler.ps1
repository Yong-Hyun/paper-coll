<#
.SYNOPSIS
    Windows 작업 스케줄러에 논문 수집 에이전트를 등록합니다.

.DESCRIPTION
    이 스크립트를 관리자 권한으로 실행하면:
    - 매일 오전 9시에 자동으로 논문 수집 에이전트가 실행됩니다.
    - PC가 꺼져 있었으면 로그인 후 가능한 빨리 실행됩니다.
    - 실행 시간을 변경하려면 아래 $TriggerTime 변수를 수정하세요.

.NOTES
    실행 방법:
      PowerShell을 관리자 권한으로 열고:
        .\scripts\setup_scheduler.ps1

    제거 방법:
      Unregister-ScheduledTask -TaskName "PaperCollectionAgent" -Confirm:$false
#>

param(
    [string]$TriggerTime = "09:00"  # 매일 실행할 시간 (24시간 형식)
)

$ErrorActionPreference = "Stop"

# ─── 경로 설정 ─────────────────────────────────────
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BatchFile = Join-Path $ProjectRoot "run_agent.bat"
$TaskName = "PaperCollectionAgent"
$Description = "AI 논문 자동 수집 에이전트 - 매일 $TriggerTime 에 arXiv, HuggingFace에서 논문을 수집합니다."

# ─── Python 확인 ───────────────────────────────────
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Error "Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다."
    exit 1
}
Write-Host "[+] Python 경로: $PythonPath" -ForegroundColor Green

# ─── 기존 작업 제거 ────────────────────────────────
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[*] 기존 작업 '$TaskName'을 제거합니다..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ─── 트리거 설정 ───────────────────────────────────
$Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime

# ─── 액션 설정 ─────────────────────────────────────
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "-m src.agent" `
    -WorkingDirectory $ProjectRoot

# ─── 설정 옵션 ─────────────────────────────────────
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# ─── 작업 등록 ─────────────────────────────────────
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $Description `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  ✅ 작업 스케줄러 등록 완료!" -ForegroundColor Green
Write-Host "  작업 이름: $TaskName" -ForegroundColor Cyan
Write-Host "  실행 시간: 매일 $TriggerTime" -ForegroundColor Cyan
Write-Host "  프로젝트 경로: $ProjectRoot" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "확인:  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "즉시 실행: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "제거:  Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
