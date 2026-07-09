# AI 리터러시 케어 — 데모 서버 종료
$found = $false
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object {
    try { Stop-Process -Id $_.OwningProcess -Force; $script:found = $true } catch {}
  }
if ($found) { Write-Host "✅ 데모 서버(:8000)를 종료했습니다." -ForegroundColor Green }
else        { Write-Host "실행 중인 데모 서버가 없습니다." -ForegroundColor DarkGray }
Start-Sleep -Seconds 1
