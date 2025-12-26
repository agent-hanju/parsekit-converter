# Error Codes

parsekit-converter API 에러 코드 정의 문서입니다.

## 응답 형식

모든 API 응답은 다음 형식을 따릅니다:

```json
{
  "code": 0,
  "message": null,
  "data": { ... }
}
```

- `code`: 0이면 성공, 그 외는 에러 코드
- `message`: 에러 메시지 (성공 시 null)
- `data`: 응답 데이터 (에러 시 null)

---

## 에러 코드 체계

| 범위 | 카테고리                |
| ---- | ----------------------- |
| 1xx  | 입력 검증               |
| 2xx  | 파일 변환 (LibreOffice) |
| 3xx  | 이미지 변환 (Poppler)   |
| 5xx  | 시스템/인프라           |

---

## 1xx: 입력 검증 에러

| 코드 | 이름       | 설명                     |
| ---- | ---------- | ------------------------ |
| 101  | EMPTY_FILE | 업로드된 파일이 비어있음 |

---

## 2xx: 파일 변환 에러

LibreOffice를 사용한 문서 변환 과정에서 발생하는 에러입니다.

| 코드 | 이름                        | 설명                              |
| ---- | --------------------------- | --------------------------------- |
| 201  | CONVERSION_FAILED           | LibreOffice 변환 실패             |
| 202  | CONVERSION_OUTPUT_NOT_FOUND | 변환 완료 후 출력 PDF 파일 없음   |
| 203  | CONVERSION_TIMEOUT          | LibreOffice 변환 타임아웃 (120초) |
| 204  | LIBREOFFICE_NOT_FOUND       | LibreOffice 미설치                |

---

## 3xx: 이미지 변환 에러

PDF를 이미지로 변환하는 과정에서 발생하는 에러입니다.

| 코드 | 이름                    | 설명                   |
| ---- | ----------------------- | ---------------------- |
| 301  | IMAGE_CONVERSION_FAILED | 이미지 변환 실패       |
| 302  | POPPLER_NOT_FOUND       | Poppler 미설치         |

---

## 5xx: 시스템 에러

| 코드 | 이름           | 설명                       |
| ---- | -------------- | -------------------------- |
| 501  | INTERNAL_ERROR | 예상치 못한 내부 서버 에러 |

---

## 에러 응답 예시

```json
{
  "code": 203,
  "message": "LibreOffice conversion timed out",
  "data": null
}
```
