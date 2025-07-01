/**
 * 메인 애플리케이션 모듈
 * 앱 초기화, 이벤트 통합 관리, 워크플로우 제어
 */

import { initializeState, AppState } from './state.js';
import { initializeFileHandlers } from './fileHandler.js';
import { calculateMaterials } from './calculator.js';
import { initializeMatching, showMatchingInterface, updateMatchingTab } from './matching.js';
import { initializeUI, displayResults, showResultsSection, registerUIEventListeners } from './ui.js';
import { initializeDownload } from './download.js';

/**
 * 애플리케이션 시작점
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 앱 초기화
 */
async function initializeApp() {
    try {
        console.log('🚀 애플리케이션 초기화 시작');
        
        // 로딩 표시
        showInitializationProgress();
        
        // 각 모듈 초기화
        await initializeModules();
        
        // 이벤트 리스너 등록
        registerEventListeners();
        
        // 초기화 완료
        hideInitializationProgress();
        
        console.log('✅ 애플리케이션 초기화 완료');
        
        // 개발 모드에서 디버그 정보 표시
        if (isDevelopmentMode()) {
            logInitializationInfo();
        }
        
    } catch (error) {
        console.error('❌ 애플리케이션 초기화 실패:', error);
        showInitializationError(error);
    }
}

/**
 * 모듈들 초기화
 */
async function initializeModules() {
    // 상태 관리 초기화
    initializeState();
    
    // 파일 핸들러 초기화
    initializeFileHandlers();
    
    // 계산기 초기화 (필요시)
    // calculateMaterials는 버튼 클릭시에만 실행
    
    // 매칭 시스템 초기화
    initializeMatching();
    
    // UI 관리자 초기화
    initializeUI();
    
    // 다운로드 기능 초기화
    initializeDownload();
    
    // UI 이벤트 리스너 등록
    registerUIEventListeners();
}

/**
 * 메인 이벤트 리스너 등록
 */
function registerEventListeners() {
    // 계산 버튼 이벤트
    document.getElementById('calculate-btn').addEventListener('click', handleCalculateClick);
    
    // 키보드 단축키 (전역)
    document.addEventListener('keydown', handleGlobalKeydown);
    
    // 창 포커스 이벤트
    window.addEventListener('focus', handleWindowFocus);
    
    // 페이지 언로드 이벤트 (데이터 저장)
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // 에러 핸들링
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    console.log('📡 메인 이벤트 리스너 등록 완료');
}

/**
 * 계산 버튼 클릭 처리
 */
async function handleCalculateClick() {
    try {
        console.log('🧮 계산 시작');
        
        // 파일 업로드 상태 확인
        if (!AppState.files.injection || !AppState.files.bom) {
            alert('사출계획 파일과 BOM 파일을 모두 업로드해주세요.');
            return;
        }
        
        // 계산 실행
        const result = await calculateMaterials();
        
        if (result.needsMatching) {
            // 매칭이 필요한 경우
            console.log('🔗 매칭 인터페이스 표시');
            showMatchingInterface(result.unmatchedProducts, AppState.data.bomJsonData);
        } else if (result.success) {
            // 계산 성공
            console.log('✅ 계산 및 표시 완료');
            displayResults(result.results);
            showResultsSection();
            updateMatchingTab();
        }
        
    } catch (error) {
        console.error('❌ 계산 처리 오류:', error);
        alert(`계산 중 오류가 발생했습니다: ${error.message}`);
    }
}

/**
 * 전역 키보드 이벤트 처리
 * @param {KeyboardEvent} event - 키보드 이벤트
 */
function handleGlobalKeydown(event) {
    // F5: 새로고침 확인
    if (event.key === 'F5' && AppState.data.calculatedResults) {
        if (!confirm('계산된 결과가 사라집니다. 새로고침하시겠습니까?')) {
            event.preventDefault();
        }
    }
    
    // Ctrl + S: 매칭 정보 저장
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        import('./state.js').then(stateModule => {
            stateModule.saveMatches();
            console.log('💾 매칭 정보 수동 저장');
        });
    }
    
    // Ctrl + Shift + D: 개발 도구
    if (event.ctrlKey && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        toggleDevTools();
    }
}

/**
 * 창 포커스 이벤트 처리
 */
function handleWindowFocus() {
    // 창이 다시 포커스될 때 UI 새로고침
    if (AppState.data.calculatedResults) {
        console.log('🔄 창 포커스 - UI 새로고침');
        // 필요시 UI 업데이트
    }
}

/**
 * 페이지 언로드 전 처리
 * @param {BeforeUnloadEvent} event - 언로드 이벤트
 */
function handleBeforeUnload(event) {
    // 계산된 결과가 있으면 확인 메시지
    if (AppState.data.calculatedResults) {
        const message = '계산된 결과가 사라집니다. 정말로 나가시겠습니까?';
        event.returnValue = message;
        return message;
    }
    
    // 매칭 정보 자동 저장
    try {
        import('./state.js').then(stateModule => {
            stateModule.saveMatches();
        });
    } catch (error) {
        console.warn('⚠️ 종료 시 매칭 정보 저장 실패:', error);
    }
}

/**
 * 전역 에러 핸들링
 * @param {ErrorEvent} event - 에러 이벤트
 */
