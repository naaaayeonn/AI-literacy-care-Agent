// 집중도(focus_score) 실시간 디버그 모니터 — window.ALC_Debug
//
// 목적: 집중도 지수에 영향을 주는 파라미터를 "다른 창"에 실시간으로 띄워 확인한다.
//   - 클라이언트 원본 이벤트(tracker): scroll 간격(duration_ms)·진행률·blur·pause
//   - 서버 계산 결과(/events 응답): focusScore·개입 레벨 + 감점 내역(debug.penalty 등)
//
// ⚠️ CSP 주의: 확장 컨텍스트에서 window.open("")로 연 about:blank 창에는 script-src 'self'
//    류 CSP가 적용돼 **인라인 <script> 실행이 차단**된다. 그래서 자식 창 문서에는 스크립트를
//    두지 않고, 렌더링은 전부 이 부모(content script) 쪽에서 자식 창의 DOM을 직접 조작해서 한다.
//    부모 스크립트는 자식 CSP의 제약을 받지 않으므로 확장/웹 어디서든 동작한다.
//    (자식 about:blank는 여는 문서와 동일 오리진이라 부모가 w.document에 접근 가능하다.)
// 열기: content_script의 단축키(Ctrl+Shift+F) 또는 session_client의 attachSession().
window.ALC_Debug = (() => {
  const S = {
    win: null,
    doc: null,
    sessionId: null,
    startAt: null,
    events: [],
    series: [],
    last: null,
    timer: null,
    scrollPxMs: 0,
    scrollPctS: 0,
    scrollPeak: 0,
    scrollLastAt: 0,
  };

  // 자식 창 문서: 마크업 + 스타일만. 스크립트 없음(CSP 회피).
  const MONITOR_HTML = [
    '<!doctype html><html lang="ko"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<title>집중도 실시간 모니터</title>',
    '<style>',
    ':root{color-scheme:dark;}',
    '*{box-sizing:border-box;}',
    'body{margin:0;font-family:system-ui,"Segoe UI",Roboto,"Malgun Gothic",sans-serif;',
    'background:#0d1117;color:#e6edf3;font-size:13px;line-height:1.4;padding:14px;}',
    'h1{font-size:14px;margin:0 0 2px;font-weight:700;}',
    '.sub{color:#8b949e;font-size:11px;margin-bottom:12px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;}',
    '.dot{width:8px;height:8px;border-radius:50%;background:#6e7681;display:inline-block;margin-right:4px;}',
    '.dot.on{background:#3fb950;box-shadow:0 0 6px #3fb950;}',
    '.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px;margin-bottom:12px;}',
    '.focusrow{display:flex;align-items:baseline;gap:10px;}',
    '#focusVal{font-size:44px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}',
    '#focusUnit{color:#8b949e;font-size:14px;}',
    '.chip{margin-left:auto;padding:4px 10px;border-radius:999px;font-weight:700;font-size:12px;',
    'background:#21262d;border:1px solid #30363d;}',
    '.bar{position:relative;height:12px;border-radius:6px;background:#21262d;margin-top:12px;overflow:hidden;}',
    '.bar>span{position:absolute;left:0;top:0;bottom:0;border-radius:6px;transition:width .2s,background .2s;}',
    '.ticks{position:relative;height:14px;margin-top:2px;}',
    '.ticks i{position:absolute;top:0;font-size:9px;color:#6e7681;transform:translateX(-50%);}',
    '.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}',
    '.cell{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:8px;}',
    '.cell .k{color:#8b949e;font-size:10px;}',
    '.cell .v{font-size:18px;font-weight:700;font-variant-numeric:tabular-nums;margin-top:2px;}',
    '.sect{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.04em;margin:0 0 8px;}',
    '.pline{display:flex;align-items:center;gap:8px;margin-bottom:6px;}',
    '.pline .lbl{width:96px;color:#c9d1d9;font-size:12px;}',
    '.pline .track{flex:1;height:9px;background:#21262d;border-radius:5px;overflow:hidden;}',
    '.pline .track>span{display:block;height:100%;background:#f85149;width:0;transition:width .2s;}',
    '.pline .num{width:46px;text-align:right;font-variant-numeric:tabular-nums;color:#ffa198;}',
    'canvas{width:100%;height:80px;display:block;}',
    '#log{max-height:230px;overflow:auto;font-family:ui-monospace,Consolas,monospace;font-size:11px;}',
    '.ev{display:flex;gap:8px;padding:3px 0;border-bottom:1px solid #161b22;white-space:nowrap;}',
    '.ev .t{color:#6e7681;width:52px;text-align:right;}',
    '.ev .ty{width:56px;font-weight:700;}',
    '.ev .d{color:#8b949e;overflow:hidden;text-overflow:ellipsis;}',
    '.ty.scroll{color:#58a6ff;}.ty.blur{color:#f85149;}.ty.focus{color:#3fb950;}',
    '.ty.pause{color:#d29922;}.ty.fast{color:#ff7b72;}',
    '.hint{color:#6e7681;font-size:10px;margin-top:6px;}',
    '</style></head><body>',
    '<h1>🎯 집중도 실시간 모니터</h1>',
    '<div class="sub"><span><span id="dot" class="dot"></span><span id="conn">대기 중</span></span>',
    '<span id="sid">session: —</span><span id="elapsed">00:00</span></div>',

    '<div class="card"><div class="focusrow">',
    '<span id="focusVal">--</span><span id="focusUnit">/100</span>',
    '<span id="lvlChip" class="chip">—</span></div>',
    '<div class="bar"><span id="focusFill" style="width:0"></span></div>',
    '<div class="ticks"><i style="left:30%">30</i><i style="left:50%">50</i><i style="left:75%">75</i></div>',
    '<div id="nudge" class="hint"></div></div>',

    '<div class="card" style="padding:10px 12px;">',
    '<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;">',
    '<span class="k" style="font-size:11px;">스크롤 속도</span>',
    '<span id="scrollPxMs" style="font-size:26px;font-weight:800;font-variant-numeric:tabular-nums;color:#58a6ff;">0.00</span>',
    '<span class="k" style="font-size:11px;">px/ms</span>',
    '<span id="scrollPctS" style="font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;color:#3fb950;margin-left:14px;">0.0</span>',
    '<span class="k" style="font-size:11px;">%/초</span>',
    '<span class="k" style="margin-left:auto;font-size:11px;">최고 <b id="scrollPeak" style="color:#c9d1d9;">0.00</b> px/ms</span>',
    '</div>',
    '<div style="margin-top:6px;font-size:10px;color:#6e7681;">정상 ~0.6 · <span style="color:#f85149;">비정상 ≥1.5 px/ms(감점)</span>',
    '<span id="abnBadge" style="display:none;margin-left:8px;color:#fff;background:#f85149;border-radius:4px;padding:1px 6px;font-weight:700;">⚠ 비정상 읽기</span></div>',
    '</div>',

    '<div class="card"><div class="grid">',
    '<div class="cell"><div class="k">진행률</div><div class="v" id="mProg">0%</div></div>',
    '<div class="cell"><div class="k">총 이벤트</div><div class="v" id="mTotal">0</div></div>',
    '<div class="cell"><div class="k">개입 필요</div><div class="v" id="mNeed">—</div></div>',
    '<div class="cell"><div class="k">이탈(blur)</div><div class="v" id="mBlur">0</div></div>',
    '<div class="cell"><div class="k">고속 스크롤(≥1.5)</div><div class="v" id="mHighVel" style="color:#ff7b72;">0</div></div>',
    '<div class="cell"><div class="k">멈춤(pause)</div><div class="v" id="mPause">0</div></div>',
    '</div></div>',

    '<div class="card"><p class="sect">감점 내역 (최근 12개 이벤트 창 · 100에서 차감)</p>',
    '<div class="pline"><span class="lbl">이탈(blur)</span><span class="track"><span id="pBlur"></span></span><span class="num" id="pBlurN">0</span></div>',
    '<div class="pline"><span class="lbl">스키밍스크롤</span><span class="track"><span id="pSkim"></span></span><span class="num" id="pSkimN">0</span></div>',
    '<div class="pline"><span class="lbl">멈춤(pause)</span><span class="track"><span id="pPause"></span></span><span class="num" id="pPauseN">0</span></div>',
    '<div class="pline"><span class="lbl">정체(dwell)</span><span class="track"><span id="pDwell"></span></span><span class="num" id="pDwellN">0</span></div>',
    '<div class="pline"><span class="lbl">총 감점</span><span class="track"><span id="pTot"></span></span><span class="num" id="pTotN">0</span></div></div>',

    '<div class="card"><p class="sect">집중도 추이</p><canvas id="spark" width="420" height="80"></canvas></div>',

    '<div class="card"><p class="sect">이벤트 로그 (클라이언트 원본)</p><div id="log"></div>',
    '<div class="hint">scroll: 직전과의 간격(ms)·진행률 · blur: 이탈시간(ms) · 간격 300ms 미만은 빠른스크롤 감점.</div></div>',
    '</body></html>',
  ].join("\n");

  const LEVEL_LABEL = {
    none: "개입 없음",
    soft: "SOFT 하이라이트",
    medium: "MEDIUM 재읽기",
    hard: "HARD 퀴즈",
  };

  function isOpen() {
    return !!(S.win && !S.win.closed);
  }

  function el(id) {
    return S.doc ? S.doc.getElementById(id) : null;
  }
  function setText(id, t) {
    const e = el(id);
    if (e) e.textContent = t;
  }
  function pad(n) {
    n = Math.floor(n);
    return (n < 10 ? "0" : "") + n;
  }
  function color(v) {
    return v >= 75 ? "#3fb950" : v >= 50 ? "#d29922" : v >= 30 ? "#ff9800" : "#f85149";
  }
  function setConn(on) {
    const d = el("dot");
    if (d) d.className = "dot" + (on ? " on" : "");
    setText("conn", on ? "세션 연결됨" : "대기 중");
  }

  function renderScrollSpeed() {
    const abnormal = S.scrollPxMs >= 1.5; // 비정상 읽기 임계
    const pxEl = el("scrollPxMs");
    if (pxEl) {
      pxEl.textContent = S.scrollPxMs.toFixed(2);
      pxEl.style.color = abnormal ? "#f85149" : "#58a6ff";
    }
    const badge = el("abnBadge");
    if (badge) badge.style.display = abnormal ? "inline-block" : "none";
    setText("scrollPctS", S.scrollPctS.toFixed(1));
    setText("scrollPeak", S.scrollPeak.toFixed(2));
  }

  function ensureOpen() {
    if (isOpen()) {
      S.win.focus();
      return true;
    }
    let w;
    try {
      w = window.open("", "alc_focus_monitor", "width=480,height=860,resizable=yes,scrollbars=yes");
    } catch (_) {
      w = null;
    }
    if (!w) {
      console.warn("[ALC-Debug] 팝업이 차단되었습니다. Ctrl+Shift+F로 다시 시도하세요.");
      return false;
    }
    S.win = w;
    try {
      w.document.open();
      w.document.write(MONITOR_HTML);
      w.document.close();
      S.doc = w.document;
    } catch (e) {
      console.warn("[ALC-Debug] 모니터 문서 작성 실패:", e);
      S.win = null;
      S.doc = null;
      return false;
    }
    startTimer();
    renderAll();
    return true;
  }

  function startTimer() {
    if (S.timer) clearInterval(S.timer);
    S.timer = setInterval(() => {
      if (!isOpen()) {
        clearInterval(S.timer);
        S.timer = null;
        return;
      }
      if (S.startAt) {
        const s = Math.floor((Date.now() - S.startAt) / 1000);
        setText("elapsed", pad(s / 60) + ":" + pad(s % 60));
      }
      // 스크롤이 멈추면 현재 속도를 0으로 감쇠(최고 속도는 유지).
      if ((S.scrollPxMs > 0 || S.scrollPctS > 0) && Date.now() - S.scrollLastAt > 700) {
        S.scrollPxMs = 0;
        S.scrollPctS = 0;
        renderScrollSpeed();
      }
    }, 700);
  }

  function appendRow(e) {
    const doc = S.doc;
    const log = el("log");
    if (!doc || !log) return;
    // ⚡(스키밍) 라벨은 실제 감점 기준과 동일하게 velocity(≥1.5 px/ms)로 판정한다.
    // (이전엔 간격<300ms 기준이라 정상 스크롤에도 ⚡가 붙어 감점처럼 오해됐다.)
    const isFast = e.type === "scroll" && e.velocity != null && e.velocity >= 1.5;
    const row = doc.createElement("div");
    row.className = "ev";
    const t = doc.createElement("span");
    t.className = "t";
    t.textContent = ((e.timestamp_ms || 0) / 1000).toFixed(1) + "s";
    const ty = doc.createElement("span");
    ty.className = "ty " + (isFast ? "fast" : e.type);
    ty.textContent = isFast ? "scroll⚡" : e.type;
    const d = doc.createElement("span");
    d.className = "d";
    const parts = [];
    if (e.duration_ms != null && e.type === "scroll") parts.push("Δ" + Math.round(e.duration_ms) + "ms");
    if (e.velocity != null && e.type === "scroll") parts.push(e.velocity.toFixed(2) + "px/ms");
    if (e.speed_pct_s != null && e.type === "scroll") parts.push(e.speed_pct_s.toFixed(1) + "%/s");
    if (e.duration_ms != null && e.type === "blur") parts.push("이탈 " + Math.round(e.duration_ms) + "ms");
    if (e.position != null) parts.push("pos " + Math.round(e.position * 100) + "%");
    d.textContent = parts.join(" · ");
    row.appendChild(t);
    row.appendChild(ty);
    row.appendChild(d);
    log.insertBefore(row, log.firstChild);
    while (log.childNodes.length > 60) log.removeChild(log.lastChild);
  }

  function applyResponse(r) {
    if (!isOpen()) return;
    setConn(true);
    const f = r.focusScore != null ? r.focusScore : r.debug && r.debug.focusScore;
    if (f != null) {
      const fv = el("focusVal");
      if (fv) {
        fv.textContent = Math.round(f);
        fv.style.color = color(f);
      }
      const ff = el("focusFill");
      if (ff) {
        ff.style.width = Math.max(0, Math.min(100, f)) + "%";
        ff.style.background = color(f);
      }
    }
    const dbg = r.debug || {};
    const lvl = dbg.interventionLevel || r.nudgeLevel || "none";
    const chip = el("lvlChip");
    if (chip) {
      chip.textContent = LEVEL_LABEL[lvl] || lvl;
      chip.style.color = lvl === "none" ? "#3fb950" : lvl === "soft" ? "#d29922" : "#f85149";
    }
    setText("nudge", r.nudgeMessage || "");
    if (r.progress != null) setText("mProg", Math.round(r.progress) + "%");
    if (dbg.interventionNeeded != null) setText("mNeed", dbg.interventionNeeded ? "YES" : "no");
    const c = dbg.eventCounts || {};
    if (c.total != null) setText("mTotal", c.total);
    if (c.blur != null) setText("mBlur", c.blur);
    if (c.highVelocity != null) setText("mHighVel", c.highVelocity);
    if (c.pause != null) setText("mPause", c.pause);
    const p = dbg.penalty || {};
    pen("pBlur", "pBlurN", p.blur);
    pen("pSkim", "pSkimN", p.skimScroll);
    pen("pPause", "pPauseN", p.pause);
    pen("pDwell", "pDwellN", p.dwell);
    pen("pTot", "pTotN", p.total);
  }

  function pen(fill, num, val) {
    const v = val || 0;
    setText(num, "-" + v.toFixed(1));
    const e = el(fill);
    if (e) e.style.width = Math.min(100, v) + "%";
  }

  function draw() {
    const c = el("spark");
    if (!c || !c.getContext) return;
    const ctx = c.getContext("2d");
    const W = c.width;
    const H = c.height;
    ctx.clearRect(0, 0, W, H);
    [[75, "#3fb950"], [50, "#d29922"], [30, "#f85149"]].forEach((g) => {
      const y = H - (g[0] / 100) * H;
      ctx.strokeStyle = "rgba(255,255,255,0.10)";
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    });
    if (S.series.length < 2) return;
    const win = S.series.slice(-60);
    const n = win.length;
    const step = W / (n - 1);
    ctx.strokeStyle = "#58a6ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const x = i * step;
      const y = H - (Math.max(0, Math.min(100, win[i])) / 100) * H;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    const last = win[n - 1];
    ctx.fillStyle = color(last);
    ctx.beginPath();
    ctx.arc((n - 1) * step, H - (last / 100) * H, 3, 0, 6.3);
    ctx.fill();
  }

  // (재)오픈 시 누적 상태를 자식 창에 다시 그린다.
  function renderAll() {
    if (!isOpen()) return;
    if (S.sessionId) {
      setText("sid", "session: " + String(S.sessionId).slice(0, 8));
      setConn(true);
    }
    const log = el("log");
    if (log) log.innerHTML = "";
    S.events.slice(-60).forEach(appendRow);
    if (S.last) applyResponse(S.last);
    renderScrollSpeed();
    draw();
  }

  return {
    ensureOpen,
    isOpen,
    toggle() {
      if (isOpen()) {
        S.win.close();
        S.win = null;
        S.doc = null;
      } else {
        ensureOpen();
      }
    },
    attachSession(id) {
      S.sessionId = id;
      S.startAt = Date.now();
      if (isOpen()) {
        setText("sid", "session: " + String(id).slice(0, 8));
        setConn(true);
      }
    },
    pushEvent(evt) {
      S.events.push(evt);
      if (S.events.length > 250) S.events.shift();
      if (evt.type === "scroll" && (evt.velocity != null || evt.speed_pct_s != null)) {
        if (evt.velocity != null) {
          S.scrollPxMs = evt.velocity;
          if (evt.velocity > S.scrollPeak) S.scrollPeak = evt.velocity;
        }
        if (evt.speed_pct_s != null) S.scrollPctS = evt.speed_pct_s;
        S.scrollLastAt = Date.now();
        if (isOpen()) renderScrollSpeed();
      }
      if (isOpen()) appendRow(evt);
    },
    pushResponse(cmd) {
      const p = (cmd && cmd.payload) || {};
      const r = {
        focusScore: p.focusScore,
        progress: p.progress,
        nudgeLevel: p.nudgeLevel,
        nudgeMessage: p.nudgeMessage,
        type: cmd && cmd.type,
        debug: cmd && cmd.debug,
      };
      S.last = r;
      const f = r.focusScore != null ? r.focusScore : r.debug && r.debug.focusScore;
      if (f != null) {
        S.series.push(f);
        if (S.series.length > 300) S.series.shift();
      }
      if (isOpen()) {
        applyResponse(r);
        draw();
      }
    },
    reset() {
      S.events = [];
      S.series = [];
      S.last = null;
      S.startAt = null;
      S.scrollPxMs = 0;
      S.scrollPctS = 0;
      S.scrollPeak = 0;
      S.scrollLastAt = 0;
      if (isOpen()) renderAll();
    },
  };
})();
