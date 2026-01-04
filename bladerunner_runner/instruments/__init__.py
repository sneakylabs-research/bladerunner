"""Psychological instruments for Bladerunner."""

from .base import BaseInstrument, Question, InstrumentResult
from .levenson import LevensonInstrument
from .bfi import BFIInstrument
from .dark_triad import DarkTriadInstrument
from .phq9 import PHQ9Instrument
from .gad7 import GAD7Instrument
from .phq6_bc import PHQ6BCInstrument
from .phq3_a import PHQ3AInstrument

__all__ = [
    'BaseInstrument',
    'Question',
    'InstrumentResult',
    'LevensonInstrument',
    'BFIInstrument',
    'DarkTriadInstrument',
    'PHQ9Instrument',
    'GAD7Instrument',
    'PHQ6BCInstrument',
    'PHQ3AInstrument',
    'get_instrument',
    'list_instruments',
]

# Registry of available instruments
_INSTRUMENTS = {
    'levenson': LevensonInstrument,
    'bfi': BFIInstrument,
    'dark_triad': DarkTriadInstrument,
    'phq9': PHQ9Instrument,
    'gad7': GAD7Instrument,
    'phq6_bc': PHQ6BCInstrument,
    'phq3_a': PHQ3AInstrument,
}


def get_instrument(name: str) -> BaseInstrument:
    """Get instrument instance by name."""
    if name not in _INSTRUMENTS:
        raise ValueError(f"Unknown instrument: {name}. Available: {list(_INSTRUMENTS.keys())}")
    return _INSTRUMENTS[name]()


def list_instruments() -> list:
    """List available instrument names."""
    return list(_INSTRUMENTS.keys())
