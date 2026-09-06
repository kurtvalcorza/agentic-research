#!/usr/bin/env python3
"""verify-review profile integration layer.

The mature loop engine is kept byte-for-byte in ``review_units_core.py``. This
entry point registers opt-in research-profile checks that live on independent
feature branches: current/full GRADE and the Cochrane intervention-review profile.
It mutates the core's declarative tables before re-exporting its API, so the same
validation, scope, routing, preview, manifest, and fail-closed machinery remains
the single implementation.

PROFILE ACTIVATION
  ``profile: "cochrane_intervention"`` is valid only with
  ``review_type: "systematic"`` and automatically adds ``U_cochrane`` to the
  frozen scope. Omitting the ``cochrane_profile`` check therefore leaves that unit
  underived and prevents VERIFIED; the profile cannot be declared and then ignored.

CURRENT GRADE
  ``U_grade_current`` is registered as an explicit opt-in unit/check because the
  repository preserves the legacy GRADE contract alongside current/full mode.
  Put ``U_grade_current`` in ``units_in_scope`` and declare the
  ``grade_profile_current`` check. Its optional ``rob_record`` is an appraisal
  route, so supplying it requires ``rob_appraisal`` to run on the same record,
  preserving the human-gate identity invariant.

WHAT THIS CANNOT CHECK
  Registration cannot authenticate a review profile, an appraisal confirmation,
  or the substantive correctness of a GRADE/Cochrane judgment. It makes the child
  validators part of the mechanical verdict and preserves their fail-closed
  accounting; their own documented epistemic limits still apply.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_core():
    spec = importlib.util.spec_from_file_location(
        "_verify_review_units_core", _HERE / "review_units_core.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load review_units_core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_core = _load_core()

# New derivable units. Neither extends the universal floor: they apply only when
# the review explicitly opts into the corresponding methodology/profile.
_core.DEFAULT_WEIGHTS.update({
    "U_grade_current": 1,
    "U_cochrane": 1,
})

# ``profile`` is a classification field, not argv. It is consumed only by the
# scope resolver below and never passed to a subprocess.
_core.RECORD_KEYS.add("profile")

_core.CHECK_TABLE.update({
    "grade_profile_current": {
        "script": ("skills", "validate-evidence", "scripts", "grade_profile_current.py"),
        "units": ("U_grade_current",),
        "gates": (),
        "optional_records": (("rob_record", "--rob"),),
        "conditional_units": {},
    },
    "cochrane_profile": {
        "script": ("skills", "cochrane-intervention", "scripts", "cochrane_profile.py"),
        "units": ("U_cochrane",),
        "gates": (),
        "optional_records": (),
        "conditional_units": {},
    },
})

# The parent engine deliberately owns only the appraisal routes registered in its
# own CHECK_TABLE. Profile extensions are enumerated here instead of mutating the
# parent's APPRAISAL_ROUTES set: that keeps the core closure invariant meaningful
# while giving this integration layer an equally explicit closure of its own.
PROFILE_APPRAISAL_ROUTES = {("grade_profile_current", "rob_record")}

# Rebuild producer maps after extending the declarative table. The core's compute
# and preview functions read these module globals at call time.
_core.DERIVED_BY = {
    unit: name
    for name, spec in _core.CHECK_TABLE.items()
    for unit in spec["units"]
}
_core.DERIVED_BY_GATE = {
    gate: name
    for name, spec in _core.CHECK_TABLE.items()
    for gate in spec["gates"]
}

_base_validated_scope = _core._validated_scope
_base_validated_checks = _core._validated_checks


def _validated_scope_with_profile(data):
    declared, declared_present = _base_validated_scope(data)
    profile = data.get("profile")
    if profile is None:
        return declared, declared_present
    if not isinstance(profile, str):
        raise _core.InputError("profile: expected a string")
    if profile != "cochrane_intervention":
        raise _core.InputError(
            "profile: unknown profile %r; expected 'cochrane_intervention'" % profile
        )
    if data.get("review_type") != "systematic":
        raise _core.InputError(
            "profile: cochrane_intervention requires review_type 'systematic'"
        )
    scoped = list(declared)
    if "U_cochrane" not in scoped:
        scoped.append("U_cochrane")
    # A declared methodological profile is itself a scope declaration. This means
    # the rigorous path applies even if units_in_scope was omitted: gates must be
    # explicit and U_cochrane must be derived before VERIFIED is reachable.
    return scoped, True


def _validated_checks_with_profiles(data, runner):
    """Validate core checks, then close appraisal identity for profile routes.

    The parent engine enforces this invariant for the routes it owns. Current GRADE
    is registered by this wrapper, so its ``rob_record`` is checked here against
    the same ``rob_appraisal.record`` identity rule rather than mutating the core's
    route enumeration behind its regression tests.
    """
    out = _base_validated_checks(data, runner)
    raw = data.get("checks")
    if not isinstance(raw, dict):
        return out  # the core already handled absent/malformed shapes

    for name, key in sorted(PROFILE_APPRAISAL_ROUTES):
        entry = raw.get(name)
        if not (isinstance(entry, dict) and key in entry):
            continue
        rob = raw.get("rob_appraisal")
        if not isinstance(rob, dict) or "record" not in rob:
            raise _core.InputError(
                f"checks.{name}: supplies {key!r} but no 'rob_appraisal' entry "
                f"runs that record. Pending signatures in it would be counted by "
                f"nothing, so the appraisal check must run alongside"
            )
        mine = runner.contained_record(entry[key], f"checks.{name}.{key}")
        theirs = runner.contained_record(
            rob["record"], "checks.rob_appraisal.record"
        )
        if not runner.same_record(mine, theirs):
            raise _core.InputError(
                f"checks.{name}.{key} and checks.rob_appraisal.record name "
                f"DIFFERENT files ({entry[key]!r} vs {rob['record']!r}). They must "
                f"be the same appraisal so pending signatures cannot disappear "
                f"between the profile check and the H_rob owner"
            )
    return out


_core._validated_scope = _validated_scope_with_profile
_core._validated_checks = _validated_checks_with_profiles

# Re-export the core API after mutation. Functions remain bound to the core module,
# whose globals above now contain the extended tables and scope/check resolvers.
for _name in dir(_core):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_core, _name)

# Wrapper-owned integration vocabulary is intentionally exported after the core so
# callers/tests can distinguish parent routes from routes introduced by this layer.
globals()["PROFILE_APPRAISAL_ROUTES"] = PROFILE_APPRAISAL_ROUTES


if __name__ == "__main__":
    raise SystemExit(_core.main())
