/**
 * 다운로드 기능 모듈
 * 엑셀 다운로드, CSV 생성, 브라우저 호환성 처리 담당
 */

import { AppState } from './state.js';
import { showModal, closeModal, showError, showProgress, hideProgress } from './ui.js';

/**
 * 다운로드 기능 초기화
 */
export function initializeDownload() {
    // 다운로드 버튼 이벤트 리스너
    document.getElementById('download-btn').addEventListener('click', downloadInkList);
    
    console.log('📥 다운로드 기능 초기화 완료');
}

/**
 * 잉크 목록 다운로드 메인 함수
 */
export function downloadInkList() {
    if (!AppState.data.calculatedResults) {
        showError('먼저 계산을 실행해주세요.');
        return;
    }

    try {
        console.log('📥 잉크 목록 다운로드 시작');
        showProgress(10, '데이터 수집 중...');

        // 주간 전체 잉크 데이터 수집
        const weeklyInks = collectWeeklyInkData();
        showProgress(30, '데이터 정렬 중...');

        // 내림차순 정렬
        const sortedInks = Object.entries(weeklyInks).sort((a, b) => b[1] - a[1]);
        
        if (sortedInks.length === 0) {
            hideProgress();
            showError('다운로드할 잉크 데이터가 없습니다.');
            return;
        }

        showProgress(50, 'CSV 생성 중...');

        // CSV 데이터 생성
        const csvContent = generateCSVContent(sortedInks);
        showProgress(70, '파일 준비 중...');

        // 다운로드 실행
        executeDownload(csvContent, sortedInks.length);
        showProgress(100, '완료');
        
        setTimeout(() => hideProgress(), 500);

    } catch (error) {
        console.error('❌ 다운로드 오류:', error);
        hideProgress();
        showDataAsText(); // 백업 방법
    }
}

/**
 * 주간 잉크 데이터 수집
 * @returns {Object} 주간 잉크 데이터
 */
function collectWeeklyInkData() {
    const weeklyInks = {};
    
    Object.keys(AppState.data.calculatedResults).forEach(date => {
        Object.keys(AppState.data.calculatedResults[date].inks).forEach(ink => {
            weeklyInks[ink] = (weeklyInks[ink] || 0) + AppState.data.calculatedResults[date].inks[ink];
        });
    });

    console.log(`📊 수집된 잉크 종류: ${Object.keys(weeklyInks).length}개`);
    return weeklyInks;
}

/**
 * CSV 컨텐츠 생성
 * @param {Array} sortedInks - 정렬된 잉크 배열
 * @returns {string} CSV 컨텐츠
 */
function generateCSVContent(sortedInks) {
    let csvContent = '순위,잉크명,필요량,비고,사용일자\n';
    
    sortedInks.forEach(([inkName, count], index) => {
        // 해당 잉크가 사용되는 날짜들 찾기
        const usageDates = findInkUsageDates(inkName);
        
        // CSV 안전성을 위한 문자열 처리
        const cleanInkName = escapeCSVField(inkName);
        const dateString = usageDates.join('; ');
        
        csvContent += `${index + 1},"${cleanInkName}",${count},"자동계산","${dateString}"\n`;
    });

    // 한글 지원을 위한 BOM 추가
    const BOM = '\uFEFF';
    return BOM + csvContent;
}

/**
 * 특정 잉크의 사용 날짜 찾기
 * @param {string} inkName - 잉크명
 * @returns {Array} 사용 날짜 배열
 */
function findInkUsageDates(inkName) {
    const dates = [];
    
    Object.keys(AppState.data.calculatedResults).forEach(date => {
        if (AppState.data.calculatedResults[date].inks[inkName]) {
            const dateObj = new Date(date);
            const formattedDate = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
            dates.push(formattedDate);
        }
    });
    
    return dates.sort();
}

/**
 * CSV 필드 이스케이프 처리
 * @param {string} field - 필드 값
 * @returns {string} 이스케이프된 값
 */
