from abc import ABC, abstractmethod
from typing import Callable

class BaseEngine(ABC):
    @abstractmethod
    def convert(self, input_path: str, output_path: str, progress_callback: Callable[[float, str], None] = None):
        """
        Convert input_path to output_path.
        progress_callback: function(progress_0_100, status_message)
        """
        pass
    
    @abstractmethod
    def cancel(self):
        """
        Cancel the current operation.
        """
        pass
