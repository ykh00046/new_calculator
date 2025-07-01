/**
 * 애플리케이션 전역 상태 관리
 * 모든 데이터와 UI 상태를 중앙에서 관리
 */

// 전역 상태 객체
export const AppState = {
    // 파일 관련 상태
    files: {
        injection: null,          // 사출계획 엑셀 파일
        bom: null                 // BOM Tree 엑셀 파일
    },
    
    // 데이터 상태
    data: {
        bomJsonData: [],          // BOM 데이터 (JSON 형태)
        allInjectionProducts: [], // 모든 사출계획 제품 목록
        calculatedResults: null   // 계산 결과
    },
    
    // 매칭 관련 상태
    matching: {
        productMatches: {},       // 저장된 제품 매칭 정보
        currentEditingProduct: null, // 현재 편집 중인 제품
        pendingMatches: {},       // 임시 매칭 정보
        currentMatchingProducts: [], // 현재 매칭 중인 제품 목록
        matchingIndex: 0,         // 매칭 진행 인덱스
        unmatchedProducts: []     // 매칭되지 않은 제품 목록
    },
    
    // UI 상태
    ui: {
        selectedDate: null,       // 선택된 날짜
        activeTab: 'results'      // 활성 탭
    }
};

/**
 * 상태 초기화
 */
export function initializeState() {
    // localStorage에서 저장된 매칭 정보 로드
    loadSavedMatches();
    
    console.log('✅ AppState 초기화 완료');
}

/**
 * 저장된 매칭 정보 로드
 */
function loadSavedMatches() {
    try {
        const saved = localStorage.getItem('productMatches');
        if (saved) {
            AppState.matching.productMatches = JSON.parse(saved);
            console.log(`📦 저장된 매칭 정보 로드: ${Object.keys(AppState.matching.productMatches).length}개`);
        }
    } catch (error) {
        console.warn('⚠️ 매칭 정보 로드 실패:', error);
        AppState.matching.productMatches = {};
    }
}

/**
 * 매칭 정보 저장
 */
export function saveMatches() {
    try {
        localStorage.setItem('productMatches', JSON.stringify(AppState.matching.productMatches));
        console.log('💾 매칭 정보 저장 완료');
    } catch (error) {
        console.warn('⚠️ 매칭 정보 저장 실패:', error);
    }
}

/**
 * 상태 유효성 검사
 */
export function validateState() {
    const errors = [];
    
    // 필수 파일 체크
    if (!AppState.files.injection) {
        errors.push('사출계획 파일이 없습니다');
    }
    
    if (!AppState.files.bom) {
        errors.push('BOM 파일이 없습니다');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * 상태 리셋 (디버깅용)
 */
export function resetState() {
    AppState.files.injection = null;
    AppState.files.bom = null;
    AppState.data.bomJsonData = [];
    AppState.data.allInjectionProducts = [];
    AppState.data.calculatedResults = null;
    AppState.matching.currentEditingProduct = null;
    AppState.matching.pendingMatches = {};
    AppState.matching.currentMatchingProducts = [];
    AppState.matching.matchingIndex = 0;
    AppState.matching.unmatchedProducts = [];
    AppState.ui.selectedDate = null;
    AppState.ui.activeTab = 'results';
    
    console.log('🔄 상태 리셋 완료');
}

/**
 * 상태 정보 출력 (디버깅용)
 */
export function logState() {
    console.group('📊 현재 AppState');
    console.log('Files:', {
        injection: !!AppState.files.injection,
        bom: !!AppState.files.bom
    });
    console.log('Data:', {
        bomProducts: AppState.data.bomJsonData.length,
        injectionProducts: AppState.data.allInjectionProducts.length,
        hasResults: !!AppState.data.calculatedResults
    });
    console.log('Matching:', {
        savedMatches: Object.keys(AppState.matching.productMatches).length,
        currentEditing: AppState.matching.currentEditingProduct,
        unmatched: AppState.matching.unmatchedProducts.length
    });
    console.log('UI:', AppState.ui);
    console.groupEnd();
}