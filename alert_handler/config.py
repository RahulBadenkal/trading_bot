import os

from dotenv import load_dotenv

from common.base_config import BaseConfig


class Config(BaseConfig):
    db_max_batch_size: int

    @staticmethod
    async def init():
        curr_dir_path = os.path.dirname(__file__)
        load_dotenv(os.path.join(curr_dir_path, '../.env_common'))  # Common dotenv
        load_dotenv(os.path.join(curr_dir_path, '../.env_alert_handler'))  # App specific dotenv

        # Call the base config init
        await super(Config, Config).init()

        Config.db_max_batch_size = int(os.getenv("DB_MAX_BATCH_SIZE"))

