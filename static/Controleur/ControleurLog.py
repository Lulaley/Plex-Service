from .ControleurConf import ControleurConf
import logging

def write_log(message):
    # Get the configuration
    log_file_path = ControleurConf.get_config('log', 'file')
    log_level = ControleurConf.get_config('log', 'level')

    # Perform the log writing logic here
    try:
        logging.basicConfig(filename=log_file_path, level=log_level)
        logging.info(message)
    except Exception as e:
        print(f"Error occurred while writing log: {str(e)}")
