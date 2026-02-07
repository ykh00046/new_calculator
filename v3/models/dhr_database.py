"""
DHR 전용 데이터베이스 관리 모듈
기존 배합 기록과 분리된 별도 데이터베이스 사용
Google Sheets 백업 없음
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from config.settings import USER_DATA_DIR
from utils.logger import logger
from utils.error_handler import DatabaseError, handle_exceptions


# DHR 전용 DB 파일 경로
DHR_DB_FILE = os.path.join(USER_DATA_DIR, "dhr_records.db")


class DhrDatabaseManager:
    """DHR 전용 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = DHR_DB_FILE
        
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()
        logger.info(f"DHR 데이터베이스 초기화 완료: {self.db_path}")
    
    def _ensure_database_exists(self):
        """데이터베이스 디렉토리가 존재하는지 확인하고 생성"""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"DHR 데이터베이스 오류: {e}")
            raise DatabaseError(f"DHR 데이터베이스 연결 오류: {e}")
        finally:
            if conn:
                conn.close()
    
    @handle_exceptions(user_message="DHR 테이블 생성 중 오류가 발생했습니다.")
    def _create_tables(self):
        """필요한 테이블들을 생성"""
        with self.get_connection() as conn:
            # DHR 기록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dhr_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_lot TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    worker TEXT NOT NULL,
                    work_date TEXT NOT NULL,
                    work_time TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    scale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # DHR 상세 기록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dhr_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dhr_record_id INTEGER NOT NULL,
                    material_code TEXT,
                    material_name TEXT NOT NULL,
                    material_lot TEXT,
                    ratio REAL,
                    theory_amount REAL,
                    actual_amount REAL,
                    sequence_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dhr_record_id) REFERENCES dhr_records (id)
                )
            """)
            
            # --- DHR 레시피 관련 테이블 추가 ---
            
            # 분류 마스터 테이블 (거래처, 제품종류, 약품, 착용기간)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dhr_recipe_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category_type, value)
                )
            """)
            
            # DHR 레시피 헤더 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dhr_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_name TEXT NOT NULL,
                    company TEXT,
                    product_type TEXT,
                    drug TEXT,
                    wear_period TEXT,
                    default_amount REAL DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # DHR 레시피 자재 목록 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dhr_recipe_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    material_code TEXT,
                    material_name TEXT NOT NULL,
                    ratio REAL DEFAULT 0,
                    sequence_order INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recipe_id) REFERENCES dhr_recipes (id)
                )
            """)
            
            # 인덱스 생성
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dhr_records_date ON dhr_records(work_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dhr_records_lot ON dhr_records(product_lot)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dhr_recipes_name ON dhr_recipes(recipe_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dhr_categories_type ON dhr_recipe_categories(category_type)")
            
            conn.commit()
            logger.debug("DHR 데이터베이스 테이블 생성/확인 완료")
    
    @handle_exceptions(user_message="DHR 기록 저장 중 오류가 발생했습니다.")
    def generate_product_lot(self, product_name: str, work_date: str) -> str:
        """DHR 제품별로 신규 LOT 번호를 생성합니다. (예: {product_name}{YYMMDD}{seq:02d})"""
        target_date = datetime.strptime(work_date, "%Y-%m-%d")
        date_str = target_date.strftime("%y%m%d")
        base_lot = f"{product_name}{date_str}"

        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT product_lot FROM dhr_records WHERE work_date = ? AND product_name = ?", (work_date, product_name))
                max_seq = 0
                for row in cursor.fetchall():
                    lot = row['product_lot']
                    if lot.startswith(base_lot):
                        try:
                            seq = int(lot[len(base_lot):])
                            if seq > max_seq:
                                max_seq = seq
                        except (ValueError, IndexError):
                            continue
                new_seq = max_seq + 1
                return f"{base_lot}{new_seq:02d}"
        except Exception as e:
            logger.error(f"DHR LOT 번호 생성 실패: {e}. 기본값으로 대체합니다.")
            return f"{base_lot}01"

    def save_dhr_record(self, record_data: Dict, details: List[Dict]) -> int:
        """
        DHR 기록을 저장합니다.
        
        Args:
            record_data: 기본 정보
            details: 상세 정보 리스트
        
        Returns:
            저장된 레코드의 ID
        """
        with self.get_connection() as conn:
            # 기본 기록 저장
            cursor = conn.execute("""
                INSERT INTO dhr_records 
                (product_lot, product_name, worker, work_date, work_time, total_amount, scale)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data['product_lot'],
                record_data.get('product_name', ''),
                record_data['worker'],
                record_data['work_date'],
                record_data.get('work_time', ''),
                record_data['total_amount'],
                record_data.get('scale', '')
            ))
            
            record_id = cursor.lastrowid
            
            # 상세 기록 저장
            for i, detail in enumerate(details):
                conn.execute("""
                    INSERT INTO dhr_details 
                    (dhr_record_id, material_code, material_name, material_lot, 
                     ratio, theory_amount, actual_amount, sequence_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_id,
                    detail.get('material_code', ''),
                    detail.get('material_name', ''),
                    detail.get('material_lot', ''),
                    detail.get('ratio', 0),
                    detail.get('theory_amount', 0),
                    detail.get('actual_amount', 0),
                    i + 1
                ))
            
            conn.commit()
            logger.info(f"DHR 기록 저장 완료: LOT {record_data['product_lot']}, ID {record_id}")
            return record_id
    
    @handle_exceptions(user_message="DHR 기록 조회 중 오류가 발생했습니다.", default_return=[])
    def get_dhr_records(self, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        limit: int = 100) -> List[Dict]:
        """
        DHR 기록을 조회합니다.
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM dhr_records WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND work_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND work_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            records = [dict(row) for row in cursor.fetchall()]
            
            logger.debug(f"DHR 기록 조회: {len(records)}건")
            return records
    
    @handle_exceptions(user_message="DHR 상세 정보 조회 중 오류가 발생했습니다.", default_return=[])
    def get_dhr_details(self, dhr_record_id: int) -> List[Dict]:
        """특정 DHR 기록의 상세 정보를 조회합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM dhr_details 
                WHERE dhr_record_id = ? 
                ORDER BY sequence_order
            """, (dhr_record_id,))
            
            details = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"DHR 상세 조회: 레코드ID {dhr_record_id}, {len(details)}건")
            return details

    @handle_exceptions(user_message="DHR 기록 조회 중 오류가 발생했습니다.", default_return=None)
    def get_dhr_record_by_lot(self, product_lot: str) -> Optional[Dict]:
        """제품 LOT 번호로 DHR 기록을 조회합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM dhr_records WHERE product_lot = ?", (product_lot,))
            record = cursor.fetchone()

            if record:
                return dict(record)
            return None
    
    @handle_exceptions(user_message="DHR 기록 삭제 중 오류가 발생했습니다.")
    def delete_dhr_record(self, record_id: int) -> bool:
        """DHR 기록을 삭제합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT product_lot FROM dhr_records WHERE id = ?", (record_id,))
            record = cursor.fetchone()

            if not record:
                logger.warning(f"삭제할 DHR 레코드를 찾을 수 없습니다: ID {record_id}")
                return False

            product_lot = record['product_lot']

            # 상세 정보 먼저 삭제
            conn.execute("DELETE FROM dhr_details WHERE dhr_record_id = ?", (record_id,))

            # 기본 레코드 삭제
            conn.execute("DELETE FROM dhr_records WHERE id = ?", (record_id,))

            conn.commit()
            logger.info(f"DHR 기록 삭제 완료: ID {record_id}, LOT {product_lot}")
            return True

    # ========== DHR 레시피 관리 메서드 ==========
    
    @handle_exceptions(user_message="분류 항목 저장 중 오류가 발생했습니다.")
    def add_category(self, category_type: str, value: str) -> int:
        """분류 항목을 추가합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO dhr_recipe_categories (category_type, value)
                VALUES (?, ?)
            """, (category_type, value))
            conn.commit()
            return cursor.lastrowid
    
    @handle_exceptions(user_message="분류 항목 조회 중 오류가 발생했습니다.", default_return=[])
    def get_categories(self, category_type: str) -> List[str]:
        """특정 분류 타입의 모든 값을 조회합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT value FROM dhr_recipe_categories 
                WHERE category_type = ? ORDER BY value
            """, (category_type,))
            return [row['value'] for row in cursor.fetchall()]
    
    @handle_exceptions(user_message="레시피 저장 중 오류가 발생했습니다.")
    def save_recipe(self, recipe_data: Dict, materials: List[Dict]) -> int:
        """DHR 레시피를 저장합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO dhr_recipes 
                (recipe_name, company, product_type, drug, wear_period, default_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_data['recipe_name'],
                recipe_data.get('company', ''),
                recipe_data.get('product_type', ''),
                recipe_data.get('drug', ''),
                recipe_data.get('wear_period', ''),
                recipe_data.get('default_amount', 0)
            ))
            
            recipe_id = cursor.lastrowid
            
            # 자재 목록 저장
            for i, mat in enumerate(materials):
                conn.execute("""
                    INSERT INTO dhr_recipe_materials 
                    (recipe_id, material_code, material_name, ratio, sequence_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    recipe_id,
                    mat.get('material_code', ''),
                    mat.get('material_name', ''),
                    mat.get('ratio', 0),
                    i + 1
                ))
            
            # 분류 마스터에 자동 추가
            for cat_type, value in [
                ('company', recipe_data.get('company')),
                ('product_type', recipe_data.get('product_type')),
                ('drug', recipe_data.get('drug')),
                ('wear_period', recipe_data.get('wear_period'))
            ]:
                if value:
                    conn.execute("""
                        INSERT OR IGNORE INTO dhr_recipe_categories (category_type, value)
                        VALUES (?, ?)
                    """, (cat_type, value))
            
            conn.commit()
            logger.info(f"DHR 레시피 저장 완료: {recipe_data['recipe_name']}, ID {recipe_id}")
            return recipe_id
    
    @handle_exceptions(user_message="레시피 조회 중 오류가 발생했습니다.", default_return=[])
    def get_recipes(self, company: str = None, product_type: str = None, 
                    drug: str = None, wear_period: str = None) -> List[Dict]:
        """조건에 맞는 레시피 목록을 조회합니다."""
        with self.get_connection() as conn:
            query = "SELECT * FROM dhr_recipes WHERE is_active = 1"
            params = []
            
            if company:
                query += " AND company = ?"
                params.append(company)
            if product_type:
                query += " AND product_type = ?"
                params.append(product_type)
            if drug:
                query += " AND drug = ?"
                params.append(drug)
            if wear_period:
                query += " AND wear_period = ?"
                params.append(wear_period)
            
            query += " ORDER BY recipe_name"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @handle_exceptions(user_message="레시피 자재 조회 중 오류가 발생했습니다.", default_return=[])
    def get_recipe_materials(self, recipe_id: int) -> List[Dict]:
        """특정 레시피의 자재 목록을 조회합니다."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM dhr_recipe_materials 
                WHERE recipe_id = ? ORDER BY sequence_order
            """, (recipe_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @handle_exceptions(user_message="레시피 삭제 중 오류가 발생했습니다.")
    def delete_recipe(self, recipe_id: int) -> bool:
        """레시피를 삭제합니다."""
        with self.get_connection() as conn:
            # 자재 목록 먼저 삭제
            conn.execute("DELETE FROM dhr_recipe_materials WHERE recipe_id = ?", (recipe_id,))
            # 레시피 삭제
            conn.execute("DELETE FROM dhr_recipes WHERE id = ?", (recipe_id,))
            conn.commit()
            logger.info(f"DHR 레시피 삭제 완료: ID {recipe_id}")
            return True
    
    @handle_exceptions(user_message="레시피 수정 중 오류가 발생했습니다.")
    def update_recipe(self, recipe_id: int, recipe_data: Dict, materials: List[Dict]) -> bool:
        """레시피를 수정합니다."""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE dhr_recipes SET 
                    recipe_name = ?, company = ?, product_type = ?, 
                    drug = ?, wear_period = ?, default_amount = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                recipe_data['recipe_name'],
                recipe_data.get('company', ''),
                recipe_data.get('product_type', ''),
                recipe_data.get('drug', ''),
                recipe_data.get('wear_period', ''),
                recipe_data.get('default_amount', 0),
                recipe_id
            ))
            
            # 기존 자재 삭제 후 재삽입
            conn.execute("DELETE FROM dhr_recipe_materials WHERE recipe_id = ?", (recipe_id,))
            
            for i, mat in enumerate(materials):
                conn.execute("""
                    INSERT INTO dhr_recipe_materials 
                    (recipe_id, material_code, material_name, ratio, sequence_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    recipe_id,
                    mat.get('material_code', ''),
                    mat.get('material_name', ''),
                    mat.get('ratio', 0),
                    i + 1
                ))
            
            conn.commit()
            logger.info(f"DHR 레시피 수정 완료: ID {recipe_id}")
            return True
