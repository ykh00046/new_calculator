# Excel Exporter 개선 사항

**작업 일자**: 2025-11-17
**파일**: `models/excel_exporter.py`

---

## 📋 개선 내용 요약

`.venv\models\excel_exporter.py`의 고급 기능을 현재 프로젝트에 통합하여 엑셀 출력 품질을 대폭 향상시켰습니다.

---

## ✨ 추가된 기능

### 1. 이미지 위치 및 크기 조정
**변경 전**:
```python
ws.add_image(img, 'A1')  # A1 셀에 원본 크기로 삽입
```

**변경 후**:
```python
img.width = 233   # 픽셀 단위
img.height = 71   # 픽셀 단위
img.anchor = 'G2'  # G2 셀에 앵커 설정
ws.add_image(img)
```

**효과**:
- 서명 이미지가 G2 셀에 정확하게 배치
- 이미지 크기가 셀에 맞게 자동 조정

### 2. 셀 병합 기능
**새로운 메서드**: `_apply_cell_merges()`

```python
# 제품LOT 세로 병합 (A6:A끝행)
ws.merge_cells(f'A6:A{data_end_row}')
# 배합량 세로 병합 (B6:B끝행)
ws.merge_cells(f'B6:B{data_end_row}')

# 중앙 정렬 적용
lot_cell.alignment = Alignment(horizontal='center', vertical='center')
amount_cell.alignment = Alignment(horizontal='center', vertical='center')
```

**효과**:
- 제품LOT와 배합량이 세로로 병합되어 깔끔한 표 형식
- 자동 중앙 정렬로 가독성 향상

### 3. 테이블 경계선 자동 적용
**새로운 메서드**: `_apply_borders()`

```python
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# 헤더 및 데이터 행에 테두리 적용
for row in range(5, data_end_row + 1):
    for col in range(1, 8):  # A~G 컬럼
        cell = ws.cell(row=row, column=col)
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')
```

**효과**:
- 전문적인 표 형식의 테두리
- 모든 셀 자동 중앙 정렬

### 4. 빈 행 자동 삭제
**새로운 메서드**: `_delete_empty_rows()`

```python
for row_num in range(original_max_row, data_end_row, -1):
    is_empty = True
    for col in range(1, 8):  # A~G 컬럼 확인
        cell_value = ws.cell(row=row_num, column=col).value
        if cell_value is not None and str(cell_value).strip() != '':
            is_empty = False
            break

    if is_empty:
        ws.delete_rows(row_num, 1)
```

**효과**:
- 템플릿의 불필요한 빈 행 자동 제거
- 파일 크기 최적화

### 5. 워크시트 정리
**새로운 메서드**: `_clean_worksheet()`

```python
for row in range(data_end_row + 1, max_check_row + 1):
    for col in range(1, 8):  # A~G 컬럼
        cell = ws.cell(row=row, column=col)
        if cell.value is not None:
            cell.value = None

ws.calculate_dimension()
```

**효과**:
- 데이터 범위 외부의 불필요한 셀 값 제거
- 워크시트 크기 최적화

---

## 🔧 코드 변경 사항

### import 추가
```python
from openpyxl.styles import Border, Side, Alignment
```

### export_to_excel 메서드 개선
```python
def export_to_excel(self, data, include_image=False, image_path=None):
    # ... 기존 코드 ...

    # 데이터 끝 행 계산
    data_end_row = start_row + len(data.get('materials', [])) - 1

    # 이미지 삽입 (크기 및 위치 조정)
    if include_image and image_path and os.path.exists(image_path):
        img = OpenpyxlImage(image_path)
        img.width = 233
        img.height = 71
        img.anchor = 'G2'
        ws.add_image(img)

    # 워크시트 서식 적용
    self._clean_worksheet(ws, data_end_row)
    self._delete_empty_rows(ws, data_end_row)
    self._apply_cell_merges(ws, data_end_row)
    self._apply_borders(ws, data_end_row)

    # 파일 저장
    wb.save(output_file)
    wb.close()  # 명시적 종료 추가
```

### 새로운 private 메서드 4개 추가
1. `_clean_worksheet(ws, data_end_row)` - 워크시트 정리
2. `_delete_empty_rows(ws, data_end_row)` - 빈 행 삭제
3. `_apply_cell_merges(ws, data_end_row)` - 셀 병합
4. `_apply_borders(ws, data_end_row)` - 테두리 적용

