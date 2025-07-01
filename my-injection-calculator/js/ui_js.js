/**
 * UI 관리 모듈
 * 결과 표시, 탭 관리, 통계 업데이트 담당
 */

import { AppState } from './state.js';

/**
 * UI 관리자 초기화
 */
export function initializeUI() {
    // 메인 탭 이벤트 리스너
    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            switchMainTab(tabName, e.target);
        });
    });

    console.log('🎨 UI 관리자 초기화 완료');
}

/**
 * 메인 탭 전환
 * @param {string} tabName - 탭 이름
 * @param {Element} tabElement - 탭 엘리먼트
 */
export function switchMainTab(tabName, tabElement) {
    // 탭 버튼 활성화 상태 변경
    document.querySelectorAll('.main-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    tabElement.classList.add('active');

    // 탭 컨텐츠 표시/숨김
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + '-tab').classList.add('active');

    // 상태 업데이트
    AppState.ui.activeTab = tabName;

    // 매칭 관리 탭이 선택된 경우 데이터 업데이트
    if (tabName === 'matching') {
        import('./matching.js').then(matchingModule => {
            matchingModule.updateMatchingTab();
        });
    }

    console.log(`📑 탭 전환: ${tabName}`);
}

/**
 * 결과 섹션 표시
 */
export function showResultsSection() {
    const resultsSection = document.getElementById('results');
    resultsSection.classList.add('show');
    console.log('📊 결과 섹션 표시');
}

/**
 * 계산 결과 표시
 * @param {Object} results - 계산 결과
 */
export function displayResults(results) {
    if (!results) {
        console.warn('⚠️ 표시할 결과가 없습니다');
        return;
    }

    console.log('📊 결과 표시 시작');

    // 날짜 탭 생성
    createDateTabs(results);

    // 주간 요약 표시
    displayWeeklySummary(results);

    // 첫 번째 날짜 데이터 표시
    const dates = Object.keys(results).sort();
    if (dates.length > 0) {
        displayDateData(dates[0]);
        AppState.ui.selectedDate = dates[0];
    }

    console.log('✅ 결과 표시 완료');
}

/**
 * 날짜 탭 생성
 * @param {Object} results - 계산 결과
 */
function createDateTabs(results) {
    const dates = Object.keys(results).sort();
    const dateTabsContainer = document.getElementById('date-tabs');
    dateTabsContainer.innerHTML = '';

    dates.forEach((date, index) => {
        const tab = document.createElement('div');
        tab.className = 'date-tab';
        if (index === 0) {
            tab.classList.add('active');
        }

        const dateObj = new Date(date);
        const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
        const dayName = dayNames[dateObj.getDay()];
        tab.textContent = `${dateObj.getMonth() + 1}/${dateObj.getDate()} (${dayName})`;

        tab.addEventListener('click', () => selectDate(date, tab));
        dateTabsContainer.appendChild(tab);
    });

    console.log(`📅 날짜 탭 생성: ${dates.length}개`);
}

/**
 * 날짜 선택
 * @param {string} date - 선택된 날짜
 * @param {Element} tabElement - 탭 엘리먼트
 */
