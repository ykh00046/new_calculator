/**
 * 파일 업로드 및 처리 모듈
 * 엑셀 파일 읽기, 파싱, 유효성 검사 담당
 */

import { AppState } from './state.js';

/**
 * 파일 업로드 핸들러 초기화
 */
export function initializeFileHandlers() {
    // 사출계획 파일 업로드
    document.getElementById('injection-file').addEventListener('change', (e) => {
        handleFileUpload(e, 'injection');
    });
    
    // BOM 파일 업로드
    document.getElementById('bom-file').addEventListener('change', (e) => {
        handleFileUpload(e, 'bom');
    });
    
    console.log('📁 파일 핸들러 초기화 완료');
}

/**
 * 파일 업로드 처리
 * @param {Event} event - 파일 입력 이벤트
 * @param {string} type - 파일 타입 ('injection' 또는 'bom')
 */
export function handleFileUpload(event, type) {
    const file = event.target.files[0];
    if (!file) return;

    // 파일 유효성 검사
    if (!validateFile(file)) {
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const workbook = XLSX.read(e.target.result, {type: 'binary'});
            
            // 추가 유효성 검사
            if (!validateWorkbook(workbook, type)) {
                return;
            }
            
            // 상태 업데이트 및 UI 반영
            updateFileState(workbook, file, type);
            updateFileUI(file, type);
            
            console.log(`✅ ${type} 파일 로드 완료: ${file.name}`);
            
        } catch (error) {
            console.error('❌ 파일 읽기 오류:', error);
            alert(`파일 읽기 오류: ${error.message}`);
        }
    };
    
    reader.readAsBinaryString(file);
}

/**
 * 파일 유효성 검사
 * @param {File} file - 업로드된 파일
 * @returns {boolean} 유효성 여부
 */
function validateFile(file) {
    // 파일 확장자 검사
    const validExtensions = ['.xlsx', '.xls'];
    const fileName = file.name.toLowerCase();
    const isValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidExtension) {
        alert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.');
        return false;
    }
    
    // 파일 크기 검사 (10MB 제한)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        alert('파일 크기는 10MB 이하만 가능합니다.');
        return false;
    }
    
    return true;
}

/**
 * 워크북 유효성 검사
 * @param {Object} workbook - XLSX 워크북 객체
 * @param {string} type - 파일 타입
 * @returns {boolean} 유효성 여부
 */
function validateWorkbook(workbook, type) {
    // 시트 존재 여부 확인
    if (!workbook.SheetNames || workbook.SheetNames.length === 0) {
        alert('유효한 시트가 없습니다.');
        return false;
    }
    
    const sheet = workbook.Sheets[workbook.SheetNames[0]];
    if (!sheet) {
        alert('첫 번째 시트를 읽을 수 없습니다.');
        return false;
    }
    
    // 타입별 특별 검사
    if (type === 'injection') {
        return validateInjectionSheet(sheet);
    } else if (type === 'bom') {
        return validateBOMSheet(sheet);
    }
    
    return true;
}

/**
 * 사출계획 시트 유효성 검사
 * @param {Object} sheet - 엑셀 시트
 * @returns {boolean} 유효성 여부
 */
function validateInjectionSheet(sheet) {
    const jsonData = XLSX.utils.sheet_to_json(sheet, {header: 1});
    
    // 최소 데이터 행 수 확인
    if (jsonData.length < 4) {
        alert('사출계획 파일에 충분한 데이터가 없습니다.');
        return false;
    }
    
    // '호기' 열 존재 확인
    let hasValidData = false;
    for (let i = 3; i < Math.min(jsonData.length, 10); i++) {
        const row = jsonData[i];
        if (row && row[0] && row[0].toString().includes('호기')) {
            hasValidData = true;
            break;
        }
    }
    
    if (!hasValidData) {
        alert('사출계획 파일 형식이 올바르지 않습니다. (호기 정보를 찾을 수 없음)');
        return false;
    }
    
    return true;
}