function escapeCSVField(field) {
    if (!field) return '';
    
    // 쉼표, 따옴표, 줄바꿈이 포함된 경우 처리
    let escaped = field.toString();
    
    // 따옴표 이스케이프
    escaped = escaped.replace(/"/g, '""');
    
    return escaped;
}

/**
 * 다운로드 실행
 * @param {string} content - 파일 컨텐츠
 * @param {number} count - 항목 수
 */
function executeDownload(content, count) {
    try {
        const filename = generateFileName();
        
        // 브라우저별 다운로드 처리
        if (downloadWithModernAPI(content, filename, count)) {
            return; // 성공
        }
        
        // 백업 방법: 모달로 데이터 표시
        showDataModal(content, count);
        
    } catch (error) {
        console.error('❌ 다운로드 실행 오류:', error);
        showDataModal(content, count);
    }
}

/**
 * 파일명 생성
 * @returns {string} 파일명
 */
function generateFileName() {
    const today = new Date();
    const dateString = today.getFullYear() + 
        (today.getMonth() + 1).toString().padStart(2, '0') + 
        today.getDate().toString().padStart(2, '0');
    
    return `잉크_소요량_${dateString}.csv`;
}

/**
 * 최신 브라우저 API로 다운로드
 * @param {string} content - 컨텐츠
 * @param {string} filename - 파일명
 * @param {number} count - 항목 수
 * @returns {boolean} 성공 여부
 */
function downloadWithModernAPI(content, filename, count) {
    try {
        // Blob 생성
        const blob = new Blob([content], { 
            type: 'text/csv;charset=utf-8;' 
        });

        // IE 브라우저 지원
        if (window.navigator && window.navigator.msSaveOrOpenBlob) {
            window.navigator.msSaveOrOpenBlob(blob, filename);
            showDownloadSuccess(filename, count);
            return true;
        }

        // 최신 브라우저 지원
        const url = window.URL.createObjectURL(blob);
        const tempLink = document.createElement('a');
        
        tempLink.style.display = 'none';
        tempLink.href = url;
        tempLink.setAttribute('download', filename);
        
        // 안전한 DOM 조작
        if (document.body) {
            document.body.appendChild(tempLink);
            tempLink.click();
            document.body.removeChild(tempLink);
        } else {
            tempLink.click();
        }

        // URL 정리
        window.URL.revokeObjectURL(url);

        // 성공 메시지 (약간의 지연 후)
        setTimeout(() => {
            showDownloadSuccess(filename, count);
        }, 100);

        return true;

    } catch (error) {
        console.error('❌ 최신 API 다운로드 실패:', error);
        return false;
    }
}

/**
 * 다운로드 성공 메시지
 * @param {string} filename - 파일명
 * @param {number} count - 항목 수
 */
function showDownloadSuccess(filename, count) {
    const message = `${filename} 파일이 다운로드되었습니다!\n\n` +
                   `총 ${count}개 잉크 목록이 포함되어 있습니다.\n\n` +
                   `※ 다운로드 폴더를 확인해주세요.`;
    
    showModal('다운로드 완료', message, [
        {
            text: '확인',
            color: '#28a745',
            onclick: 'window.downloadModule.closeModal()'
        }
    ]);
}

/**
 * 데이터 모달로 표시 (복사/붙여넣기용)
 * @param {string} content - CSV 컨텐츠
 * @param {number} count - 항목 수
 */
function showDataModal(content, count) {
    const modalContent = `
        <div style="
            background: #f8f9fa; padding: 15px; border-radius: 8px;
            margin-bottom: 20px; border-left: 4px solid #007bff;
        ">
            <strong>📋 사용 방법:</strong><br>
            1. 아래 텍스트를 모두 선택 (Ctrl+A)<br>
            2. 복사 (Ctrl+C)<br>
            3. 엑셀에 새 시트 만들고 붙여넣기 (Ctrl+V)<br>
            4. 엑셀에서 "데이터 → 텍스트 나누기" 선택<br>
            5. 구분 기호 "쉼표" 선택하여 완료
        </div>
        <textarea id="csv-data" style="
            width: 100%; height: 300px; 
            font-family: 'Courier New', monospace; font-size: 12px;
            border: 2px solid #ddd; border-radius: 5px; padding: 10px;
            resize: vertical; background: #fafafa;
        " readonly>${content}</textarea>
    `;

    showModal(
        `📊 잉크 소요량 데이터 (${count}개)`,
        modalContent,
        [
            {
                text: '📋 복사하기',
                color: '#28a745',
                onclick: 'window.downloadModule.copyToClipboard()'
            },
            {
                text: '닫기',
                color: '#6c757d',
                onclick: 'window.downloadModule.closeModal()'
            }
        ]
    );

    // 텍스트 자동 선택
    setTimeout(() => {
        const textarea = document.getElementById('csv-data');
        if (textarea) {
            textarea.focus();
            textarea.select();
        }
    }, 100);
}

/**
 * 클립보드에 복사
 */
export function copyToClipboard() {
    const textarea = document.getElementById('csv-data');
    if (textarea) {
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                alert('📋 데이터가 클립보드에 복사되었습니다!');
            } else {
                alert('복사에 실패했습니다. 수동으로 선택하여 복사해주세요.');
            }
        } catch (err) {
            console.warn('클립보드 복사 실패:', err);
            alert('복사에 실패했습니다. 수동으로 선택하여 복사해주세요.');
        }
    }
}

