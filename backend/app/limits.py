"""Application tier limits configuration."""

from app.models.user import UserTier

TIER_LIMITS = {
    UserTier.free: {
        "max_dynamic_qrs": 5,
        "max_scans_per_month": 200,
    },
    UserTier.pro: {
        "max_dynamic_qrs": 100,
        "max_scans_per_month": 10000,
    },
    UserTier.enterprise: {
        "max_dynamic_qrs": -1,
        "max_scans_per_month": -1,
    },
}

