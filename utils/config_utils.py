# config_utils.py
import logging
import os

import yaml

from utils.tools import load_yaml_config

logger = logging.getLogger(__name__)
current_directory = os.getcwd()
config_path = os.path.join(current_directory, 'config.yaml')


class Config:
    """统一的配置类，集中管理所有常量"""
    config = load_yaml_config()
    # Chroma 数据库配置
    CHROMADB_DIRECTORY = config['database'].get('CHROMADB_DIRECTORY', 'chromaDB')
    CHROMADB_COLLECTION_NAME = config['database'].get('CHROMADB_COLLECTION_NAME', 'demo001')

    # 日志持久化存储
    LOG_FILE = config['log'].get('LOG_FILE', 'log/app.log')
    MAX_BYTES = int(config['database'].get('MAX_BYTES', '5e6'))
    BACKUP_COUNT = int(config['database'].get('BACKUP_COUNT', '3'))

    # 数据库 URI，默认值
    DB_URI = config['database'].get('DB_URI', 'postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable')

    # openai:调用gpt模型,oneapi:调用oneapi方案支持的模型,ollama:调用本地开源大模型,qwen:调用阿里通义千问大模型
    LLM_TYPE = "openai"

    # API服务地址和端口
    HOST = config['api'].get('HOST', 'localhost')
    PORT = config['api'].get('PORT', '8012')

    def load_yaml_config(self, config_file=config_path):
        """
        加载 YAML 文件中的配置。
        """
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)  # 安全加载 YAML 文件
            return config
        except FileNotFoundError:
            logger.error(f"Error: YAML file not found at {config_file}")

    def load_yaml_to_env(self, yaml_path=config_path):
        """
        加载 YAML 文件中的配置到环境变量。
        """
        try:
            config = self.load_yaml_config(yaml_path)

            if isinstance(config, dict):
                for key, value in config.items():
                    # 将键和值都转换为字符串，以确保兼容性
                    os.environ[str(key)] = str(value)
                logger.info(f"Successfully loaded config into environment variables.")
            else:
                logger.warning(f"Warning: yaml does not contain a dictionary at the top level.")

        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
