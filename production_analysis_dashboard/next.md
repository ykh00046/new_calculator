🥇 1순위: 성능 병목 현상 (계산 vs 렌더링)
가장 큰 성능 저하의 원인은 '계산'이 아니라 **'UI 렌더링'**입니다.

데이터 로딩 (I/O 병목)

현상: app.py는 앱 시작 시 1년 치 전체 데이터(full_data)를 로드한 후, Pandas로 카테고리(잉크, 용수 등)를 필터링합니다. 데이터가 수백만 건이 되면 앱 시작 자체가 매우 느려집니다.

해결: load_production_data가 selected_category를 인자로 받도록 수정하세요. DB 쿼리 자체에 WHERE product_category = ?를 포함시켜, 처음부터 필요한 데이터만 가져오도록 변경해야 합니다.

UI 렌더링 (CPU/메모리 병목)

현상: product_status_tab에서 '전체 제품 보기'를 켜면, 제품 수(예: 500개)만큼 st.container, st.metric, st.expander, 그리고 **st.altair_chart**가 한 번에 생성됩니다. 이는 브라우저를 다운시킬 수 있는 가장 큰 병목점입니다.

해결 (핵심): '전체 보기' 토글을 제거하고 st.pagination 컴포넌트를 도입하세요. 한 페이지에 12~24개의 제품 카드만 렌더링하도록 제한해야 합니다.

벡터화 vs 렌더링

product_cards.py의 for 루프 내 계산(비중, 변화율)을 벡터화로 개선할 수 있습니다.

하지만 이는 렌더링 병목에 비하면 미미한 수준입니다. (2)번의 렌더링 최적화가 99%의 성능 향상을 가져올 것입니다.

🧩 3순위: 앱 구조 및 사용자 경험(UX)
앱의 사용성을 높이고 구조를 명확하게 만듭니다.

기능 중복 및 분산

현상: weekly/monthly/custom 탭에도 'Top 5 제품 차트'가 있고, product_status_tab에도 '제품별 카드', '제품 비교'가 있습니다. 기능이 분산되어 혼란스럽습니다.

권장안: weekly/monthly/custom 탭에서는 제품별 분석을 모두 제거하고, 해당 기간의 전체 카테고리 총량 추이(일별 생산량)와 메트릭에만 집중하게 하세요. 모든 제품 레벨 상세 분석은 product_status_tab에서만 수행하도록 역할을 명확히 분리하는 것이 좋습니다.

하드코딩된 UI

'Top 5' 고정: app.py에서 product_filter_mode = 'top5'로 고정되어 사용자가 변경할 수 없습니다. st.selectbox 등을 추가하여 'Top 5', 'Top 10', '직접 선택' 등을 고를 수 있게 해야 합니다.

카테고리 버튼 고정: '잉크', '용수', '약품' 버튼이 하드코딩되어 있습니다. DB에서 가져온 available_categories 리스트를 기반으로 동적으로 버튼을 생성하도록 변경하는 것이 좋습니다.

차트 X축 문제

현상: create_daily_production_chart가 '11/10 (월)' 같은 문자열(:N)을 X축으로 사용합니다. weekly_tab(7일)에서는 괜찮지만, monthly_tab(30일)이나 custom_tab(90일)에서는 X축 레이블이 겹쳐서 깨집니다.

해결: X축은 항상 실제 date 컬럼을 사용하고 시간 축(:T)으로 인코딩하세요. Altair가 자동으로 간격을 조절해 줄 것입니다.

🧹 4순위: 코드 정리
미사용 함수: summary.py의 display_summary_metrics 함수는 현재 어디에서도 호출되지 않습니다. 혼동을 막기 위해 삭제하는 것이 좋습니다.