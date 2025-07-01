/**
 * 매칭 시스템 모듈
 * 자동/수동 매칭, 매칭 관리 탭, 검색 기능 담당
 */

import { AppState, saveMatches } from './state.js';
import { findSimilarProducts, recalculateResults } from './calculator.js';

/**
 * 매칭 시스템 초기화
 */
export function initializeMatching() {
    // 매칭 관련 이벤트 리스너 등록
    document.getElementById('skip-all-btn').addEventListener('click', skipAllMatches);
    document.getElementById('save-matches-btn').addEventListener('click', saveMatchesAndContinue);
    document.getElementById('refresh-matching').addEventListener('click', refreshMatching);
    document.getElementById('cancel-edit').addEventListener('click', cancelEdit);
    document.getElementById('clear-matching').addEventListener('click', clearMatching);
    
    console.log('🔗 매칭 시스템 초기화 완료');
}

/**
 * 매칭 인터페이스 표시
 * @param {Array} unmatchedList - 매칭되지 않은 제품 목록
 * @param {Array} bomJsonData - BOM 데이터
 */
export function showMatchingInterface(unmatchedList, bomJsonData) {
    AppState.matching.currentMatchingProducts = unmatchedList;
    AppState.matching.matchingIndex = 0;
    AppState.matching.pendingMatches = {};

    console.log(`🔗 매칭 인터페이스 시작: ${unmatchedList.length}개 제품`);

    // UI 표시/숨김
    document.getElementById('warning-section').classList.remove('show');
    document.getElementById('matching-section').classList.add('show');

    displayCurrentMatching(bomJsonData);
}

/**
 * 현재 매칭 화면 표시
 * @param {Array} bomJsonData - BOM 데이터
 */
function displayCurrentMatching(bomJsonData) {
    const { currentMatchingProducts, matchingIndex } = AppState.matching;

    if (matchingIndex >= currentMatchingProducts.length) {
        // 모든 매칭 완료
        document.getElementById('matching-section').classList.remove('show');
        saveMatchesAndContinue();
        return;
    }

    const product = currentMatchingProducts[matchingIndex];
    const suggestions = findSimilarProducts(product, bomJsonData);

    // 진행상황 업데이트
    document.getElementById('progress-info').textContent = 
        `진행상황: ${matchingIndex + 1} / ${currentMatchingProducts.length}`;

    // 매칭 컨테이너 업데이트
    const container = document.getElementById('matching-container');
    container.innerHTML = createMatchingHTML(product, suggestions, matchingIndex);

    // 제안 버튼 이벤트 추가
    addSuggestionEventListeners(container, product);
}

/**
 * 매칭 HTML 생성
 * @param {string} product - 제품명
 * @param {Array} suggestions - 제안 목록
 * @param {number} index - 인덱스
 * @returns {string} HTML 문자열
 */
function createMatchingHTML(product, suggestions, index) {
    return `
        <div class="matching-item">
            <div class="product-name">📦 ${product}</div>
            <div>유사한 BOM 제품을 선택하거나 건너뛰세요:</div>
            <div class="suggestions" id="suggestions-${index}">
                ${suggestions.map((sug, idx) => 
                    `<div class="suggestion-btn" data-product="${escapeHtml(sug.product)}" data-index="${idx}">
                        ${escapeHtml(sug.product)} (${Math.round(sug.similarity * 100)}%)
                    </div>`
                ).join('')}
            </div>
            <div class="match-controls" style="margin-top: 10px;">
                <button class="skip-btn" onclick="window.matchingModule.skipCurrentMatch()">건너뛰기</button>
                <button class="confirm-btn" onclick="window.matchingModule.confirmCurrentMatch()" id="confirm-current" disabled>선택 확인</button>
            </div>
        </div>
    `;
}

/**
 * 제안 버튼 이벤트 리스너 추가
 * @param {Element} container - 컨테이너 엘리먼트
 * @param {string} product - 제품명
 */
function addSuggestionEventListeners(container, product) {
    container.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 선택 상태 업데이트
            container.querySelectorAll('.suggestion-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            
            // 확인 버튼 활성화
            document.getElementById('confirm-current').disabled = false;
            
            // 임시 매칭 저장
            AppState.matching.pendingMatches[product] = this.dataset.product;
        });
    });
}

/**
 * 현재 매칭 건너뛰기
 */
export function skipCurrentMatch() {
    AppState.matching.matchingIndex++;
    displayCurrentMatching(AppState.data.bomJsonData);
}

/**
 * 현재 매칭 확인
 */
