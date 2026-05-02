# qr-gen-web

중간 과제용 QR 생성기 웹 서비스 저장소입니다.

## 목표

- URL 또는 텍스트를 입력받아 QR 코드를 PNG로 반환
- `/health` 엔드포인트로 서비스 상태 확인
- GitHub Actions, Docker, Render까지 이어지는 DevOps 파이프라인 구성

## Docker

```bash
docker build -t qr-gen-web .
docker run --rm -p 8000:8000 qr-gen-web
```

기본 포트는 `8000`. 클라우드에서 넘기는 `PORT` 환경 변수를 그대로 씁니다.

브라우저에서 `http://localhost:8000` 접속.

## 진행 상태

- [x] 저장소 초기화 (`README`, `LICENSE`, `.gitignore`)
- [x] 웹 앱 스캐폴드 및 `/health`
- [x] QR 생성 API
- [x] 테스트 및 CI
- [x] Docker 이미지
- [ ] Render 배포
