<#
.SYNOPSIS
    Windows 작업 스케줄러에서 논문 수집 에이전트 작업을 제거합니다.

.DESCRIPTION
    관리자 권한으로 실행하세요.
#>

$TaskName = "PaperCollectionAgent"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ 작업 '$TaskName'이 성공적으로 제거되었습니다." -ForegroundColor Green
} else {
    Write-Host "⚠️ 작업 '$TaskName'이 존재하지 않습니다." -ForegroundColor Yellow
}
