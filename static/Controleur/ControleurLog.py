from .ControleurConf import ControleurConf
import logging

def write_log(message):
    # Get the configuration
    conf = ControleurConf()
    log_file_path = conf.get_config('LOG', 'file')
    log_level = conf.get_config('LOG', 'level')

    # Perform the log writing logic here
    try:
        logging.basicConfig(filename=log_file_path, level=log_level)
        logging.info(message)
    except Exception as e:
        print(f"Error occurred while writing log: {str(e)}")
