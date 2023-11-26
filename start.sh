#!/bin/bash

# Redis 데이터 플러시
redis-cli flushall

# Redis 서버 재시작 (기본 설정 사용)
redis-server &

# Uvicorn으로 FastAPI 애플리케이션 실행
uvicorn main:app --host 0.0.0.0 --port 8001 --reload --workers 1