---

## 📊 개선 효과

### Before vs After

| 항목 | Before | After |
|------|--------|-------|
| 이미지 위치 | A1 (고정) | G2 (조정 가능) |
| 이미지 크기 | 원본 크기 | 233x71 픽셀 (최적화) |
| 셀 병합 | 없음 | 제품LOT, 배합량 병합 |
| 테두리 | 템플릿 의존 | 자동 적용 |
| 빈 행 | 템플릿 그대로 | 자동 삭제 |
| 셀 정렬 | 템플릿 의존 | 자동 중앙 정렬 |
| 파일 크기 | ~25KB | ~6.5KB (최적화) |

### 테스트 결과
```
엑셀 파일: TEST25111701.xlsx (6.5KB)
PDF 파일: TEST25111701.pdf (69.7KB)

로그:
✓ 워크시트 정리 완료
✓ 빈 행 삭제 완료
✓ 셀 병합 완료
✓ 테이블 경계선 적용 완료
✓ 엑셀 파일 생성 완료
✓ PDF 파일 생성 완료
```

---

## 🎯 주요 이점

### 1. 전문성 향상
- 깔끔한 표 형식
- 일관된 서식
- 보기 좋은 레이아웃

### 2. 유지보수 용이
- 템플릿 변경 시에도 자동으로 서식 적용
- 빈 행/셀 자동 정리

### 3. 파일 크기 최적화
- 불필요한 데이터 제거
- 약 75% 크기 감소 (25KB → 6.5KB)

### 4. 사용자 경험 개선
- 더 빠른 파일 로딩
- 깔끔한 출력물
- 인쇄 시 최적화된 레이아웃

---

## 📝 사용 예제

```python
from models.excel_exporter import ExcelExporter

exporter = ExcelExporter()

# 데이터 준비
data = {
    'product_lot': 'APB25111701',
    'worker': '김민호',
    'work_date': '2025-11-17',
    'work_time': '10:00:00',
    'scale': 'M-65',
    'total_amount': 100.0,
    'materials': [
        {'material_name': 'PB', 'material_lot': 'LOT001',
         'ratio': 100.0, 'theory_amount': 100.0, 'actual_amount': 100.0},
        # ... more materials
    ]
}

# 엑셀 파일 생성 (서식 자동 적용)
excel_file = exporter.export_to_excel(data, include_image=True, image_path='signature.png')

# PDF 변환
pdf_file = exporter.export_to_pdf(excel_file)
```

---

## 🔄 호환성

### 기존 코드와의 호환성
✅ 100% 호환

기존 코드를 수정할 필요 없이 자동으로 개선된 기능 적용:
- 기존 `export_to_excel()` 호출은 그대로 작동
- 추가 매개변수 불필요
- 기존 설정 (config.json) 그대로 사용

### 의존성
변경 사항 없음:
```python
openpyxl          # 기존 의존성
openpyxl.styles   # 이미 포함되어 있음
```

---

## 📌 향후 개선 가능 사항

### 단기
- [ ] 이미지 위치를 config.json에서 설정 가능하게
- [ ] 셀 병합 범위를 config.json에서 지정
- [ ] 테두리 스타일 옵션 추가

### 중기
- [ ] 여러 이미지 삽입 지원
- [ ] 조건부 서식 지원
- [ ] 차트 자동 생성

### 장기
- [ ] 템플릿 자동 생성 기능
- [ ] 다양한 레이아웃 지원
- [ ] Excel 매크로 통합

---

## ✅ 체크리스트

**반영 완료**:
- [x] Border, Side, Alignment import 추가
- [x] 이미지 크기 조정 로직 추가
- [x] G2 셀 앵커 설정
- [x] _clean_worksheet 메서드 추가
- [x] _delete_empty_rows 메서드 추가
- [x] _apply_cell_merges 메서드 추가
- [x] _apply_borders 메서드 추가
- [x] export_to_excel에 서식 적용 로직 통합
- [x] wb.close() 명시적 호출 추가
- [x] 테스트 완료

**검증 완료**:
- [x] 엑셀 파일 생성 확인
- [x] PDF 변환 확인
- [x] 파일 크기 최적화 확인
- [x] 로그 메시지 확인

---

**작성일**: 2025-11-17 10:10
**상태**: ✅ 완료 및 테스트 통과
