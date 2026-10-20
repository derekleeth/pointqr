"""Application tier limits configuration."""

from app.models.user import UserTier

TIER_LIMITS = {
    UserTier.free: {
        "max_dynamic_qrs": 3,
        "max_scans_per_month": 300,
    },
    UserTier.pro: {
        "max_dynamic_qrs": 100,
        "max_scans_per_month": 10000,
    },
    UserTier.max: {
        "max_dynamic_qrs": 1000,
        "max_scans_per_month": -1,
    },
}

