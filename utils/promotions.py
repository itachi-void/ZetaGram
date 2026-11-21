import math
from typing import Optional, Tuple
from sqlalchemy import select, and_

from database.models import FlashEvent, PromoCode, PromoCodeRedemption
from utils.html_utils import utcnow


async def get_active_flash_event(session, now=None) -> Optional[FlashEvent]:
    """Return the currently active FlashEvent with the highest multiplier_pct, if any."""
    now = now or utcnow()
    stmt = (
        select(FlashEvent)
        .where(
            and_(
                FlashEvent.is_active == True,
                FlashEvent.starts_at <= now,
                FlashEvent.ends_at > now,
            )
        )
        .order_by(FlashEvent.multiplier_pct.desc(), FlashEvent.id.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def format_multiplier(multiplier_pct: int) -> str:
    """Format an integer percentage multiplier (e.g. 200 -> '2x', 150 -> '1.5x')."""
    val = multiplier_pct / 100.0
    if abs(val - round(val)) < 1e-6:
        return f"{int(round(val))}x"
    return f"{val:.1f}x"


async def validate_promo_code(
    session, user_id: int, code: str, base_cost: int, now=None
) -> Tuple[bool, Optional[PromoCode], str]:
    """
    Validate an advertiser promo code against expiration, usage cap,
    minimum order size, and prior redemption by the same user.
    Returns (is_valid, promo_obj_or_None, i18n_error_key).
    """
    now = now or utcnow()
    norm_code = (code or "").strip().upper()
    if not norm_code:
        return False, None, "promo_err_invalid"

    promo = (
        await session.execute(select(PromoCode).where(PromoCode.code == norm_code))
    ).scalar_one_or_none()

    if not promo or not promo.is_active:
        return False, None, "promo_err_invalid"

    if promo.expires_at and now >= promo.expires_at:
        return False, None, "promo_err_expired"

    if (promo.used_count or 0) >= (promo.max_uses or 0):
        return False, None, "promo_err_exhausted"

    if base_cost < (promo.min_order_grams or 0):
        return False, promo, "promo_err_min_order"

    existing_redemption = (
        await session.execute(
            select(PromoCodeRedemption.id).where(
                and_(
                    PromoCodeRedemption.promo_code_id == promo.id,
                    PromoCodeRedemption.user_id == user_id,
                )
            )
        )
    ).scalar_one_or_none()
    if existing_redemption:
        return False, None, "promo_err_already_used"

    return True, promo, ""


def calculate_campaign_pricing(
    base_cost: int, fee_rate: float, promo: Optional[PromoCode]
) -> dict:
    """
    Compute campaign cost breakdown with optional PromoCode discount.
    Prevents cancel-refund arbitrage on 'total'-scoped discounts by tracking
    platform-subsidized discount (promo_subsidy).
    """
    original_commission = math.ceil(base_cost * fee_rate) if fee_rate > 0 else 0
    original_total = base_cost + original_commission

    if not promo:
        return {
            "base_cost": base_cost,
            "original_commission": original_commission,
            "original_total": original_total,
            "discount": 0,
            "commission_paid": original_commission,
            "final_total": original_total,
            "promo_subsidy": 0,
        }

    scope = (promo.discount_scope or "commission").lower()
    if scope == "total":
        pct = min(max(int(promo.discount_percent), 1), 50)
        discount = int(original_total * pct / 100)
        final_total = max(1, original_total - discount)
        actual_discount = original_total - final_total
        commission_paid = max(0, original_commission - actual_discount)
        promo_subsidy = max(0, actual_discount - original_commission)
    else:
        pct = min(max(int(promo.discount_percent), 1), 100)
        discount = (
            min(original_commission, math.ceil(original_commission * pct / 100))
            if original_commission > 0
            else 0
        )
        commission_paid = original_commission - discount
        final_total = base_cost + commission_paid
        actual_discount = discount
        promo_subsidy = 0

    return {
        "base_cost": base_cost,
        "original_commission": original_commission,
        "original_total": original_total,
        "discount": actual_discount,
        "commission_paid": commission_paid,
        "final_total": final_total,
        "promo_subsidy": promo_subsidy,
    }