function handleGlobalError(event) {
    console.error('❌ 전역 에러:', event.error);
    
    // 사용자에게 친화적인 에러 메시지
    const userMessage = getUserFriendlyErrorMessage(event.error);
    
    // 중요한 에러만 사용자에게 알림
    if (isCriticalError(event.error)) {
        alert(`오류가 발생했습니다: ${userMessage}`);
    }
    
    // 에러 로깅 (개발 모드)
    if (isDevelopmentMode()) {
        logErrorDetails(event.error);
    }
}

/**
 * 처리되지 않은 Promise 거부 핸들링
 * @param {PromiseRejectionEvent} event - Promise 거부 이벤트
 */
function handleUnhandledRejection(event) {
    console.error('❌ 처리되지 않은 Promise 거부:', event.reason);
    
    // Promise 거부 이벤트의 기본 동작 방지
    event.preventDefault();
    
    // 에러 처리
    handleGlobalError({ error: event.reason });
}

/**
 * 사용자 친화적 에러 메시지 생성
 * @param {Error} error - 에러 객체
 * @returns {string} 사용자 친화적 메시지
 */
function getUserFriendlyErrorMessage(error) {
    if (!error) return '알 수 없는 오류가 발생했습니다.';
    
    const message = error.message || error.toString();
    
    // 특정 에러 패턴에 대한 친화적 메시지
    if (message.includes('NetworkError') || message.includes('fetch')) {
        return '네트워크 연결을 확인해주세요.';
    }
    
    if (message.includes('Permission denied') || message.includes('Access denied')) {
        return '파일에 접근할 수 없습니다. 권한을 확인해주세요.';
    }
    
    if (message.includes('Invalid file') || message.includes('File format')) {
        return '파일 형식이 올바르지 않습니다.';
    }
    
    if (message.includes('Memory') || message.includes('quota')) {
        return '메모리가 부족합니다. 페이지를 새로고침해주세요.';
    }
    
    // 기본 메시지
    return message.length > 100 ? message.substring(0, 100) + '...' : message;
}

/**
 * 중요한 에러인지 판단
 * @param {Error} error - 에러 객체
 * @returns {boolean} 중요한 에러 여부
 */
function isCriticalError(error) {
    if (!error) return false;
    
    const message = error.message || error.toString();
    
    // 중요하지 않은 에러들
    const nonCriticalPatterns = [
        'ResizeObserver loop limit exceeded',
        'Non-Error promise rejection captured',
        'Script error',
        'Network request failed'
    ];
    
    return !nonCriticalPatterns.some(pattern => message.includes(pattern));
}

/**
 * 초기화 진행 상태 표시
 */
function showInitializationProgress() {
    const button = document.getElementById('calculate-btn');
    if (button) {
        button.textContent = '⏳ 초기화 중...';
        button.disabled = true;
    }
}

/**
 * 초기화 진행 상태 숨김
 */
function hideInitializationProgress() {
    const button = document.getElementById('calculate-btn');
    if (button && !AppState.files.injection && !AppState.files.bom) {
        button.textContent = '🧮 약품/잉크 종류 계산하기';
        button.disabled = true;
    }
}

/**
 * 초기화 에러 표시
 * @param {Error} error - 에러 객체
 */
function showInitializationError(error) {
    const container = document.querySelector('.container');
    if (container) {
        container.innerHTML = `
            <div style="padding: 50px; text-align: center; color: #dc3545;">
                <h2>❌ 애플리케이션 초기화 실패</h2>
                <p style="margin: 20px 0;">${getUserFriendlyErrorMessage(error)}</p>
                <button onclick="location.reload()" style="
                    background: #007bff; color: white; border: none;
                    padding: 15px 30px; border-radius: 8px; cursor: pointer;
                ">페이지 새로고침</button>
            </div>
        `;
    }
}

/**
 * 개발 모드 확인
 * @returns {boolean} 개발 모드 여부
 */
function isDevelopmentMode() {
    return location.hostname === 'localhost' || 
           location.hostname === '127.0.0.1' || 
           location.search.includes('debug=true');
}

/**
 * 초기화 정보 로깅 (개발 모드)
 */
function logInitializationInfo() {
    console.group('🔧 개발 모드 정보');
    console.log('URL:', location.href);
    console.log('User Agent:', navigator.userAgent);
    console.log('AppState:', AppState);
    console.log('Available Memory:', navigator.deviceMemory || 'Unknown');
    console.log('Connection:', navigator.connection || 'Unknown');
    console.groupEnd();
}

/**
 * 에러 상세 로깅 (개발 모드)
 * @param {Error} error - 에러 객체
 */
function logErrorDetails(error) {
    console.group('🐛 에러 상세 정보');
    console.error('Error:', error);
    console.error('Stack:', error.stack);
    console.error('AppState:', AppState);
    console.error('Timestamp:', new Date().toISOString());
    console.groupEnd();
}

/**
 * 개발 도구 토글
 */
function toggleDevTools() {
    if (!isDevelopmentMode()) {
        console.log('개발 모드가 아닙니다.');
        return;
    }
    
    const existingPanel = document.getElementById('dev-tools-panel');
    
    if (existingPanel) {
        existingPanel.remove();
        return;
    }
    
    // 개발 도구 패널 생성
    const panel = document.createElement('div');
    panel.id = 'dev-tools-panel';
    panel.style.cssText = `
        position: fixed; top: 20px; right: 20px; width: 300px;
        background: rgba(0,0,0,0.9); color: white; padding: 20px;
        border-radius: 8px; z-index: 10003; font-family: monospace;
        font-