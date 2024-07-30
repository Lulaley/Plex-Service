import logging
import inspect
from .ControleurConf import ControleurConf

def write_log(message):
    # Get the configuration
    conf = ControleurConf()
    log_file_path = conf.get_config('LOG', 'file')
    log_level = conf.get_config('LOG', 'level').upper()

    # Map string log levels to logging module constants
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # Get the name of the calling function
    caller_function = inspect.stack()[1].function

    # Perform the log writing logic here
    try:
        # Ensure the log level is valid
        if log_level not in log_levels:
            raise ValueError(f"Invalid log level: {log_level}")

        # Create a logger
        logger = logging.getLogger(caller_function)
        logger.setLevel(log_levels[log_level])

        # Create file handler
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(log_levels[log_level])

        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(fh)

        # Log the message with the caller function
        logger.log(log_levels[log_level], f"{message}")

    except Exception as e:
        print(f"Failed to write log: {e}")
