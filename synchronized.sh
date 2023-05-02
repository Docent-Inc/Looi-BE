#!/bin/bash

# 자동 생성된 마이그레이션 파일 생성
alembic revision --autogenerate -m "Database changes"

# 데이터베이스를 최신 상태로 업데이트
alembic upgrade head
