import unittest
import sys
import os

def run_tests():
    # 프로젝트 루트를 path에 추가 (tests 폴더 상위의 상위, 즉 v3/main)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)

    # 테스트 로더 및 스위트
    loader = unittest.TestLoader()
    start_dir = current_dir
    suite = loader.discover(start_dir, pattern='test_*.py')

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 실패 시 exit code 1
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_tests()
