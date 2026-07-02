# vendored pdf.js

크롬 기본 PDF뷰어(PDFium)는 확장이 글자·좌표에 접근할 수 없어서, PDF를 우리 뷰어가
직접 렌더한다(EXTENSION_DESIGN §9). 여기에 **pdf.js 배포본을 번들**한다(자체 호스팅, 외부 CDN 미사용).

- 라이브러리: [Mozilla pdf.js](https://github.com/mozilla/pdf.js)
- 버전: **pdfjs-dist@4.10.38**
- 라이선스: **Apache-2.0** (무료)
- 파일:
  - `pdf.mjs` — 메인 모듈
  - `pdf.worker.mjs` — 워커(파싱/렌더)

## 사용처

`extension/pdf/viewer.js`에서 ES module로 import하고, 워커 경로를
`chrome.runtime.getURL("vendor/pdfjs/pdf.worker.mjs")`로 지정한다.

## 업데이트 방법 (무비용)

```bash
ver=4.10.38   # 원하는 버전
base="https://cdn.jsdelivr.net/npm/pdfjs-dist@${ver}/build"
curl -fsSL -o pdf.mjs        "$base/pdf.mjs"
curl -fsSL -o pdf.worker.mjs "$base/pdf.worker.mjs"
```

> 스캔(이미지) PDF는 텍스트 레이어가 없어 그대로는 본문 추출이 안 된다.
> OCR(Tesseract.js·Apache-2.0·무료)은 후속 단계(EXTENSION_DESIGN §11).