/**
 * 간단한 텍스트 알림 (최종 백업)
 */
function showDataAsText() {
    if (!AppState.data.calculatedResults) return;

    const weeklyInks = collectWeeklyInkData();
    const sortedInks = Object.entries(weeklyInks).sort((a, b) => b[1] - a[1]);
    
    let displayText = '📊 잉크 소요량 목록 (내림차순)\n';
    displayText += '='.repeat(40) + '\n\n';
    
    sortedInks.slice(0, 20).forEach(([inkName, count], index) => {
        displayText += `${(index + 1).toString().padStart(2, ' ')}. ${inkName}: ${count}\n`;
    });
    
    if (sortedInks.length > 20) {
        displayText += `\n... 외 ${sortedInks.length - 20}개 더`;
    }

    showModal(
        '잉크 소요량 목록',
        `<pre style="white-space: pre-wrap; font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 400px; overflow-y: auto;">${displayText}</pre>`,
        [
            {
                text: '확인',
                color: '#007bff',
                onclick: 'window.downloadModule.closeModal()'
            }
        ]
    );
}

/**
 * 다운로드 포맷 선택 모달
 */
export function showDownloadOptions() {
    const modalContent = `
        <div style="text-align: center; margin: 20px 0;">
            <p style="margin-bottom: 20px;">다운로드할 형식을 선택하세요:</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; max-width: 400px; margin: 0 auto;">
                <button onclick="window.downloadModule.downloadCSV()" style="
                    padding: 15px; border: 2px solid #28a745; border-radius: 8px;
                    background: white; color: #28a745; cursor: pointer; font-weight: bold;
                ">📊 CSV 파일<br><small>엑셀에서 열기</small></button>
                <button onclick="window.downloadModule.downloadExcel()" style="
                    padding: 15px; border: 2px solid #007bff; border-radius: 8px;
                    background: white; color: #007bff; cursor: pointer; font-weight: bold;
                ">📈 엑셀 파일<br><small>직접 열기</small></button>
            </div>
        </div>
    `;

    showModal('다운로드 옵션', modalContent, [
        {
            text: '취소',
            color: '#6c757d',
            onclick: 'window.downloadModule.closeModal()'
        }
    ]);
}

/**
 * CSV 형식으로 다운로드
 */
export function downloadCSV() {
    closeModal();
    downloadInkList();
}

/**
 * 엑셀 형식으로 다운로드 (향후 구현)
 */
export function downloadExcel() {
    closeModal();
    showModal(
        '기능 준비 중',
        '엑셀 형식 다운로드는 준비 중입니다.<br>현재는 CSV 형식만 지원됩니다.',
        [
            {
                text: 'CSV 다운로드',
                color: '#28a745',
                onclick: 'window.downloadModule.downloadCSV()'
            },
            {
                text: '확인',
                color: '#007bff',
                onclick: 'window.downloadModule.closeModal()'
            }
        ]
    );
}

/**
 * 전체 데이터 내보내기 (JSON 형태)
 */
export function exportAllData() {
    if (!AppState.data.calculatedResults) {
        showError('내보낼 데이터가 없습니다.');
        return;
    }

    try {
        const exportData = {
            timestamp: new Date().toISOString(),
            version: '1.0',
            calculatedResults: AppState.data.calculatedResults,
            productMatches: AppState.matching.productMatches,
            injectionProducts: AppState.data.allInjectionProducts,
            bomData: AppState.data.bomJsonData.map(item => ({
                판매명: item['판매명'],
                약품명: item['약품명'],
                잉크명1: item['잉크명1'],
                잉크명2: item['잉크명2'],
                잉크명3: item['잉크명3']
            }))
        };

        const jsonContent = JSON.stringify(exportData, null, 2);
        const filename = `사출계획_전체데이터_${generateDateString()}.json`;

        downloadWithModernAPI(jsonContent, filename, Object.keys(exportData).length);

    } catch (error) {
        console.error('❌ 전체 데이터 내보내기 실패:', error);
        showError('데이터 내보내기에 실패했습니다.');
    }
}