function selectDate(date, tabElement) {
    AppState.ui.selectedDate = date;

    // 탭 활성화 상태 변경
    document.querySelectorAll('.date-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    tabElement.classList.add('active');

    displayDateData(date);
    console.log(`📅 날짜 선택: ${date}`);
}

/**
 * 특정 날짜 데이터 표시
 * @param {string} date - 날짜
 */
export function displayDateData(date) {
    const data = AppState.data.calculatedResults[date];
    if (!data) {
        console.warn(`⚠️ ${date} 데이터가 없습니다`);
        return;
    }

    // 날짜 제목 업데이트
    updateDateTitle(date);

    // 통계 업데이트
    updateDayStatistics(data);

    // 약품 리스트 표시
    displayChemicalsList(data.chemicals);

    // 잉크 리스트 표시
    displayInksList(data.inks);

    console.log(`📊 ${date} 데이터 표시 완료`);
}

/**
 * 날짜 제목 업데이트
 * @param {string} date - 날짜
 */
function updateDateTitle(date) {
    const dateObj = new Date(date);
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    const dayName = dayNames[dateObj.getDay()];
    
    document.getElementById('selected-date').textContent = 
        `${dateObj.getMonth() + 1}월 ${dateObj.getDate()}일 (${dayName}요일)`;
}

/**
 * 일일 통계 업데이트
 * @param {Object} data - 날짜별 데이터
 */
function updateDayStatistics(data) {
    document.getElementById('day-products').textContent = data.products.length;
    document.getElementById('day-chemicals').textContent = Object.keys(data.chemicals).length;
    document.getElementById('day-inks').textContent = Object.keys(data.inks).length;
}

/**
 * 약품 리스트 표시
 * @param {Object} chemicals - 약품 데이터
 */
function displayChemicalsList(chemicals) {
    const container = document.getElementById('chemicals-list');
    container.innerHTML = '';

    if (Object.keys(chemicals).length === 0) {
        container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">약품이 필요한 제품이 없습니다</div>';
        return;
    }

    // 사용량이 많은 순으로 정렬
    const sortedChemicals = Object.entries(chemicals).sort((a, b) => b[1] - a[1]);

    sortedChemicals.forEach(([chemical, count]) => {
        const tag = document.createElement('div');
        tag.className = 'material-tag';
        tag.innerHTML = `${escapeHtml(chemical)} <span class="material-tag count">${count}</span>`;
        container.appendChild(tag);
    });
}

/**
 * 잉크 리스트 표시
 * @param {Object} inks - 잉크 데이터
 */
function displayInksList(inks) {
    const container = document.getElementById('inks-list');
    container.innerHTML = '';

    if (Object.keys(inks).length === 0) {
        container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">잉크가 필요한 제품이 없습니다</div>';
        return;
    }

    // 사용량이 많은 순으로 정렬
    const sortedInks = Object.entries(inks).sort((a, b) => b[1] - a[1]);

    sortedInks.forEach(([ink, count]) => {
        const tag = document.createElement('div');
        tag.className = 'material-tag';
        tag.innerHTML = `${escapeHtml(ink)} <span class="material-tag count">${count}</span>`;
        container.appendChild(tag);
    });
}

/**
 * 주간 요약 표시
 * @param {Object} results - 전체 결과
 */
function displayWeeklySummary(results) {
    // 주간 전체 통계 계산
    const weeklyChemicals = {};
    const weeklyInks = {};

    Object.keys(results).forEach(date => {
        Object.keys(results[date].chemicals).forEach(chemical => {
            weeklyChemicals[chemical] = (weeklyChemicals[chemical] || 0) + results[date].chemicals[chemical];
        });

        Object.keys(results[date].inks).forEach(ink => {
            weeklyInks[ink] = (weeklyInks[ink] || 0) + results[date].inks[ink];
        });
    });

    // 약품 요약 표시
    displayWeeklyChemicals(weeklyChemicals);

    // 잉크 요약 표시
    displayWeeklyInks(weeklyInks);

    console.log(`📈 주간 요약: 약품 ${Object.keys(weeklyChemicals).length}종, 잉크 ${Object.keys(weeklyInks).length}종`);
}

/**
 * 주간 약품 요약 표시
 * @param {Object} weeklyChemicals - 주간 약품 데이터
 */
function displayWeeklyChemicals(weeklyChemicals) {
    document.getElementById('total-chemicals').textContent = Object.keys(weeklyChemicals).length;
    
    const container = document.getElementById('weekly-chemicals');
    container.innerHTML = '';

    const sortedChemicals = Object.entries(weeklyChemicals).sort((a, b) => b[1] - a[1]);
    
    sortedChemicals.forEach(([chemical, count]) => {
        const tag = document.createElement('div');
        tag.className = 'top-material';
        tag.textContent = `${chemical}: ${count}`;
        container.appendChild(tag);
    });
}

/**
 * 주간 잉크 요약 표시
 * @param {Object} weeklyInks - 주간 잉크 데이터
 */
function displayWeeklyInks(weeklyInks) {
    document.getElementById('total-inks').textContent = Object.keys(weeklyInks).length;
    
    const container = document.getElementById('weekly-inks');
    container.innerHTML = '';

    // 상위 잉크들만 표시 (최대 20개)
    const sortedInks = Object.entries(weeklyInks).sort((a, b) => b[1] - a[1]).slice(0, 20);
    
    sortedInks.forEach(([ink, count]) => {
        const tag = document.createElement('div');
        tag.className = 'top-material';
        tag.textContent = `${ink}: ${count}`;
        container.appendChild(tag);
    });

    // 더 많은 잉크가 있다면 표시
    if (Object.keys(weeklyInks).length > 20) {
        const moreTag = document.createElement('div');
        moreTag.className = 'top-material';
        moreTag.style.fontStyle = 'italic';
        moreTag.textContent = `...외 ${Object.keys(weeklyInks).length - 20}종`;
        container.appendChild(moreTag);
    }
}

/**
 * 로딩 상태 표시
 * @param {string} message - 로딩 메시지
 */
export function showLoading(message = '처리 중...') {
    const button = document.getElementById('calculate-btn');
    if (button) {
        button.textContent = `⏳ ${message}`;
        button.disabled = true;
    }
}

/**
 * 로딩 상태 숨김
 * @param {string} message - 완료 메시지
 */
export function hideLoading(message = '완료') {
    const button = document.getElementById('calculate-btn');
    if (button) {
        button.textContent = `✅ ${message}`;
        button.disabled = false;
    }
}

/**
 * 성공 알림 표시
 * @param {string} message - 메시지
 */
export function showSuccess(message) {
    // 간단한 알림 (나중에 toast 알림으로 개선 가능)
    alert(`✅ ${message}`);
    console.log(`✅ ${message}`);
}

/**
 * 오류 알림 표시
 * @param {string} message - 오류 메시지
 */
export function showError(message) {
    alert(`❌ ${message}`);
    console.error(`❌ ${message}`);
}

/**
 * 경고 알림 표시
 * @param {string} message - 경고 메시지
 */
export function showWarning(message) {
    alert(`⚠️ ${message}`);
    console.warn(`⚠️ ${message}`);
}

/**
 * 확인 대화상자 표시
 * @param {string} message - 메시지
 * @returns {boolean} 사용자 선택
 */
export function showConfirm(message) {
    return confirm(`❓ ${message}`);
}

/**
 * 모달 표시 (범용)
 * @param {string} title - 제목
 * @param {string} content - 내용
 * @param {Array} buttons - 버튼 설정
 */
export function showModal(title, content, buttons = []) {
    // 기존 모달 제거
    const existingModal = document.getElementById('app-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // 버튼 HTML 생성
    const buttonsHTML = buttons.map(btn => 
        `<button onclick="${btn.onclick}" style="
            background: ${btn.color || '#007bff'}; color: white; border: none;
            padding: 10px 20px; border-radius: 5px; cursor: pointer;
            margin-right: 10px; font-weight: bold;
        ">${btn.text}</button>`
    ).join('');

    // 모달 HTML
    const modalHTML = `
        <div id="app-modal" style="
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 10000;
            display: flex; align-items: center; justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        ">
            <div style="
                background: white; padding: 30px; border-radius: 15px;
                max-width: 90%; max-height: 90%; overflow: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <h3 style="margin: 0 0 20px 0; color: #333;">${escapeHtml(title)}</h3>
                <div style="margin-bottom: 20px; line-height: 1.5;">${content}</div>
                <div style="text-align: center;">
                    ${buttonsHTML}
                    ${buttons.length === 0 ? '<button onclick="document.getElementById(\'app-modal\').remove()" style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">닫기</button>' : ''}
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * 모달 닫기
 */
export function closeModal() {
    const modal = document.getElementById('app-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * HTML 이스케이프 처리
 * @param {string} text - 텍스트
 * @returns {string} 이스케이프된 텍스트
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * UI 상태 정보 (디버깅용)
 * @returns {Object} UI 상태
 */
export function getUIState() {
    return {
        activeTab: AppState.ui.activeTab,
        selectedDate: AppState.ui.selectedDate,
        resultsVisible: document.getElementById('results').classList.contains('show'),
        matchingVisible: document.getElementById('matching-section').classList.contains('show'),
        warningVisible: document.getElementById('warning-section').classList.contains('show')
    };
}

/**
 * 반응형 UI 조정 (화면 크기 변경 시)
 */
export function adjustResponsiveUI() {
    // 모바일에서 날짜 탭 스크롤 조정
    const dateTabs = document.getElementById('date-tabs');
    if (dateTabs && window.innerWidth <= 768) {
        dateTabs.style.justifyContent = 'flex-start';
        dateTabs.style.overflowX = 'auto';
    }
    
    // 통계 그리드 조정
    const summaryStats = document.querySelector('.summary-stats');
    if (summaryStats && window.innerWidth <= 480) {
        summaryStats.style.gridTemplateColumns = '1fr';
    }
    
    console.log('📱 반응형 UI 조정 완료');
}

/**
 * 키보드 단축키 처리
 * @param {KeyboardEvent} event - 키보드 이벤트
 */
export function handleKeyboardShortcuts(event) {
    // Ctrl + Enter: 계산 실행
    if (event.ctrlKey && event.key === 'Enter') {
        const calculateBtn = document.getElementById('calculate-btn');
        if (calculateBtn && !calculateBtn.disabled) {
            calculateBtn.click();
        }
        event.preventDefault();
    }
    
    // Escape: 모달/편집 닫기
    if (event.key === 'Escape') {
        closeModal();
        
        // 매칭 편집 중이면 취소
        const searchSection = document.getElementById('search-section');
        if (searchSection && searchSection.style.display !== 'none') {
            import('./matching.js').then(matchingModule => {
                // cancelEdit() 함수는 private이므로 버튼 클릭으로 처리
                document.getElementById('cancel-edit').click();
            });
        }
    }
    
    // 숫자 키: 날짜 탭 전환 (1-9)
    if (event.key >= '1' && event.key <= '9' && !event.ctrlKey && !event.altKey) {
        const dateIndex = parseInt(event.key) - 1;
        const dateTabs = document.querySelectorAll('.date-tab');
        if (dateTabs[dateIndex]) {
            dateTabs[dateIndex].click();
        }
    }
}

/**
 * 스크롤 위치에 따른 헤더 스타일 조정
 */
export function handleScroll() {
    const header = document.querySelector('.header');
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    if (scrollTop > 100) {
        header.style.transform = 'translateY(-10px)';
        header.style.boxShadow = '0 5px 20px rgba(0,0,0,0.1)';
    } else {
        header.style.transform = 'translateY(0)';
        header.style.boxShadow = 'none';
    }
}

/**
 * 애니메이션 효과 추가
 * @param {Element} element - 대상 엘리먼트
 * @param {string} animationType - 애니메이션 타입
 */
export function addAnimation(element, animationType = 'fadeIn') {
    if (!element) return;
    
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    element.style.transition = 'all 0.3s ease';
    
    // 다음 프레임에서 애니메이션 시작
    requestAnimationFrame(() => {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    });
}

/**
 * 테이블 정렬 기능
 * @param {string} tableId - 테이블 ID
 * @param {number} columnIndex - 정렬할 컬럼 인덱스
 * @param {string} sortType - 정렬 타입 ('text', 'number', 'date')
 */
export function sortTable(tableId, columnIndex, sortType = 'text') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // 현재 정렬 방향 확인
    const isAscending = !table.dataset.sortDirection || table.dataset.sortDirection === 'desc';
    table.dataset.sortDirection = isAscending ? 'asc' : 'desc';
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        let comparison = 0;
        
        switch (sortType) {
            case 'number':
                comparison = parseFloat(aVal) - parseFloat(bVal);
                break;
            case 'date':
                comparison = new Date(aVal) - new Date(bVal);
                break;
            default:
                comparison = aVal.localeCompare(bVal);
        }
        
        return isAscending ? comparison : -comparison;
    });
    
    // 정렬된 행들을 다시 추가
    rows.forEach(row => tbody.appendChild(row));
    
    console.log(`📊 테이블 정렬: ${tableId}, 컬럼 ${columnIndex}, ${isAscending ? '오름차순' : '내림차순'}`);
}

/**
 * 검색 하이라이트 기능
 * @param {string} containerId - 컨테이너 ID
 * @param {string} searchTerm - 검색어
 */
export function highlightSearch(containerId, searchTerm) {
    const container = document.getElementById(containerId);
    if (!container || !searchTerm) return;
    
    // 기존 하이라이트 제거
    removeHighlight(containerId);
    
    const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi');
    
    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const textNodes = [];
    let node;
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }
    
    textNodes.forEach(textNode => {
        if (regex.test(textNode.textContent)) {
            const highlightedHTML = textNode.textContent.replace(regex, '<mark>$1</mark>');
            const wrapper = document.createElement('span');
            wrapper.innerHTML = highlightedHTML;
            textNode.parentNode.replaceChild(wrapper, textNode);
        }
    });
}

/**
 * 검색 하이라이트 제거
 * @param {string} containerId - 컨테이너 ID
 */
function removeHighlight(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const marks = container.querySelectorAll('mark');
    marks.forEach(mark => {
        mark.outerHTML = mark.innerHTML;
    });
}

/**
 * 정규식 이스케이프
 * @param {string} string - 문자열
 * @returns {string} 이스케이프된 문자열
 */
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\/**
 * 반응형 UI 조정 (화면 크기 변경 시)
 */
export function adjustResponsiveUI() {
    // 모바일에서');
}

/**
 * 툴팁 표시
 * @param {Element} element - 대상 엘리먼트
 * @param {string} text - 툴팁 텍스트
 * @param {string} position - 위치 ('top', 'bottom', 'left', 'right')
 */
export function showTooltip(element, text, position = 'top') {
    if (!element) return;
    
    // 기존 툴팁 제거
    hideTooltip();
    
    const tooltip = document.createElement('div');
    tooltip.id = 'app-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 10001;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s ease;
    `;
    
    document.body.appendChild(tooltip);
    
    // 위치 계산
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left, top;
    
    switch (position) {
        case 'bottom':
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.bottom + 5;
            break;
        case 'left':
            left = rect.left - tooltipRect.width - 5;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
        case 'right':
            left = rect.right + 5;
            top = rect.top + (rect.height - tooltipRect.height) / 2;
            break;
        default: // top
            left = rect.left + (rect.width - tooltipRect.width) / 2;
            top = rect.top - tooltipRect.height - 5;
    }
    
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    
    // 애니메이션 표시
    requestAnimationFrame(() => {
        tooltip.style.opacity = '1';
    });
}

/**
 * 툴팁 숨김
 */
export function hideTooltip() {
    const tooltip = document.getElementById('app-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * 프로그레스 바 표시
 * @param {number} progress - 진행률 (0-100)
 * @param {string} message - 메시지
 */
export function showProgress(progress, message = '') {
    let progressBar = document.getElementById('app-progress');
    
    if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.id = 'app-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: rgba(102, 126, 234, 0.2);
            z-index: 10002;
        `;
        
        const progressFill = document.createElement('div');
        progressFill.id = 'app-progress-fill';
        progressFill.style.cssText = `
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            width: 0%;
        `;
        
        progressBar.appendChild(progressFill);
        document.body.appendChild(progressBar);
    }
    
    const fill = document.getElementById('app-progress-fill');
    if (fill) {
        fill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
    }
    
    if (message) {
        console.log(`📊 진행률: ${progress}% - ${message}`);
    }
}

/**
 * 프로그레스 바 숨김
 */
export function hideProgress() {
    const progressBar = document.getElementById('app-progress');
    if (progressBar) {
        progressBar.remove();
    }
}

/**
 * 인쇄 최적화
 */
export function optimizeForPrint() {
    // 인쇄 스타일 추가
    const printStyle = document.createElement('style');
    printStyle.textContent = `
        @media print {
            .header { page-break-inside: avoid; }
            .upload-section { display: none; }
            .main-tabs { display: none; }
            .controls-row { display: none; }
            .material-tag { break-inside: avoid; }
            .weekly-summary { page-break-before: always; }
        }
    `;
    document.head.appendChild(printStyle);
    
    console.log('🖨️ 인쇄 최적화 적용');
}

/**
 * UI 이벤트 리스너 등록
 */
export function registerUIEventListeners() {
    // 창 크기 변경 시 반응형 조정
    window.addEventListener('resize', adjustResponsiveUI);
    
    // 키보드 단축키
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 스크롤 이벤트
    window.addEventListener('scroll', handleScroll);
    
    // 툴팁 이벤트 (data-tooltip 속성이 있는 엘리먼트)
    document.addEventListener('mouseenter', (e) => {
        if (e.target.dataset.tooltip) {
            showTooltip(e.target, e.target.dataset.tooltip);
        }
    }, true);
    
    document.addEventListener('mouseleave', (e) => {
        if (e.target.dataset.tooltip) {
            hideTooltip();
        }
    }, true);
    
    console.log('🎮 UI 이벤트 리스너 등록 완료');
}