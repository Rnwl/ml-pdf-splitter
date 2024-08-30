import logging
import os

from dotenv import load_dotenv


def load_variable(variable_name: str, logger=None) -> str:
    if logger is None:
        logger = logging.getLogger(__name__)
    variable = os.getenv(variable_name)
    if variable is None:
        load_dotenv()
        variable = os.getenv(variable_name)
        if variable is None:
            logger.error(
                f"{variable_name} not found in environment variables or .env file."
            )
            raise ValueError(
                f"{variable_name} not found in environment variables or .env file."
            )
        else:
            logger.info(f"Loaded {variable_name} from .env file.")
    else:
        logger.info(f"Loaded {variable_name} from environment variables.")
    return variable