/**
 * 날짜 문자열 생성
 * @returns {string} YYYYMMDD 형태의 날짜
 */
function generateDateString() {
    const today = new Date();
    return today.getFullYear() + 
        (today.getMonth() + 1).toString().padStart(2, '0') + 
        today.getDate().toString().padStart(2, '0');
}

/**
 * 특정 날짜의 데이터만 다운로드
 * @param {string} selectedDate - 선택된 날짜
 */
export function downloadDateData(selectedDate) {
    if (!AppState.data.calculatedResults || !AppState.data.calculatedResults[selectedDate]) {
        showError('선택된 날짜의 데이터가 없습니다.');
        return;
    }

    try {
        const dateData = AppState.data.calculatedResults[selectedDate];
        
        // 날짜별 CSV 생성
        let csvContent = '구분,항목명,수량\n';
        
        // 제품 목록
        csvContent += '제품,제품 종류,' + dateData.products.length + '\n';
        dateData.products.forEach(product => {
            csvContent += `제품,"${escapeCSVField(product)}",1\n`;
        });
        
        csvContent += '\n';
        
        // 약품 목록
        csvContent += '약품,약품 종류,' + Object.keys(dateData.chemicals).length + '\n';
        Object.entries(dateData.chemicals).forEach(([chemical, count]) => {
            csvContent += `약품,"${escapeCSVField(chemical)}",${count}\n`;
        });
        
        csvContent += '\n';
        
        // 잉크 목록
        csvContent += '잉크,잉크 종류,' + Object.keys(dateData.inks).length + '\n';
        Object.entries(dateData.inks).forEach(([ink, count]) => {
            csvContent += `잉크,"${escapeCSVField(ink)}",${count}\n`;
        });

        const BOM = '\uFEFF';
        const finalContent = BOM + csvContent;
        
        const dateObj = new Date(selectedDate);
        const filename = `사출계획_${dateObj.getMonth() + 1}월${dateObj.getDate()}일_${generateDateString()}.csv`;
        
        downloadWithModernAPI(finalContent, filename, dateData.products.length + Object.keys(dateData.chemicals).length + Object.keys(dateData.inks).length);

    } catch (error) {
        console.error('❌ 날짜별 데이터 다운로드 실패:', error);
        showError('날짜별 데이터 다운로드에 실패했습니다.');
    }
}

/**
 * 요약 리포트 생성
 */
export function generateSummaryReport() {
    if (!AppState.data.calculatedResults) {
        showError('리포트를 생성할 데이터가 없습니다.');
        return;
    }

    try {
        const dates = Object.keys(AppState.data.calculatedResults).sort();
        const weeklyChemicals = {};
        const weeklyInks = {};
        
        // 전체 통계 계산
        dates.forEach(date => {
            const dayData = AppState.data.calculatedResults[date];
            
            Object.keys(dayData.chemicals).forEach(chemical => {
                weeklyChemicals[chemical] = (weeklyChemicals[chemical] || 0) + dayData.chemicals[chemical];
            });
            
            Object.keys(dayData.inks).forEach(ink => {
                weeklyInks[ink] = (weeklyInks[ink] || 0) + dayData.inks[ink];
            });
        });

        // 리포트 HTML 생성
        const reportHTML = generateReportHTML(dates, weeklyChemicals, weeklyInks);
        
        showModal(
            '📊 요약 리포트',
            reportHTML,
            [
                {
                    text: '인쇄',
                    color: '#17a2b8',
                    onclick: 'window.print()'
                },
                {
                    text: '닫기',
                    color: '#6c757d',
                    onclick: 'window.downloadModule.closeModal()'
                }
            ]
        );

    } catch (error) {
        console.error('❌ 리포트 생성 실패:', error);
        showError('리포트 생성에 실패했습니다.');
    }
}

/**
 * 리포트 HTML 생성
 * @param {Array} dates - 날짜 배열
 * @param {Object} weeklyChemicals - 주간 약품 데이터
 * @param {Object} weeklyInks - 주간 잉크 데이터
 * @returns {string} HTML 문자열
 */