export function confirmCurrentMatch() {
    const { currentMatchingProducts, matchingIndex, pendingMatches } = AppState.matching;
    const product = currentMatchingProducts[matchingIndex];
    
    if (pendingMatches[product]) {
        AppState.matching.productMatches[product] = pendingMatches[product];
        saveMatches();
        console.log(`✅ 매칭 확인: ${product} → ${pendingMatches[product]}`);
    }
    
    AppState.matching.matchingIndex++;
    displayCurrentMatching(AppState.data.bomJsonData);
}

/**
 * 모든 매칭 건너뛰기
 */
function skipAllMatches() {
    console.log('⏭️ 모든 매칭 건너뛰기');
    
    document.getElementById('matching-section').classList.remove('show');
    
    // 매칭되지 않은 제품들을 경고창에 표시
    displayUnmatchedProducts(AppState.matching.currentMatchingProducts);
    
    // 매칭된 제품들로만 계산 진행
    proceedWithMatched();
}

/**
 * 매칭 저장하고 계속
 */
function saveMatchesAndContinue() {
    console.log('💾 매칭 저장하고 계속');
    
    saveMatches();
    document.getElementById('matching-section').classList.remove('show');
    
    // 매칭 결과 적용하여 계산 진행
    proceedWithMatched();
}

/**
 * 매칭된 제품들로 계산 진행
 */
function proceedWithMatched() {
    try {
        // calculator.js의 proceedWithCalculation 호출
        const injectionSheet = AppState.files.injection.Sheets[AppState.files.injection.SheetNames[0]];
        const injectionJsonData = XLSX.utils.sheet_to_json(injectionSheet, { header: 1 });

        // 동적 import 사용하여 순환 의존성 방지
        import('./calculator.js').then(calculatorModule => {
            const { createBOMMapWithValidation, applyMatchingStrategies, proceedWithCalculation } = calculatorModule;
            
            const { bomMap } = createBOMMapWithValidation(AppState.data.bomJsonData, injectionJsonData);
            const { finalBomMap } = applyMatchingStrategies(bomMap, AppState.data.bomJsonData, AppState.matching.unmatchedProducts);
            
            const result = proceedWithCalculation(finalBomMap, injectionJsonData);
            
            if (result.success) {
                // UI 모듈에서 결과 표시
                import('./ui.js').then(uiModule => {
                    uiModule.displayResults(result.results);
                    uiModule.showResultsSection();
                    updateMatchingTab();
                });
            }
        });

    } catch (error) {
        console.error('❌ 매칭 후 계산 오류:', error);
        alert(`계산 오류: ${error.message}`);
    }
}

/**
 * 매칭 관리 탭 업데이트
 */
export function updateMatchingTab() {
    if (AppState.data.allInjectionProducts.length === 0) {
        document.getElementById('matching-table-body').innerHTML = 
            '<tr><td colspan="5" style="text-align: center; color: #666; padding: 30px;">계산을 먼저 실행해주세요.</td></tr>';
        return;
    }

    const tableBody = document.getElementById('matching-table-body');
    tableBody.innerHTML = '';

    let matchedCount = 0;
    let unmatchedCount = 0;

    AppState.data.allInjectionProducts.forEach(product => {
        const row = document.createElement('tr');
        
        let matchedBomProduct = null;
        let materials = { chemical: '', inks: [] };

        // 매칭 정보 확인
        if (AppState.matching.productMatches[product]) {
            matchedBomProduct = AppState.matching.productMatches[product];
            const bomItem = AppState.data.bomJsonData.find(item => item['판매명'] === matchedBomProduct);
            if (bomItem) {
                materials = extractMaterials(bomItem);
                matchedCount++;
            }
        } else {
            // 직접 매칭 확인
            const bomItem = AppState.data.bomJsonData.find(item => item['판매명'] === product);
            if (bomItem) {
                matchedBomProduct = product;
                materials = extractMaterials(bomItem);
                matchedCount++;
            } else {
                unmatchedCount++;
            }
        }

        row.innerHTML = createMatchingTableRowHTML(product, matchedBomProduct, materials);
        tableBody.appendChild(row);
    });

    // 통계 업데이트
    document.getElementById('matched-count').textContent = matchedCount;
    document.getElementById('unmatched-count').textContent = unmatchedCount;

    console.log(`📊 매칭 탭 업데이트: 매칭 ${matchedCount}개, 미매칭 ${unmatchedCount}개`);
}

/**
 * 재료 정보 추출
 * @param {Object} bomItem - BOM 아이템
 * @returns {Object} 재료 정보
 */
