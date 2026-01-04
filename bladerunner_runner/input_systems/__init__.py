"""Input systems for personality programming."""

from .base import BaseInputSystem
from .ocean_direct import OceanDirectSystem
from .narrative import NarrativeSystem
from .hexaco import HexacoSystem
from .behavioral import BehavioralSystem
from .scenario import ScenarioSystem
from .exemplar import ExemplarSystem

__all__ = [
    'BaseInputSystem',
    'OceanDirectSystem',
    'NarrativeSystem',
    'HexacoSystem',
    'BehavioralSystem',
    'ScenarioSystem',
    'ExemplarSystem',
    'get_input_system',
    'list_input_systems',
]

# Registry of available input systems
_SYSTEMS = {
    'ocean_direct': OceanDirectSystem,
    'narrative': NarrativeSystem,
    'hexaco': HexacoSystem,
    'behavioral': BehavioralSystem,
    'scenario': ScenarioSystem,
    'exemplar': ExemplarSystem,
}


def get_input_system(name: str) -> BaseInputSystem:
    """Get input system instance by name."""
    if name not in _SYSTEMS:
        raise ValueError(f"Unknown input system: {name}. Available: {list(_SYSTEMS.keys())}")
    return _SYSTEMS[name]()


def list_input_systems() -> list:
    """List available input system names."""
    return list(_SYSTEMS.keys())
