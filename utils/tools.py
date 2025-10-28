import json
import logging
import os

import yaml

logger = logging.getLogger(__name__)
current_directory = os.getcwd()
config_path = os.path.join(current_directory, 'config.yaml')

def load_yaml_config(config_file=config_path):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)  # 安全加载 YAML 文件
        return config
    except FileNotFoundError:
        logger.error(f"Error: YAML file not found at {config_file}")


def load_yaml_to_env(yaml_path=config_path):
    """
    加载 YAML 文件中的配置到环境变量。
    """
    try:
        config = load_yaml_config(yaml_path)

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

def tools_list_to_dict(tool_list):
    processed_dict = {}
    for item in tool_list:
        # mcp tools
        if hasattr(item, 'name') and hasattr(item, 'coroutine'):
            processed_dict[item.name] = item
            # processed_dict[item.name] = item.coroutine
        # other tools
        else:
            processed_dict[item['name']] = item
    return processed_dict


def message_to_dict(messages):
    response = messages.model_dump_json(indent=4, exclude_none=True)
    response = json.loads(response)
    return response

if __name__ == "__main__":
    load_yaml_to_env()