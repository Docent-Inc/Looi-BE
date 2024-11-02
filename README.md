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