function extractMaterials(bomItem) {
    const materials = { chemical: '', inks: [] };
    
    materials.chemical = bomItem['약품명'] || '';
    
    for (let i = 1; i <= 3; i++) {
        const ink = bomItem[`잉크명${i}`];
        if (ink && ink.trim()) {
            materials.inks.push(ink.trim());
        }
    }
    
    return materials;
}

/**
 * 매칭 테이블 행 HTML 생성
 * @param {string} product - 제품명
 * @param {string} matchedBomProduct - 매칭된 BOM 제품
 * @param {Object} materials - 재료 정보
 * @returns {string} HTML 문자열
 */
function createMatchingTableRowHTML(product, matchedBomProduct, materials) {
    return `
        <td class="product-name-col">${escapeHtml(product)}</td>
        <td class="matched-product-col">
            ${matchedBomProduct ? escapeHtml(matchedBomProduct) : '<span style="color: #dc3545;">매칭안됨</span>'}
        </td>
        <td class="materials-col">
            ${materials.chemical ? 
                `<div class="material-chip chemical">${escapeHtml(materials.chemical)}</div>` : 
                '<span style="color: #999;">-</span>'
            }
        </td>
        <td class="materials-col">
            <div class="material-chips">
                ${materials.inks.length > 0 ? 
                    materials.inks.map(ink => `<div class="material-chip ink">${escapeHtml(ink)}</div>`).join('') :
                    '<span style="color: #999;">-</span>'
                }
            </div>
        </td>
        <td class="action-col">
            <button class="edit-btn ${matchedBomProduct ? '' : 'unmatched'}" 
                    onclick="window.matchingModule.editMatching('${escapeForAttribute(product)}')">
                ${matchedBomProduct ? '수정' : '설정'}
            </button>
        </td>
    `;
}

/**
 * 매칭 편집 시작
 * @param {string} productName - 제품명
 */
export function editMatching(productName) {
    AppState.matching.currentEditingProduct = productName;
    
    console.log(`✏️ 매칭 편집 시작: ${productName}`);
    
    // UI 업데이트
    document.getElementById('editing-product').textContent = productName;
    document.getElementById('search-section').style.display = 'block';
    document.getElementById('bom-search').value = '';
    document.getElementById('search-results').innerHTML = '';
    
    // 검색 이벤트 리스너 추가
    const searchInput = document.getElementById('bom-search');
    searchInput.removeEventListener('input', handleBomSearch);
    searchInput.addEventListener('input', handleBomSearch);
    
    searchInput.focus();
}

/**
 * BOM 검색 처리
 * @param {Event} event - 입력 이벤트
 */