/**
 * BOM 시트 유효성 검사
 * @param {Object} sheet - 엑셀 시트
 * @returns {boolean} 유효성 여부
 */
function validateBOMSheet(sheet) {
    const jsonData = XLSX.utils.sheet_to_json(sheet);
    
    // 최소 데이터 확인
    if (jsonData.length === 0) {
        alert('BOM 파일에 데이터가 없습니다.');
        return false;
    }
    
    // 필수 컬럼 확인
    const requiredColumns = ['판매명'];
    const firstRow = jsonData[0];
    const hasRequiredColumns = requiredColumns.every(col => 
        firstRow.hasOwnProperty(col)
    );
    
    if (!hasRequiredColumns) {
        alert('BOM 파일에 필수 컬럼이 없습니다. (판매명 컬럼 필요)');
        return false;
    }
    
    return true;
}

/**
 * 파일 상태 업데이트
 * @param {Object} workbook - 워크북 객체
 * @param {File} file - 파일 객체
 * @param {string} type - 파일 타입
 */
function updateFileState(workbook, file, type) {
    if (type === 'injection') {
        AppState.files.injection = workbook;
    } else if (type === 'bom') {
        AppState.files.bom = workbook;
        
        // BOM 데이터 미리 파싱
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        AppState.data.bomJsonData = XLSX.utils.sheet_to_json(sheet);
        console.log(`📋 BOM 데이터 파싱 완료: ${AppState.data.bomJsonData.length}개 제품`);
    }
    
    // 계산 버튼 활성화 체크
    updateCalculateButton();
}

/**
 * 파일 업로드 UI 업데이트
 * @param {File} file - 파일 객체
 * @param {string} type - 파일 타입
 */
function updateFileUI(file, type) {
    const uploadId = type === 'injection' ? 'injection-upload' : 'bom-upload';
    const uploadBox = document.getElementById(uploadId);
    const label = uploadBox.querySelector('label');
    
    // 업로드 완료 표시
    uploadBox.classList.add('active');
    label.innerHTML = `✅ ${file.name}<br><small>업로드 완료</small>`;
}

/**
 * 계산 버튼 상태 업데이트
 */
function updateCalculateButton() {
    const calculateBtn = document.getElementById('calculate-btn');
    const isReady = AppState.files.injection && AppState.files.bom;
    
    calculateBtn.disabled = !isReady;
    
    if (isReady) {
        calculateBtn.textContent = '🧮 약품/잉크 종류 계산하기';
        console.log('🎯 계산 준비 완료');
    }
}

/**
 * 파일 정보 출력 (디버깅용)
 */
export function logFileInfo() {
    console.group('📁 파일 정보');
    
    if (AppState.files.injection) {
        console.log('사출계획:', {
            sheets: AppState.files.injection.SheetNames,
            loaded: true
        });
    } else {
        console.log('사출계획: 미업로드');
    }
    
    if (AppState.files.bom) {
        console.log('BOM:', {
            sheets: AppState.files.bom.SheetNames,
            products: AppState.data.bomJsonData.length,
            loaded: true
        });
    } else {
        console.log('BOM: 미업로드');
    }
    
    console.groupEnd();
}

/**
 * 파일 상태 리셋
 */
export function resetFiles() {
    AppState.files.injection = null;
    AppState.files.bom = null;
    AppState.data.bomJsonData = [];
    
    // UI 리셋
    document.getElementById('injection-upload').classList.remove('active');
    document.getElementById('bom-upload').classList.remove('active');
    
    document.querySelector('#injection-upload label').innerHTML = 
        '📅 사출계획 파일 업로드<br><small>(예: 06월 5주차 사출계획_250630.xlsx)</small>';
    document.querySelector('#bom-upload label').innerHTML = 
        '🔧 BOM Tree 파일 업로드<br><small>(예: bom_tree.xlsx)</small>';
    
    updateCalculateButton();
    
    console.log('🔄 파일 상태 리셋 완료');
}