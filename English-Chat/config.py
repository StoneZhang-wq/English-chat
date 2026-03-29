import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件（使用绝对路径确保找到）
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def _get_env_bool(key: str, default: bool) -> bool:
    """从环境变量读取布尔值，支持 true/false、1/0 等"""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


def _get_env_int(key: str, default: int) -> int:
    """读取整数环境变量"""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_env_str(key: str, default: str) -> str:
    """读取字符串环境变量，None 时返回默认值"""
    val = os.getenv(key)
    return val if val is not None else default


@dataclass
class Config:
    # 服务器设置
    server_host: str = "0.0.0.0"
    server_port: int = 8080

    # LLM设置
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "doubao-seed-2-0-mini-260215"
    openai_vl_model: str = "gpt-4o-mini"

    google_api_key: Optional[str] = None

    # 数据库存储设置
    db_host: Optional[str] = "mysql"
    db_name: Optional[str] = "notex"
    db_user: Optional[str] = "notex_user"
    db_password: Optional[str] = "123456"
    db_root_password: Optional[str] = None
    db_port: int = 3306

    # 缓存存储设置（Railway 等平台常提供 REDIS_URL 整串，优先使用）
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    # 日志设置
    log_path: str = "./logs/notex.log"
    log_level: str = "info"

    # 数据保存路径
    data_path: str = "./data"

    # 特征库路径
    characters_folder: str = "./characters"

    default_characters: str = "english_tutor"

    # ASR：doubao（火山录音文件识别）| local（faster-whisper 本地文件）
    asr_provider: str = "doubao"
    local_whisper_model_size: str = "base"
    local_whisper_device: str = "cpu"
    local_whisper_compute_type: str = "int8"
    # 留空则自动检测语言；可设为 en 等强制识别语言
    local_whisper_language: str = ""
    asr_concurrency_limit: int = 2

    # 豆包 TTS 配置
    # tts_provider: doubao | piper（Piper 需本机安装 piper 可执行文件与 .onnx 模型）
    tts_provider: str = "doubao"
    volcengine_app_id: Optional[str] = None
    volcengine_access_token: Optional[str] = None
    tts_endpoint: str = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"
    tts_voice_type: str = "en_male_smith_mars_bigtts"
    tts_voice_type_b: str = "en_female_sarah_mars_bigtts"
    tts_voice_type_zh: str = "zh_female_cancan_mars_bigtts"
    tts_encoding: str = "mp3"
    # TTS 并发上限，避免触发豆包「quota exceeded for types: concurrency」
    tts_concurrency_limit: int = 2

    # 豆包 ASR（录音文件识别）
    volcengine_asr_app_id: Optional[str] = None
    volcengine_asr_access_token: Optional[str] = None
    volcengine_file_asr_resource_id: str = "volc.bigasr.auc"
    # 火山引擎 ASR 接口 base（submit/query 请求发往此地址），与 public_app_url 无关
    volcengine_asr_base_url: str = "https://openspeech.bytedance.com"
    # 豆包 ASR 拉取临时音频用的地址，须为本应用公网可访问；未配置时回退为请求 base_url
    public_app_url: str = ""

    # Piper TTS：可执行文件路径或命令名；英文/中文/B 角色 .onnx 模型路径（.onnx.json 需同目录）
    piper_executable: str = "piper"
    piper_voice_en: str = ""
    piper_voice_en_b: str = ""
    piper_voice_zh: str = ""


