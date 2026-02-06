"""

諛고빀 ?꾨줈洹몃옩 ?ㅼ젙 ?뚯씪

紐⑤뱺 ?ㅼ젙媛믩뱾???ш린??愿由ы빀?덈떎.

"""

import os

import sys



# 湲곕낯 寃쎈줈 ?ㅼ젙
if getattr(sys, 'frozen', False):
    # ?ㅽ뻾 ?뚯씪濡?留뚮뱾?댁죱????
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # ?뚯씠???ㅽ겕由쏀듃濡??ㅽ뻾????
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = "MixingProgram"


def _resolve_user_data_dir():
    """
    ?ㅽ겕由쏀듃媛? 異붿텧?섏뿬 寃쎈줈媛 嫄곕━?쒗븯?댁슂?섎㈃,
    ?뺤젣媛 ?댁긽??삤瑜??⑸땲???뚮┝??寃쎈줈瑜??꾪븳??寃쎈줈瑜??좊븣???덈떎.
    """
    candidates = []

    env_override = os.environ.get("MIXING_APP_DATA_DIR")
    if env_override:
        candidates.append(env_override)

    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if local_appdata:
            candidates.append(os.path.join(local_appdata, APP_NAME))

    home_dir = os.path.expanduser("~")
    if home_dir:
        candidates.append(os.path.join(home_dir, f".{APP_NAME.lower()}"))

    candidates.append(os.path.join(BASE_PATH, "data"))

    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            continue
    return BASE_PATH


USER_DATA_DIR = _resolve_user_data_dir()
USER_CONFIG_DIR = os.path.join(USER_DATA_DIR, "config")
USER_LOG_DIR = os.path.join(USER_DATA_DIR, "logs")
USER_OUTPUT_DIR = os.path.join(USER_DATA_DIR, "output")
os.makedirs(USER_CONFIG_DIR, exist_ok=True)
os.makedirs(USER_LOG_DIR, exist_ok=True)



# ?대뜑 寃쎈줈??(瑜섍꼍 媛쒖닔?섎뒗 寃쎈줈)
RESOURCES_FOLDER = os.path.join(BASE_PATH, "resources")

# ?뚯씪 寃쎈줈??
RECIPE_FILE = os.path.join(RESOURCES_FOLDER, "레시피.xlsx")
RECORD_FILE = os.path.join(RESOURCES_FOLDER, "諛고빀湲곕줉.xlsx")
TEMPLATE_FILE = os.path.join(RESOURCES_FOLDER, "원료배합일지_DHR.xlsx")
LOT_FILE = os.path.join(RESOURCES_FOLDER, "OUT.xlsx")

# DB/紐⑤뱺 由щ럭寃쎈줈(?뚯씪?먮쭔 ?꾩껜媛믪쓣 USER_DATA_DIR ?ㅻⅨ)
LEGACY_DB_PATH = os.path.join(BASE_PATH, "resources", "mixing_records.db")
DB_FILE = os.path.join(USER_DATA_DIR, "mixing_records.db")


# ?묒? ? 留ㅽ븨 ?뺣낫

CELL_MAPPING = {

    'date': 'A3',

    'scale': 'A4',

    'worker': 'C3',

    'work_time': 'E3',

    'product_lot': 'A6',

    'total_amount': 'B6',

    'data_start_row': 6,

    'material_name_col': 'C',

    'material_lot_col': 'D',

    'ratio_col': 'E',

    'theory_amount_col': 'F',

    'actual_amount_col': 'G'

}



# ?ㅼ젙 愿由ъ옄?먯꽌 媛믪쓣 媛?몄삤???⑥닔??
def get_default_scale():

    from config.config_manager import config

    return config.default_scale



def get_tolerance():

    from config.config_manager import config

    return config.tolerance



def get_cell_mapping():

    from config.config_manager import config

    return config.get("excel.cell_mapping", CELL_MAPPING)



# ?섏쐞 ?명솚?깆쓣 ?꾪븳 ?곸닔??(deprecation ?덉젙)
DEFAULT_SCALE = 'M-65'
TOLERANCE = 0.05  # ?덉슜 ?ㅼ감 踰붿쐞

# ?꾩슂???대뜑?ㅼ씠 ?놁쑝硫?留뚮뱾湲?
os.makedirs(RESOURCES_FOLDER, exist_ok=True)
os.makedirs(USER_OUTPUT_DIR, exist_ok=True)


# --- Robust path resolution for non-ASCII filenames ---
def _first_existing(paths, create_dir=False):
    for p in paths:
        if os.path.exists(p):
            return p
    if create_dir and paths:
        os.makedirs(paths[0], exist_ok=True)
        return paths[0]
    return paths[0] if paths else None


# Prefer the canonical Korean-named folder if present; otherwise use ASCII 'output'
_output_candidates = [
    os.path.join(USER_DATA_DIR, "실적서"),
    os.path.join(USER_DATA_DIR, "output"),
    os.path.join(BASE_PATH, "실적서"),  # legacy fallback
    os.path.join(BASE_PATH, "output"),
]
OUTPUT_FOLDER = _first_existing(_output_candidates, create_dir=True)
LOG_FOLDER = USER_LOG_DIR

# Resolve known Excel resource files even if the file names vary
_recipe_candidates = [
    os.path.join(RESOURCES_FOLDER, "레시피.xlsx"),
]
RECIPE_FILE = _first_existing(_recipe_candidates)
if not os.path.exists(RECIPE_FILE or ""):
    # Fallback: scan for a likely recipe file
    for name in os.listdir(RESOURCES_FOLDER):
        lower = name.lower()
        if lower.endswith(".xlsx") and ("recipe" in lower or "레시" in lower):
            RECIPE_FILE = os.path.join(RESOURCES_FOLDER, name)
            break

_template_candidates = [
    os.path.join(RESOURCES_FOLDER, "원료배합일지_DHR.xlsx"),
]
TEMPLATE_FILE = _first_existing(_template_candidates)
if not os.path.exists(TEMPLATE_FILE or ""):
    # Fallback: pick any *DHR.xlsx template
    for name in os.listdir(RESOURCES_FOLDER):
        lower = name.lower()
        if lower.endswith(".xlsx") and ("dhr" in lower):
            TEMPLATE_FILE = os.path.join(RESOURCES_FOLDER, name)
            break
