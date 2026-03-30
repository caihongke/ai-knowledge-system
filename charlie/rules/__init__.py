"""查理编剧体系 - 规则层"""

from .five_iron_laws import FiveIronLaws, quick_check_five_laws, CheckResult
from .causality_lock import CausalityLock, quick_check_causality
from .secret_pressure import SecretPressure, quick_check_secret_pressure
from .rhythm_redline import RhythmRedline, quick_check_rhythm
from .industrial_rules import IndustrialRules, quick_check_industrial

__all__ = [
    # 五大铁律
    "FiveIronLaws",
    "quick_check_five_laws",
    "CheckResult",
    # 扩展规则
    "CausalityLock",
    "quick_check_causality",
    "SecretPressure",
    "quick_check_secret_pressure",
    "RhythmRedline",
    "quick_check_rhythm",
    "IndustrialRules",
    "quick_check_industrial",
]