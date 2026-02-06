"""
예외 처리 유틸리티
다양한 예외 상황에 대한 표준화된 처리를 제공합니다.
"""
import functools
from typing import Optional, Callable, Any
from PySide6.QtWidgets import QMessageBox
from ui.styles import UITheme
from .logger import logger


class MixingProgramError(Exception):
    """배합 프로그램 기본 예외"""
    pass


class RecipeNotFoundError(MixingProgramError):
    """레시피를 찾을 수 없을 때 발생하는 예외"""
    pass


class InvalidMixingRatioError(MixingProgramError):
    """배합비율이 유효하지 않을 때 발생하는 예외"""
    pass


class FileOperationError(MixingProgramError):
    """파일 작업 중 오류가 발생했을 때의 예외"""
    pass


class DatabaseError(MixingProgramError):
    """데이터베이스 작업 중 오류가 발생했을 때의 예외"""
    pass


def handle_exceptions(
    show_user_message: bool = True,
    user_message: str = "작업 중 오류가 발생했습니다.",
    reraise: bool = False,
    default_return: Any = None
):
    """
    함수 데코레이터: 예외를 자동으로 처리합니다.
    
    Args:
        show_user_message: 사용자에게 메시지 박스를 보여줄지 여부
        user_message: 사용자에게 보여줄 메시지
        reraise: 예외를 다시 발생시킬지 여부
        default_return: 예외 발생 시 반환할 기본값
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 로그 기록
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # 너무 긴 경우 자르기
                    'kwargs': str(kwargs)[:200]
                }
                logger.log_error_with_context(e, context)
                
                # 사용자 메시지 표시
                if show_user_message:
                    show_error_message(user_message, str(e))
                
                # 예외 재발생 또는 기본값 반환
                if reraise:
                    raise
                return default_return
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    error_message: str = "작업 실행 중 오류가 발생했습니다.",
    default_return: Any = None
) -> Any:
    """
    함수를 안전하게 실행합니다.
    
    Args:
        func: 실행할 함수
        args: 함수 인자
        kwargs: 함수 키워드 인자
        error_message: 오류 시 표시할 메시지
        default_return: 오류 시 반환할 기본값
    
    Returns:
        함수 실행 결과 또는 기본값
    """
    if kwargs is None:
        kwargs = {}
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.log_error_with_context(e, {
            'function': func.__name__,
            'args': str(args)[:200],
            'kwargs': str(kwargs)[:200]
        })
        show_error_message(error_message, str(e))
        return default_return


def show_error_message(title: str, detail: str = "", parent=None):
    """사용자에게 에러 메시지를 표시합니다."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("오류")
    msg_box.setText(title)
    msg_box.setStyleSheet(f"QLabel {{ color: {UITheme.TEXT_PRIMARY}; }} QAbstractButton {{ color: {UITheme.TEXT_PRIMARY}; }}")
    
    if detail:
        msg_box.setDetailedText(detail)
    
    msg_box.exec()


def show_warning_message(title: str, detail: str = "", parent=None):
    """사용자에게 경고 메시지를 표시합니다."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle("경고")
    msg_box.setText(title)
    msg_box.setStyleSheet(f"QLabel {{ color: {UITheme.TEXT_PRIMARY}; }} QAbstractButton {{ color: {UITheme.TEXT_PRIMARY}; }}")
    
    if detail:
        msg_box.setDetailedText(detail)
    
    msg_box.exec()


def show_info_message(title: str, detail: str = "", parent=None):
    """사용자에게 정보 메시지를 표시합니다."""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setWindowTitle("정보")
    msg_box.setText(title)
    msg_box.setStyleSheet(f"QLabel {{ color: {UITheme.TEXT_PRIMARY}; }} QAbstractButton {{ color: {UITheme.TEXT_PRIMARY}; }}")
    
    if detail:
        msg_box.setDetailedText(detail)
    
    msg_box.exec()


def validate_mixing_ratio(actual: float, theory: float, tolerance: float) -> bool:
    """
    배합 비율의 유효성을 검사합니다.
    
    Args:
        actual: 실제 배합량
        theory: 이론 배합량
        tolerance: 허용 오차
    
    Returns:
        유효한지 여부
    
    Raises:
        InvalidMixingRatioError: 허용 오차를 벗어난 경우
    """
    if abs(actual - theory) > tolerance:
        raise InvalidMixingRatioError(
            f"배합량이 허용 오차를 벗어났습니다. "
            f"이론값: {theory}, 실제값: {actual}, 허용오차: ±{tolerance}"
        )
    return True


def validate_file_exists(file_path: str, file_description: str = "파일"):
    """
    파일 존재 여부를 검사합니다.
    
    Args:
        file_path: 파일 경로
        file_description: 파일 설명
    
    Raises:
        FileOperationError: 파일이 존재하지 않는 경우
    """
    import os
    if not os.path.exists(file_path):
        raise FileOperationError(f"{file_description}을(를) 찾을 수 없습니다: {file_path}")


def validate_recipe_data(recipe_data: dict):
    """
    레시피 데이터의 유효성을 검사합니다.
    
    Args:
        recipe_data: 레시피 데이터
    
    Raises:
        RecipeNotFoundError: 레시피 데이터가 유효하지 않은 경우
    """
    required_fields = ['품목코드', '품목명', '배합비율']
    
    for field in required_fields:
        if field not in recipe_data:
            raise RecipeNotFoundError(f"레시피 데이터에 필수 필드가 없습니다: {field}")
    
    if not isinstance(recipe_data['배합비율'], (int, float)) or recipe_data['배합비율'] <= 0:
        raise RecipeNotFoundError("배합비율은 0보다 큰 숫자여야 합니다.")