def load_config() -> Config:
    """从环境变量加载配置，并返回 Config 实例"""
    conf = Config()

    # 从环境变量覆盖默认值
    conf.server_host = _get_env_str("SERVER_HOST", conf.server_host)
    # Railway / Heroku 等平台注入 PORT，必须使用该端口才能正常响应
    _port = os.getenv("PORT") or os.getenv("SERVER_PORT")
    if _port is not None:
        try:
            conf.server_port = int(_port)
        except ValueError:
            conf.server_port = _get_env_int("SERVER_PORT", conf.server_port)
    else:
        conf.server_port = _get_env_int("SERVER_PORT", conf.server_port)

    conf.openai_api_key = _get_env_str("OPENAI_API_KEY", conf.openai_api_key)
    conf.openai_base_url = _get_env_str("OPENAI_BASE_URL", conf.openai_base_url)
    conf.openai_model = _get_env_str("OPENAI_MODEL", conf.openai_model)

    conf.google_api_key = _get_env_str("GOOGLE_API_KEY", conf.google_api_key)

    conf.db_name = _get_env_str("DB_NAME", conf.db_name)
    conf.db_host = _get_env_str("DB_HOST", conf.db_host)
    conf.db_user = _get_env_str("DB_USER", conf.db_user)
    conf.db_password = _get_env_str("DB_PASSWORD", conf.db_password)
    conf.db_root_password = os.getenv("DB_ROOT_PASSWORD") or conf.db_root_password
    conf.db_port = _get_env_int("DB_PORT", conf.db_port)

    conf.redis_url = os.getenv("REDIS_URL") or None
    if not conf.redis_url:
        conf.redis_host = _get_env_str("REDIS_HOST", conf.redis_host)
        conf.redis_port = _get_env_int("REDIS_PORT", conf.redis_port)
        conf.redis_password = _get_env_str("REDIS_PASSWORD", "") or None

    conf.log_path = _get_env_str("LOG_PATH", conf.log_path)
    conf.log_level = _get_env_str("LOG_LEVEL", conf.log_level)

    conf.data_path = _get_env_str("DATA_PATH", conf.data_path)
    conf.characters_folder = _get_env_str("CHARACTER_PATH", conf.characters_folder)
    conf.default_characters = _get_env_str("CHARACTER_NAME", conf.default_characters)

    conf.asr_provider = _get_env_str("ASR_PROVIDER", conf.asr_provider)
    conf.local_whisper_model_size = _get_env_str("LOCAL_WHISPER_MODEL_SIZE", conf.local_whisper_model_size)
    conf.local_whisper_device = _get_env_str("LOCAL_WHISPER_DEVICE", conf.local_whisper_device)
    conf.local_whisper_compute_type = _get_env_str("LOCAL_WHISPER_COMPUTE_TYPE", conf.local_whisper_compute_type)
    conf.local_whisper_language = _get_env_str("LOCAL_WHISPER_LANGUAGE", conf.local_whisper_language)
    conf.asr_concurrency_limit = _get_env_int("ASR_CONCURRENCY_LIMIT", conf.asr_concurrency_limit)

    # 豆包 TTS
    conf.tts_provider = _get_env_str("TTS_PROVIDER", conf.tts_provider)
    conf.volcengine_app_id = _get_env_str("VOLCENGINE_APP_ID", "") or None
    conf.volcengine_access_token = _get_env_str("VOLCENGINE_ACCESS_TOKEN", "") or None
    conf.tts_endpoint = _get_env_str("TTS_ENDPOINT", conf.tts_endpoint)
    conf.tts_voice_type = _get_env_str("TTS_VOICE_TYPE", conf.tts_voice_type)
    conf.tts_voice_type_b = _get_env_str("TTS_VOICE_TYPE_B", conf.tts_voice_type_b)
    conf.tts_voice_type_zh = _get_env_str("TTS_VOICE_TYPE_ZH", conf.tts_voice_type_zh)
    conf.tts_encoding = _get_env_str("TTS_ENCODING", conf.tts_encoding)
    conf.tts_concurrency_limit = _get_env_int("TTS_CONCURRENCY_LIMIT", conf.tts_concurrency_limit)

    # 豆包 ASR
    conf.volcengine_asr_app_id = _get_env_str("VOLCENGINE_ASR_APP_ID", "") or None
    conf.volcengine_asr_access_token = _get_env_str("VOLCENGINE_ASR_ACCESS_TOKEN", "") or None
    conf.volcengine_file_asr_resource_id = _get_env_str("VOLCENGINE_FILE_ASR_RESOURCE_ID", conf.volcengine_file_asr_resource_id)
    conf.volcengine_asr_base_url = _get_env_str("VOLCENGINE_ASR_BASE_URL", conf.volcengine_asr_base_url or "").strip().rstrip("/") or "https://openspeech.bytedance.com"
    _pub = _get_env_str("PUBLIC_APP_URL", conf.public_app_url or "").strip().rstrip("/")
    conf.public_app_url = _pub

    conf.piper_executable = _get_env_str("PIPER_EXECUTABLE", conf.piper_executable)
    conf.piper_voice_en = _get_env_str("PIPER_VOICE_EN", conf.piper_voice_en)
    conf.piper_voice_en_b = _get_env_str("PIPER_VOICE_EN_B", conf.piper_voice_en_b)
    conf.piper_voice_zh = _get_env_str("PIPER_VOICE_ZH", conf.piper_voice_zh)

    # 验证配置
    validate_config(conf)

    return conf


def validate_config(config: Config) -> None:
    """验证配置有效性"""
    has_openai = bool(config.openai_api_key)

    if not has_openai:
        raise ValueError("必须设置 OPENAI_API_KEY 或 OLLAMA_BASE_URL")


# 导出单例
configer = load_config()