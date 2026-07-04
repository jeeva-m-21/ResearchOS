"""Experiment context"""
from uuid import UUID
from typing import Optional

class Experiment:
    """Experiment context manager"""
    
    def __init__(self, name: str, project: str = None):
        self.name = name
        self.project = project
        self._started = False
    
    def __enter__(self):
        # TODO: Initialize experiment
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Finish experiment
        pass
