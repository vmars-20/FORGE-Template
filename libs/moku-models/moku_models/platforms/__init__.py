"""
Moku Platform Physical Models

Hardware specifications for different Moku platforms (Go, Lab, Pro, Delta).
"""

from moku_models.platforms.moku_go import MokuGoPlatform, MOKU_GO_PLATFORM
from moku_models.platforms.moku_lab import MokuLabPlatform, MOKU_LAB_PLATFORM
from moku_models.platforms.moku_pro import MokuProPlatform, MOKU_PRO_PLATFORM
from moku_models.platforms.moku_delta import MokuDeltaPlatform, MOKU_DELTA_PLATFORM

__all__ = [
    'MokuGoPlatform',
    'MOKU_GO_PLATFORM',
    'MokuLabPlatform',
    'MOKU_LAB_PLATFORM',
    'MokuProPlatform',
    'MOKU_PRO_PLATFORM',
    'MokuDeltaPlatform',
    'MOKU_DELTA_PLATFORM',
]
