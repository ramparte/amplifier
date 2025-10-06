"""
Shared Ideas Management System

A hybrid code/AI system for managing project ideas with natural language goals,
per-person assignment queues, and LLM-powered operations like reordering and theme detection.
"""

from . import cli
from . import models
from . import operations
from . import storage

__version__ = "1.0.0"
__all__ = ["storage", "operations", "cli", "models"]
