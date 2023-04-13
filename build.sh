#!/bin/bash

# 이미지 빌드
docker build -t docent .

# 이전 컨테이너 중지 및 삭제
docker stop docent-container || true && docker rm docent-container || true

# 새 컨테이너 실행
docker run -d --name docent-container -p 8000:8000 docent

# 불필요한 Docker 이미지 정리
docker image prune -f

