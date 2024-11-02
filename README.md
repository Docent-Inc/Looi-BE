# 루이 (Looi)

루이는 쉽고 빠른 기록 서비스입니다.

## 설치 및 환경 설정

1. 저장소를 클론합니다.
    ```bash
    git clone https://github.com/HypeDMZ/Docent-BE
    ```

2. 필요한 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```
   

## 실행
- FastAPI 및 Python 환경에서 작동합니다. 아래 명령어로 실행할 수 있습니다.
    ```bash
    uvicorn main:app --reload
    ```

## 배포

도슨트는 git action을 통한 Docker CI/CD 배포를 사용하며, Green-Blue 방식으로 무중단 배포 환경이 설정되어 있습니다. 메인 브랜치로 풀(Pull) 또는 푸시(Push)하면 작동하도록 설정되어 있습니다.

## 테스트

/docs에서 테스트를 진행할 수 있습니다. 로그인 후 JWT 토큰을 APIKeyHeader에 "Bearer "와 함께 설정하고 나머지 API를 테스트할 수 있습니다.

## 문서 및 개발 가이드

개발 가이드라인과 API 엔드포인트 정보는 모두 노션에 정리되어 있습니다.

## 개발자 정보

- 이름: 조태완
- 이메일: taewan2002@gachon.ac.kr
