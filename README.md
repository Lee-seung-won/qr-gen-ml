# qr-gen-web

중간 과제용 QR 생성기 웹 서비스 저장소입니다.

## 목표

- URL 또는 텍스트를 입력받아 QR 코드를 PNG로 반환
- `/health` 엔드포인트로 서비스 상태 확인
- GitHub Actions, Docker, Render까지 이어지는 DevOps 파이프라인 구성

## 구성

| 구분 | 설명 |
|------|------|
| 앱 | FastAPI 단일 모듈 `main.py` (라우트·QR 렌더·요청 로깅 미들웨어) |
| 이미지 | `qrcode` + Pillow로 PNG 바이너리 생성 |
| 테스트 | `pytest` + `TestClient` (현재 26개) |

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | QR 입력 폼(HTML). `GET /qr`로 전송 |
| GET | `/health` | `{"status":"ok"}` JSON |
| GET | `/qr` | 쿼리 `text`(필수), `box_size`(1–30, 기본 10), `border`(0–20, 기본 4), `ecc`(`L`/`M`/`Q`/`H`, 기본 `M`). 응답 PNG |
| POST | `/api/qr` | JSON 본문 동일 옵션 + `text`. 응답 `format`, `image_base64`, `width`, `height` |

모든 응답에 `X-Request-Id`(UUID) 헤더가 붙고, 서버 로그에 `event=request_completed`와 `duration_ms`가 남습니다.

## Docker

```bash
docker build -t qr-gen-web .
docker run --rm -p 8000:8000 qr-gen-web
```

기본 포트는 `8000`. 클라우드에서 넘기는 `PORT` 환경 변수를 그대로 씁니다.

브라우저에서 `http://localhost:8000` 접속.

## 배포

- URL: https://qrgenerator-zq98.onrender.com
- 상태 확인: https://qrgenerator-zq98.onrender.com/health

Render 무료 플랜은 일정 시간 요청이 없으면 슬립했다가 첫 요청 때 깰 수 있습니다.

## 진행 상태

- [x] 저장소 초기화 (`README`, `LICENSE`, `.gitignore`)
- [x] 웹 앱 스캐폴드 및 `/health`
- [x] QR 생성 API
- [x] 테스트 및 CI
- [x] Docker 이미지
- [x] Render 배포
