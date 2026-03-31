import pytest

from budgetwars.loaders import load_all_content
from budgetwars.validators import validate_content_bundle


def test_validator_rejects_invalid_effect_keys() -> None:
    bundle = load_all_content()
    invalid_item = bundle.items[0].model_copy(update={"effects": {"luck": 5}})
    invalid_bundle = bundle.model_copy(update={"items": [invalid_item, *bundle.items[1:]]})

    with pytest.raises(ValueError, match="invalid effect keys"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_duplicate_event_choice_ids() -> None:
    bundle = load_all_content()
    event = bundle.events[0]
    duplicate_choices = [
        event.choices[0],
        event.choices[0].model_copy(update={"label": "Duplicate label"}),
    ]
    invalid_event = event.model_copy(update={"choices": duplicate_choices})
    invalid_bundle = bundle.model_copy(update={"events": [invalid_event, *bundle.events[1:]]})

    with pytest.raises(ValueError, match="Duplicate event choice"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_broken_job_location_reference() -> None:
    bundle = load_all_content()
    broken_job = bundle.jobs[0].model_copy(update={"location_id": "missing_location"})
    invalid_bundle = bundle.model_copy(update={"jobs": [broken_job, *bundle.jobs[1:]]})

    with pytest.raises(ValueError, match="references unknown location"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_invalid_optional_expense_effect_key() -> None:
    bundle = load_all_content()
    broken_expense = bundle.expenses[-1].model_copy(update={"skip_effects": {"happiness": 3}})
    invalid_bundle = bundle.model_copy(update={"expenses": [*bundle.expenses[:-1], broken_expense]})

    with pytest.raises(ValueError, match="invalid effect keys"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_optional_expense_without_tradeoff_effects() -> None:
    bundle = load_all_content()
    target = next(expense for expense in bundle.expenses if not expense.mandatory)
    broken = target.model_copy(
        update={
            "pay_effects": {},
            "skip_effects": {},
            "pay_temporary_effects": [],
            "skip_temporary_effects": [],
        }
    )
    fixed_expenses = [broken if expense.id == target.id else expense for expense in bundle.expenses]
    invalid_bundle = bundle.model_copy(update={"expenses": fixed_expenses})

    with pytest.raises(ValueError, match="should define pay_effects, skip_effects, or temporary effects"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_invalid_temporary_effect_keys() -> None:
    bundle = load_all_content()
    target = next(expense for expense in bundle.expenses if expense.pay_temporary_effects)
    broken_effect = target.pay_temporary_effects[0].model_copy(update={"effects": {"luck": 1}})
    broken_expense = target.model_copy(update={"pay_temporary_effects": [broken_effect]})
    fixed_expenses = [broken_expense if expense.id == target.id else expense for expense in bundle.expenses]
    invalid_bundle = bundle.model_copy(update={"expenses": fixed_expenses})

    with pytest.raises(ValueError, match="invalid effect keys"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_invalid_temporary_effect_duration() -> None:
    bundle = load_all_content()
    target = next(job for job in bundle.jobs if job.work_temporary_effects)
    broken_effect = target.work_temporary_effects[0].model_copy(update={"duration_weeks": 0})
    broken_job = target.model_copy(update={"work_temporary_effects": [broken_effect]})
    fixed_jobs = [broken_job if job.id == target.id else job for job in bundle.jobs]
    invalid_bundle = bundle.model_copy(update={"jobs": fixed_jobs})

    with pytest.raises(ValueError, match="duration_weeks must be between 1 and 4"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_offsite_penalty_above_max_energy() -> None:
    bundle = load_all_content()
    invalid_config = bundle.config.model_copy(update={"offsite_work_energy_penalty": bundle.config.max_energy + 1})
    invalid_bundle = bundle.model_copy(update={"config": invalid_config})

    with pytest.raises(ValueError, match="offsite_work_energy_penalty exceeds config.max_energy"):
        validate_content_bundle(invalid_bundle)
