# ParseKit Converter

ParseKit LibreOffice 기반 문서-PDF 변환 API 서버

## 지원 포맷

**변환 가능 (→ PDF)**

- Microsoft Office: `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- 한글: `.hwp`, `.hwpx`
- OpenDocument: `.odt`, `.odp`, `.ods`

**패스스루 (그대로 반환)**

- PDF: `.pdf`
- 이미지: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`

## API

### `POST /convert`

문서를 PDF로 변환하여 JSON으로 반환 (base64 인코딩)

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@document.docx"
```

**응답:**

```json
{
  "code": 0,
  "data": {
    "filename": "document.pdf",
    "content": "JVBERi0xLjQK...",
    "size": 12345,
    "converted": true
  }
}
```

### `POST /convert/raw`

문서를 PDF로 변환하여 바이너리로 직접 반환

```bash
curl -X POST http://localhost:8080/convert/raw \
  -F "file=@document.docx" \
  -o output.pdf
```

### `GET /supported-formats`

지원 포맷 목록 조회

### `GET /health`

헬스체크

## 실행

### Docker (권장)

```bash
docker build -t parsekit-converter .
docker run -p 8080:8080 parsekit-converter
```

### 로컬 실행

**1. LibreOffice 설치**

```bash
# Ubuntu/Debian
apt-get install libreoffice libreoffice-java-common default-jre

# macOS
brew install --cask libreoffice
# + Java 설치: brew install openjdk

# Windows
# https://www.libreoffice.org/download
# + Java 설치: https://adoptium.net/
```

**2. HWP 지원 (선택)**

[H2Orestart](https://github.com/ebandal/H2Orestart) 확장 설치:

```bash
# 확장 다운로드 후 LibreOffice에 설치
wget https://github.com/ebandal/H2Orestart/releases/download/v0.7.9/H2Orestart.oxt
unopkg add H2Orestart.oxt
```

**3. 서버 실행**

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## 에러 코드

| 코드 | 설명               |
| ---- | ------------------ |
| 0    | 성공               |
| 101  | 빈 파일            |
| 201  | 변환 실패          |
| 202  | 출력 파일 없음     |
| 203  | 타임아웃           |
| 204  | LibreOffice 미설치 |
| 501  | 내부 오류          |

자세한 내용은 [docs/errors.md](docs/errors.md) 참조

## 관련 프로젝트

- [ParseKit](https://github.com/agent-hanju/parsekit) - 문서 파싱용 간단 자바 SDK
