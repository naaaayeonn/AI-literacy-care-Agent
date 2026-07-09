# ============================================================
# AI 리터러시 케어 — 데모 원클릭 시작 스크립트
# 하는 일: 최신 main 반영 → 프론트 빌드 → 백엔드 기동 → 브라우저 열기
# 실행 결과: http://localhost:8000 하나에서 전체(1·2·3·4·5번 통합) 동작
# ============================================================
$ErrorActionPreference = "Stop"

# 스크립트 위치 기준으로 프로젝트 루트 자동 계산 (demo/ 의 상위 = team-full)
$ROOT    = Split-Path -Parent $PSScriptRoot
$BACKEND = Join-Path $ROOT "3. Cognitive Care Backend"
$WEB     = Join-Path $ROOT "apps\web"
$PY      = Join-Path $ROOT ".venv\Scripts\python.exe"

# DB/Redis 없이도 도는 데모 기본값 (SQLite 파일 + InMemory 캐시)
$env:DATABASE_URL   = "sqlite+aiosqlite:///./literacy_care.db"
$env:VITE_API_BASE_URL = ""        # 같은 오리진(/api)으로 호출
$env:VITE_USE_MOCK  = "false"      # 실제 백엔드 사용(목업 아님)

function Say($m, $c="White") { Write-Host $m -ForegroundColor $c }

Say "`n=== AI 리터러시 케어 데모 준비 시작 ===`n" Cyan

# [1/5] 최신 main 반영 (실패해도 현재 코드로 계속)
Say "[1/5] GitHub main 최신 반영..."
Set-Location $ROOT
try { git pull origin main } catch { Say "  ! git pull 실패 — 현재 로컬 코드로 계속 진행합니다." Yellow }

# [2/5] 백엔드 의존성 (venv 없으면 생성, 이미 있으면 즉시 통과)
Say "[2/5] 백엔드 의존성 확인..."
if (-not (Test-Path $PY)) {
  Say "  가상환경(.venv) 생성 중..." Yellow
  python -m venv (Join-Path $ROOT ".venv")
}
& $PY -m pip install -q --upgrade pip
& $PY -m pip install -q -r (Join-Path $BACKEND "requirements.txt")
& $PY -m pip install -q "psycopg[binary]" aiosqlite greenlet httpx

# [3/5] 프론트 빌드 (node_modules 없으면 설치)
Say "[3/5] 프론트엔드 빌드 (1~2분)..."
Set-Location $WEB
if (-not (Test-Path (Join-Path $WEB "node_modules"))) {
  Say "  npm 패키지 설치 중..." Yellow
  npm install
}
npm run build
if ($LASTEXITCODE -ne 0) { Say "  ! 프론트 빌드 실패. 중단합니다." Red; Read-Host "엔터로 종료"; exit 1 }

# [4/5] 빌드 결과를 백엔드가 서빙하는 위치로 배치
Say "[4/5] 정적 파일 배치..."
$dist = Join-Path $WEB "dist"
$dest = Join-Path $BACKEND "frontend_dist"
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse -Force $dist $dest

# [5/5] 백엔드 기동
Say "[5/5] 백엔드 기동 (localhost:8000)..."
# 기존 8000 포트 정리
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force } catch {} }
Start-Sleep -Milliseconds 500
# 서버를 별도 창에서 실행 (데모 내내 유지)
Start-Process -FilePath $PY -ArgumentList "run.py" -WorkingDirectory $BACKEND

# health 대기
$ok = $false
for ($i=0; $i -lt 30; $i++) {
  try { if ((Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { $ok=$true; break } } catch {}
  Start-Sleep -Seconds 1
}

if ($ok) {
  # 워밍업 — 첫 클릭이 느리지 않도록 미리 한 번 호출
  try { Invoke-WebRequest "http://localhost:8000/api/session/start" -Method POST -Body '{"userId":"warmup"}' -ContentType "application/json" -UseBasicParsing -TimeoutSec 15 | Out-Null } catch {}
  Say "`n✅ 준비 완료! 브라우저를 엽니다 → http://localhost:8000" Green
  Say "   (종료하려면 stop_demo.bat 실행)`n" DarkGray
  Start-Process "http://localhost:8000"
} else {
  Say "`n⚠️ 서버가 응답하지 않습니다. 백엔드 창의 에러 로그를 확인하세요." Red
}
Read-Host "이 창은 닫아도 됩니다. 엔터로 종료"
