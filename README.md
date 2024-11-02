# 나만의 기록을 돕는 AI 비서, Looi

일기, 꿈, 일정, 메모까지 모든 기록을 한 곳에서 자동으로 분류 및 저장해 주고, 이 기록을 토대로 한 주 돌아보기 등의 인사이트와 콘텐츠를 제공해 주는 서비스입니다 🤖🌙

![LOOK-IR-소개](https://github.com/Docent-Inc/Docent-Front/assets/87323603/2cf2ddfc-f0bc-45cc-8944-6a843d93a419)

<br/>

## System Architecture
![System Architecture](https://github.com/Docent-Inc/Docent-Front/assets/87323603/c3429686-2eb8-4258-8fdc-8a4ef9032288)

- **Frontend** `vue` `nuxt` SSR로 API와 동일 서버에 배포
- **Android**  웹에 PWA 세팅하여 PWA Builder로 파일 빌드 / 웹단에서 service worker로 푸시 구현
- **[iOS](https://github.com/Docent-Inc/Docent-IOS)** `swift` WKWebView로 웹 패키징 / 네이티브 앱에서 Notification Service Extension 추가하여 푸시 구현

<br/>

## Features
![image](https://github.com/Docent-Inc/Docent-Front/assets/87323603/1d50eb88-dd50-4036-ab15-1f49c8a82532)
![image](https://github.com/Docent-Inc/Docent-Front/assets/87323603/3da02f0f-be45-4fd4-9e84-b0e56d846b92)


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
