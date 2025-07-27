# NiFi CDC Core

Apache NiFi 기반 Change Data Capture (CDC) 구현을 위한 코어 프로젝트입니다.

## 프로젝트 개요

이 프로젝트는 NiFi API를 활용하여 다양한 데이터베이스와 데이터 소스 간의 CDC를 구현합니다. 초기에는 Oracle to Oracle CDC에 집중하며, 추후 PostgreSQL, Kafka, S3 등 다양한 소스로 확장할 예정입니다.

## 시작하기

### 사전 요구사항

- Apache NiFi 1.28 (외부 배포)
- Java 8 이상
- 소스/타겟 데이터베이스 접근 권한

### 설치 및 설정

1. 저장소 클론
```bash
git clone <repository-url>
cd nificdc-core
```

2. 환경 설정
```bash
cp .env.example .env
# .env 파일을 열어 필요한 접속 정보 입력
```

3. 의존성 설치 (기술 스택 결정 후)
```bash
# 예시: Python
pip install -r requirements.txt

# 예시: Node.js
npm install

# 예시: Java
mvn install
```

## 환경 변수 설정

`.env` 파일에서 다음 정보를 설정해야 합니다:

- **NiFi API 설정**: NiFi 서버 URL, 인증 정보
- **소스 DB 설정**: 데이터베이스 연결 정보
- **타겟 DB 설정**: 데이터베이스 연결 정보
- **CDC 설정**: 폴링 간격, 배치 크기 등

자세한 내용은 `.env.example` 파일을 참조하세요.

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

[라이선스 정보 추가 예정]