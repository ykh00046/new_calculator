# 🧪 사출계획 약품/잉크 종류 계산기

사출계획과 BOM 파일을 업로드하여 일자별 필요한 약품/잉크 종류를 자동 계산하는 웹 애플리케이션입니다.

![Screenshot](assets/images/screenshot.png)

## ✨ 주요 기능

- 📅 **엑셀 파일 업로드**: 사출계획 및 BOM Tree 파일 지원
- 🔗 **자동 제품 매칭**: 유사도 기반 자동 매칭 + 수동 매칭 관리
- 📊 **일자별 계산**: 약품/잉크 종류별 필요량 계산 (배수 적용)
- 📥 **엑셀 다운로드**: 계산 결과를 CSV 형태로 다운로드
- 📱 **반응형 디자인**: 데스크톱/모바일 모두 지원
- 💾 **자동 저장**: 매칭 정보 브라우저 저장

## 🚀 빠른 시작

### 온라인 사용
GitHub Pages에서 바로 사용할 수 있습니다:
👉 **[https://username.github.io/injection-calculator](https://username.github.io/injection-calculator)**

### 로컬 실행
```bash
# 저장소 클론
git clone https://github.com/username/injection-calculator.git
cd injection-calculator

# 웹 서버 실행 (Python 예시)
python -m http.server 8000

# 브라우저에서 접속
# http://localhost:8000
```

## 📖 사용 방법

### 1. 파일 준비
- **사출계획 파일**: `06월 5주차 사출계획_250630.xlsx` 형태
- **BOM Tree 파일**: `bom_tree.xlsx` 형태

### 2. 파일 업로드
1. 각각의 업로드 박스에 파일을 드래그하거나 클릭하여 선택
2. 업로드 완료 시 ✅ 표시 확인

### 3. 계산 실행
1. "약품/잉크 종류 계산하기" 버튼 클릭
2. 매칭이 필요한 제품이 있으면 매칭 화면에서 처리

### 4. 결과 확인
- **계산 결과 탭**: 일자별 약품/잉크 종류 및 수량 확인
- **매칭 관리 탭**: 제품 매칭 상태 관리 및 수정

### 5. 다운로드
"잉크 목록 엑셀 다운로드" 버튼으로 결과를 CSV 파일로 저장

## 🏗️ 프로젝트 구조

```
injection-calculator/
├── index.html                    # 메인 HTML 파일
├── README.md                     # 프로젝트 문서
├── css/
│   └── styles.css               # 모든 CSS 스타일
├── js/
│   ├── app.js                   # 메인 애플리케이션
│   ├── state.js                 # 상태 관리
│   ├── fileHandler.js           # 파일 처리
│   ├── calculator.js            # 계산 로직
│   ├── matching.js              # 매칭 시스템
│   ├── ui.js                    # UI 관리
│   └── download.js              # 다운로드 기능
└── assets/
    ├── demo/
    │   ├── sample_injection.xlsx # 샘플 파일
    │   └── sample_bom.xlsx
    └── images/
        └── screenshot.png       # 스크린샷
```

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3, JavaScript (ES6 Modules)
- **Libraries**: 
  - [SheetJS (XLSX)](https://sheetjs.com/) - 엑셀 파일 처리
  - [FileSaver.js](https://github.com/eligrey/FileSaver.js/) - 파일 다운로드
- **Deployment**: GitHub Pages
- **Browser Support**: Chrome, Firefox, Safari, Edge (최신 버전)

## ⚙️ 설정 및 커스터마이징

### 날짜 범위 변경
`js/calculator.js` 파일에서 `extractProductionPlan` 함수의 `dateColumns` 배열을 수정:

```javascript
const dateColumns = [
    { index: 1, date: '2025-06-29' },
    { index: 3, date: '2025-06-29' },
    // ... 추가 날짜
];
```

### 배수 설정 변경
`js/calculator.js` 파일에서 `calculateDailyMaterialTypes` 함수의 배수값 수정:

```javascript
// 약품 배수 (현재: ×3)
results[date].chemicals[cleanChemical] = 
    (results[date].chemicals[cleanChemical] || 0) + 3;

// 잉크 배수 (현재: ×2)
results[date].inks[cleanInk] = 
    (results[date].inks[cleanInk] || 0) + 2;
```

## 🎹 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl + Enter` | 계산 실행 |
| `1-9` | 날짜 탭 전환 |
| `Escape` | 모달/편집 취소 |
| `F5` | 새로고침 (결과 확인) |
| `Ctrl + S` | 매칭 정보 저장 |
| `Ctrl + Shift + D` | 개발 도구 (개발 모드) |

## 🐛 문제해결

### 파일 업로드 오류
- 파일 형식이 `.xlsx` 또는 `.xls`인지 확인
- 파일 크기가 10MB 이하인지 확인
- 브라우저를 새로고침한 후 다시 시도

### 매칭 문제
- "매칭 관리" 탭에서 수동으로 매칭 설정
- 브라우저의 로컬 스토리지가 활성화되어 있는지 확인

### 다운로드 문제
- 팝업 차단이 해제되어 있는지 확인
- 다운로드가 안 되면 모달창에서 수동 복사/붙여넣기 사용

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 개발 노트

### 모듈 시스템
ES6 모듈을 사용하여 코드를 논리적으로 분리했습니다:
- **상태 관리**: 중앙집중식 상태 관리
- **기능별 분리**: 각 기능을 독립적인 모듈로 구성
- **순환 의존성 방지**: 동적 import를 활용한 의존성 관리

### 브라우저 호환성
- **모던 브라우저**: ES6 모듈 네이티브 지원
- **구형 브라우저**: Polyfill 또는 번들러 필요시 추가 가능
- **IE 지원**: 현재 미지원 (필요시 Babel 트랜스파일 가능)

### 성능 최적화
- **지연 로딩**: 필요시에만 모듈 import
- **메모리 관리**: 이벤트 리스너 적절한 정리
- **DOM 최적화**: 배치 업데이트 및 가상 DOM 개념 활용

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👨‍💻 개발자

**Injection Calculator Team**
- 이메일: contact@example.com
- GitHub: [@username](https://github.com/username)

## 📚 추가 자료

- [SheetJS 문서](https://docs.sheetjs.com/)
- [ES6 모듈 가이드](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [GitHub Pages 배포 가이드](https://pages.github.com/)

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

Made with ❤️ for manufacturing efficiency

</div>