"""
로깅 시스템
애플리케이션의 모든 로그를 관리합니다.
"""
import os
import logging
import logging.handlers
from datetime import datetime
from config.settings import LOG_FOLDER


class Logger:
    """통합 로깅 시스템"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """로거 설정"""
        # 로그 폴더 생성
        log_dir = LOG_FOLDER
        os.makedirs(log_dir, exist_ok=True)
        
        # 로거 생성
        self._logger = logging.getLogger("MixingProgram")
        self._logger.setLevel(logging.DEBUG)
        
        # 중복 핸들러 방지
        if self._logger.handlers:
            return
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 파일 핸들러 (일별 로테이션)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "mixing_program.log"),
            when='D',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # 에러 전용 파일 핸들러
        error_handler = logging.FileHandler(
            filename=os.path.join(log_dir, "error.log"),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self._logger.addHandler(error_handler)
        
        # 콘솔 핸들러 (개발 환경용)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)-8s | %(module)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
    
    def debug(self, message, **kwargs):
        """디버그 로그"""
        self._logger.debug(message, **kwargs)

    def info(self, message, **kwargs):
        """정보 로그"""
        self._logger.info(message, **kwargs)

    def warning(self, message, **kwargs):
        """경고 로그"""
        self._logger.warning(message, **kwargs)

    def error(self, message, **kwargs):
        """에러 로그"""
        self._logger.error(message, **kwargs)

    def critical(self, message, **kwargs):
        """치명적 에러 로그"""
        self._logger.critical(message, **kwargs)
    
    def log_mixing_operation(self, operation, recipe_name, worker, **details):
        """배합 작업 전용 로그"""
        log_message = f"[배합작업] {operation} | 레시피: {recipe_name} | 작업자: {worker}"
        if details:
            detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
            log_message += f" | {detail_str}"
        self.info(log_message)
    
    def log_error_with_context(self, error, context=None):
        """컨텍스트와 함께 에러 로그"""
        import traceback
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        if context:
            error_info['context'] = context
        
        self.error(f"예외 발생: {error_info}")


# 글로벌 로거 인스턴스
logger = Logger()
