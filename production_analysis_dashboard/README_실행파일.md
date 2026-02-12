# 실행파일 사용 가이드 (통일본)

## 빠른 실행
이제 `run_dashboard.bat` 하나만 사용합니다.
```bash
# 기본 실행 (포트 8504)
run_dashboard.bat

# 포트 지정
run_dashboard.bat 8501

# 헤드리스 실행
run_dashboard.bat 8504 headless

# 의존성 설치 후 실행
run_dashboard.bat 8504 headless install
```

## 비고
- 기존 `start_dashboard*.bat`는 정리되었습니다.
- 데스크톱 바로가기 등 추가 자동화가 필요하면 `create_desktop_shortcut.vbs`만 참고하세요.