function generateReportHTML(dates, weeklyChemicals, weeklyInks) {
    const startDate = new Date(dates[0]);
    const endDate = new Date(dates[dates.length - 1]);
    
    return `
        <div style="max-height: 70vh; overflow-y: auto; padding: 20px; font-family: Arial, sans-serif;">
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 15px;">
                <h2 style="margin: 0; color: #333;">사출계획 약품/잉크 요약 리포트</h2>
                <p style="margin: 10px 0; color: #666;">
                    기간: ${startDate.getMonth() + 1}월 ${startDate.getDate()}일 ~ ${endDate.getMonth() + 1}월 ${endDate.getDate()}일
                    (총 ${dates.length}일)
                </p>
                <p style="margin: 0; color: #999; font-size: 12px;">
                    생성일시: ${new Date().toLocaleString('ko-KR')}
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
                <div>
                    <h3 style="color: #28a745; border-bottom: 1px solid #28a745; padding-bottom: 5px;">
                        💊 약품 요약 (총 ${Object.keys(weeklyChemicals).length}종)
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">약품명</th>
                                <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">수량</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(weeklyChemicals)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 10)
                                .map(([chemical, count]) => 
                                    `<tr>
                                        <td style="border: 1px solid #ddd; padding: 8px;">${chemical}</td>
                                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">${count}</td>
                                    </tr>`
                                ).join('')}
                        </tbody>
                    </table>
                    ${Object.keys(weeklyChemicals).length > 10 ? `<p style="text-align: center; margin-top: 10px; color: #666; font-size: 12px;">...외 ${Object.keys(weeklyChemicals).length - 10}종</p>` : ''}
                </div>
                
                <div>
                    <h3 style="color: #007bff; border-bottom: 1px solid #007bff; padding-bottom: 5px;">
                        🎨 잉크 요약 (총 ${Object.keys(weeklyInks).length}종)
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">잉크명</th>
                                <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">수량</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(weeklyInks)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 10)
                                .map(([ink, count]) => 
                                    `<tr>
                                        <td style="border: 1px solid #ddd; padding: 8px;">${ink}</td>
                                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">${count}</td>
                                    </tr>`
                                ).join('')}
                        </tbody>
                    </table>
                    ${Object.keys(weeklyInks).length > 10 ? `<p style="text-align: center; margin-top: 10px; color: #666; font-size: 12px;">...외 ${Object.keys(weeklyInks).length - 10}종</p>` : ''}
                </div>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <h3 style="color: #333; margin-bottom: 15px;">📅 일자별 요약</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="border: 1px solid #ddd; padding: 8px;">날짜</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">제품 수</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">약품 종류</th>
                            <th style="border: 1px solid #ddd; padding: 8px;">잉크 종류</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${dates.map(date => {
                            const dayData = AppState.data.calculatedResults[date];
                            const dateObj = new Date(date);
                            const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
                            return `
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 8px;">
                                        ${dateObj.getMonth() + 1}/${dateObj.getDate()} (${dayNames[dateObj.getDay()]})
                                    </td>
                                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">${dayData.products.length}</td>
                                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">${Object.keys(dayData.chemicals).length}</td>
                                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">${Object.keys(dayData.inks).length}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                <p>본 리포트는 사출계획 약품/잉크 종류 계산기에서 자동 생성되었습니다.</p>
            </div>
        </div>
    `;
}

/**
 * 전역 함수 노출
 */
if (typeof window !== 'undefined') {
    window.downloadModule = {
        copyToClipboard,
        closeModal,
        downloadCSV,
        downloadExcel,
        showDownloadOptions: () => showDownloadOptions(),
        exportAllData: () => exportAllData(),
        generateSummaryReport: () => generateSummaryReport()
    };
}

/**
 * 다운로드 통계 정보
 * @returns {Object} 다운로드 가능한 데이터 통계
 */
export function getDownloadStats() {
    if (!AppState.data.calculatedResults) {
        return {
            available: false,
            message: '다운로드할 데이터가 없습니다.'
        };
    }

    const dates = Object.keys(AppState.data.calculatedResults);
    const weeklyInks = collectWeeklyInkData();
    
    return {
        available: true,
        dates: dates.length,
        totalInks: Object.keys(weeklyInks).length,
        totalProducts: AppState.data.allInjectionProducts.length,
        message: `${dates.length}일간 ${Object.keys(weeklyInks).length}종의 잉크 데이터`
    };
}