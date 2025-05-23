import time
import logging
import os
import sys
import traceback

class TimedLogger:
    def __init__(self,
                filename: str = None,
                format: str = "%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d",
                datefmt: str = "%Y-%m-%d %H:%M:%S",
                name: str = __name__):

        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        handlers = [stdout_handler]
        if filename and os.getenv("ENABLE_FILE_LOGS", "false").lower() == "true":
            handlers.append(logging.FileHandler(filename=filename))
        logging.basicConfig(
            level=logging.INFO,
            format=format,
            datefmt=datefmt,
            handlers=handlers,
        )
        self.logger = logging.getLogger(name)
        self.logger.info(f"Logger initialised for {name}")
        self.start_time = time.time()
        self.function_starts = {}
        self.function_times = {}

    @property
    def elapsed(self):
        duration = time.time() - self.start_time
        return duration

    @property
    def seconds(self):
        return f'{round(self.elapsed, 2)} seconds'

    def info(self, text):
        self.logger.info(text + f' Time passed: {self.seconds}.')

    def error(self, text):
        self.logger.error(text + f' Time passed: {self.seconds}.')
        self.logger.error(traceback.format_exc())

    def start_function(self, function_name):
        self.function_starts[function_name] = time.time()

    def end_function(self, function_name):
        self.function_times[function_name] = time.time() - self.function_starts[function_name]


    def time_function(self, func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            func_list = list(filter(lambda x: func_name in x, list(self.function_starts.keys()))) # Get all iters of functions with the same name
            if len(func_list) > 0:
                func_iter = sorted([int(func_str.split('_')[-1]) for func_str in func_list])[-1] + 1 # Get the highest iter and add 1
            else:
                func_iter = 0
            func_name += f'_{func_iter}'
            self.start_function(func_name)
            result = func(*args, **kwargs)
            self.end_function(func_name)
            return result
        return wrapper
    
    def print_function_times(self):
        for function_name, time_taken in self.function_times.items():
            self.logger.info(f"Function {function_name} took {time_taken} seconds.")

    def reset_times(self):
        self.function_starts = {}
        self.function_times = {}
        self.start_time = time.time()