function handleBomSearch(event) {
    const query = event.target.value.toLowerCase().trim();
    const resultsContainer = document.getElementById('search-results');

    if (query.length < 2) {
        resultsContainer.innerHTML = '';
        return;
    }

    // BOM 데이터에서 검색
    const results = AppState.data.bomJsonData.filter(item => {
        const productName = item['판매명'];
        return productName && productName.toLowerCase().includes(query);
    }).slice(0, 10);

    resultsContainer.innerHTML = '';

    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="search-result-item" style="color: #999;">검색 결과가 없습니다.</div>';
        return;
    }

    // 검색 결과 표시
    results.forEach(item => {
        const div = document.createElement('div');
        div.className = 'search-result-item';
        
        const materials = extractMaterials(item);
        
        div.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 5px;">${escapeHtml(item['판매명'])}</div>
            <div style="font-size: 0.8rem; color: #666;">
                약품: ${materials.chemical || '없음'} | 
                잉크: ${materials.inks.length > 0 ? materials.inks.join(', ') : '없음'}
            </div>
        `;

        div.addEventListener('click', () => {
            selectBomProduct(item['판매명']);
        });

        resultsContainer.appendChild(div);
    });
}

/**
 * BOM 제품 선택
 * @param {string} bomProductName - 선택된 BOM 제품명
 */
export function selectBomProduct(bomProductName) {
    if (!AppState.matching.currentEditingProduct) {
        console.warn('⚠️ 편집 중인 제품이 없습니다');
        return;
    }

    // 매칭 저장
    AppState.matching.productMatches[AppState.matching.currentEditingProduct] = bomProductName;
    saveMatches();
    
    console.log(`✅ 매칭 저장: ${AppState.matching.currentEditingProduct} → ${bomProductName}`);
    
    // UI 업데이트
    updateMatchingTab();
    cancelEdit();
    
    // 계산 결과 업데이트
    if (AppState.data.calculatedResults) {
        try {
            const newResults = recalculateResults();
            if (newResults) {
                import('./ui.js').then(uiModule => {
                    uiModule.displayResults(newResults);
                });
            }
        } catch (error) {
            console.warn('⚠️ 재계산 실패:', error);
        }
    }

    alert(`✅ "${AppState.matching.currentEditingProduct}"이(가) "${bomProductName}"과(와) 매칭되었습니다.`);
}

/**
 * 편집 취소
 */
function cancelEdit() {
    AppState.matching.currentEditingProduct = null;
    document.getElementById('search-section').style.display = 'none';
    console.log('❌ 매칭 편집 취소');
}

/**
 * 매칭 해제
 */
function clearMatching() {
    if (!AppState.matching.currentEditingProduct) {
        console.warn('⚠️ 편집 중인 제품이 없습니다');
        return;
    }

    const productName = AppState.matching.currentEditingProduct;
    
    if (AppState.matching.productMatches[productName]) {
        delete AppState.matching.productMatches[productName];
        saveMatches();
        updateMatchingTab();
        cancelEdit();
        
        // 계산 결과 업데이트
        if (AppState.data.calculatedResults) {
            try {
                const newResults = recalculateResults();
                if (newResults) {
                    import('./ui.js').then(uiModule => {
                        uiModule.displayResults(newResults);
                    });
                }
            } catch (error) {
                console.warn('⚠️ 재계산 실패:', error);
            }
        }

        console.log(`🗑️ 매칭 해제: ${productName}`);
        alert(`✅ "${productName}"의 매칭이 해제되었습니다.`);
    } else {
        alert('해제할 매칭이 없습니다.');
    }
}

/**
 * 매칭 새로고침
 */
function refreshMatching() {
    updateMatchingTab();
    console.log('🔄 매칭 정보 새로고침');
    alert('매칭 정보가 새로고침되었습니다.');
}

/**
 * 매칭되지 않은 제품들을 경고창에 표시
 * @param {Array} unmatchedList - 미매칭 제품 목록
 */
function displayUnmatchedProducts(unmatchedList) {
    const warningSection = document.getElementById('warning-section');
    const unmatchedListContainer = document.getElementById('unmatched-list');
    
    unmatchedListContainer.innerHTML = '';
    unmatchedList.forEach((product, index) => {
        const item = document.createElement('div');
        item.className = 'unmatched-item';
        item.textContent = `${index + 1}. ${product}`;
        unmatchedListContainer.appendChild(item);
    });
    
    warningSection.classList.add('show');
    console.log(`⚠️ 미매칭 제품 표시: ${unmatchedList.length}개`);
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
 * HTML 속성용 이스케이프 처리
 * @param {string} text - 텍스트
 * @returns {string} 이스케이프된 텍스트
 */
function escapeForAttribute(text) {
    if (!text) return '';
    return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

/**
 * 전역 함수 노출 (onclick 이벤트용)
 */
if (typeof window !== 'undefined') {
    window.matchingModule = {
        skipCurrentMatch,
        confirmCurrentMatch,
        editMatching,
        selectBomProduct
    };
}

/**
 * 매칭 통계 정보
 * @returns {Object} 매칭 통계
 */
export function getMatchingStats() {
    const totalProducts = AppState.data.allInjectionProducts.length;
    const matchedProducts = Object.keys(AppState.matching.productMatches).length;
    const directMatches = AppState.data.allInjectionProducts.filter(product => 
        AppState.data.bomJsonData.some(item => item['판매명'] === product)
    ).length;
    
    return {
        total: totalProducts,
        matched: matchedProducts + directMatches,
        unmatched: totalProducts - matchedProducts - directMatches,
        savedMatches: matchedProducts,
        directMatches: directMatches
    };
}

/**
 * 매칭 정보 내보내기 (디버깅/백업용)
 * @returns {Object} 매칭 정보
 */
export function exportMatches() {
    return {
        productMatches: AppState.matching.productMatches,
        timestamp: new Date().toISOString(),
        stats: getMatchingStats()
    };
}

/**
 * 매칭 정보 가져오기 (복원용)
 * @param {Object} matchingData - 매칭 데이터
 */
export function importMatches(matchingData) {
    if (matchingData && matchingData.productMatches) {
        AppState.matching.productMatches = matchingData.productMatches;
        saveMatches();
        updateMatchingTab();
        console.log('📥 매칭 정보 가져오기 완료');
    } else {
        console.error('❌ 유효하지 않은 매칭 데이터');
    }
}