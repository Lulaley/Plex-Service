import logging
import inspect
from flask import session
from .ControleurConf import ControleurConf

def write_log(message, log_level=None, username=None):
    # Get the configuration
    conf = ControleurConf()
    log_file_path = conf.get_config('LOG', 'file')
    
    # Use the provided log_level or fall back to the default from the configuration
    if log_level is None:
        log_level = conf.get_config('LOG', 'level').upper()
    else:
        log_level = log_level.upper()

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

    # Add username to the log message if available
    if username:
        message = f"{username} - {message}"

    # Perform the log writing logic here
    try:
        # Ensure the log level is valid
        if log_level not in log_levels:
            raise ValueError(f"Invalid log level: {log_level}")

        # Create a logger
        logger = logging.getLogger(caller_function)
        logger.setLevel(log_levels[log_level])

        # Check if the logger already has handlers
        if not logger.handlers:
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
