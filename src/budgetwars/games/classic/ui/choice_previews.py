from __future__ import annotations


def _money(value: int) -> str:
    return f"${value:,}"


def _format_preview(base: str, effects: list[str]) -> str:
    effects = [item for item in effects if item]
    if not effects:
        return base
    return f"{base} Likely changes: {', '.join(effects)}."


def _signed_label(value: int, label: str, *, unit: str = "") -> str | None:
    if value == 0:
        return None
    suffix = unit or ""
    return f"{label} {value:+d}{suffix}"


def _percent_label(value: float, label: str) -> str | None:
    if value == 0:
        return None
    sign = "+" if value >= 0 else ""
    return f"{label} {sign}{value * 100:.0f}%"


def _career_preview(track) -> str:
    tier = track.tiers[0]
    effects = [
        f"income starts at {_money(tier.monthly_income)}/mo",
        _signed_label(tier.stress_delta, "stress"),
        _signed_label(tier.energy_delta, "energy"),
        _signed_label(tier.life_satisfaction_delta, "life"),
        f"promotion target {tier.promotion_target}",
    ]
    return _format_preview(track.description, [effect for effect in effects if effect])


def _career_branch_preview(branch) -> str:
    effects = [
        _percent_label(branch.income_multiplier - 1.0, "income"),
        _signed_label(branch.stress_delta, "stress"),
        _signed_label(branch.energy_delta, "energy"),
        _signed_label(branch.promotion_progress_bonus, "promo"),
        _signed_label(branch.layoff_pressure_delta, "layoff pressure"),
    ]
    if branch.min_transport_reliability is not None:
        effects.append(f"transport {branch.min_transport_reliability}+")
    if branch.min_social_stability is not None:
        effects.append(f"social {branch.min_social_stability}+")
    if branch.min_energy is not None:
        effects.append(f"energy floor {branch.min_energy}+")
    if branch.max_stress is not None:
        effects.append(f"stress cap {branch.max_stress}")
    return _format_preview(branch.description, [effect for effect in effects if effect])


def _housing_preview(option) -> str:
    effects = [
        f"rent {_money(option.base_monthly_cost)}/mo",
        _signed_label(option.stress_delta, "stress"),
        _signed_label(option.life_satisfaction_delta, "life"),
        _signed_label(option.social_stability_delta, "social"),
    ]
    if option.minimum_credit_score:
        effects.append(f"credit gate {option.minimum_credit_score}+")
    return _format_preview(option.description, [effect for effect in effects if effect])


def _transport_preview(option, upfront: int, monthly: int) -> str:
    effects = [
        f"upfront {_money(upfront)}",
        f"monthly {_money(monthly)}",
        f"access {option.access_level}",
        f"reliability {option.reliability * 100:.0f}%",
        _signed_label(option.commute_stress_delta, "commute stress"),
    ]
    if option.minimum_credit_score:
        effects.append(f"credit gate {option.minimum_credit_score}+")
    return _format_preview(option.description, [effect for effect in effects if effect])


def _budget_preview(stance) -> str:
    effects = [
        f"debt payment x{stance.debt_payment_multiplier:.2f}",
        f"savings {stance.savings_contribution_rate * 100:.0f}%",
        _signed_label(stance.stress_delta, "stress"),
        _signed_label(stance.energy_delta, "energy"),
        _signed_label(stance.life_satisfaction_delta, "life"),
        _signed_label(stance.social_stability_delta, "social"),
    ]
    return _format_preview(stance.description, [effect for effect in effects if effect])


def _wealth_preview(strategy) -> str:
    effects = [
        f"emergency floor {_money(strategy.emergency_cash_floor)}",
        f"debt pay rate {strategy.extra_debt_payment_rate * 100:.0f}%",
        f"savings {strategy.safe_savings_rate * 100:.0f}%",
        f"index {strategy.index_invest_rate * 100:.0f}%",
        f"growth {strategy.growth_invest_rate * 100:.0f}%",
        f"risk bias {strategy.risk_bias}",
    ]
    return _format_preview(strategy.description, effects)


def _focus_preview(focus) -> str:
    effects = [
        f"income x{focus.income_multiplier:.2f}",
        _signed_label(focus.promotion_progress_bonus, "promo"),
        _signed_label(focus.education_progress_bonus, "education"),
        _signed_label(focus.stress_delta, "stress"),
        _signed_label(focus.energy_delta, "energy"),
        _signed_label(focus.life_satisfaction_delta, "life"),
        _signed_label(focus.social_stability_delta, "social"),
    ]
    return _format_preview(focus.description, [effect for effect in effects if effect])


def _education_intensity_options(program) -> list[tuple[str, str, str]]:
    return [
        (
            "Standard",
            "standard",
            _format_preview(
                "Normal pace and stress.",
                [
                    "baseline progress",
                    "school stays balanced with the rest of the run",
                ],
            ),
        ),
        (
            "Intensive",
            "intensive",
            _format_preview(
                "Higher cost, higher stress, better GPA trend.",
                [
                    "stress +3",
                    "energy -2",
                    "progress stronger",
                    "best when you can afford to push the school lane",
                ],
            ),
        ),
        (
            "Light",
            "light",
            _format_preview(
                "Lower cost, lower stress, risk of slipping GPA.",
                [
                    "stress -2",
                    "energy +1",
                    "progress softer",
                    "good when you need recovery more than speed",
                ],
            ),
        ),
    ]
