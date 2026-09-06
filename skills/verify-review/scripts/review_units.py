#!/usr/bin/env python3
"""verify-review profile integration layer.

The mature loop engine is kept byte-for-byte in ``review_units_core.py``. This
entry point registers opt-in research-profile checks that live on independent
feature branches: current/full GRADE and the Cochrane intervention-review profile.
It mutates the core's declarative unit/check vocabulary before re-exporting its
API, while keeping profile-only optional records in this wrapper so the parent's
closed optional-record contract remains exact.

PROFILE ACTIVATION
  ``profile: "cochrane_intervention"`` is valid only with
  ``review_type: "systematic"`` and requires an explicit ``units_in_scope``
  declaration. The integration appends ``U_cochrane`` to that frozen scope when
  missing; it never creates a singleton scope from the profile alone. Omitting the
  ``cochrane_profile`` check therefore leaves that unit underived and prevents
  VERIFIED without suppressing defects from the review's already-declared scope.

CURRENT GRADE
  ``U_grade_current`` is registered as an explicit opt-in unit/check because the
  repository preserves the legacy GRADE contract alongside current/full mode.
  Put ``U_grade_current`` in ``units_in_scope`` and declare the
  ``grade_profile_current`` check. Its wrapper-owned optional ``rob_record`` is an
  appraisal route, so supplying it requires ``rob_appraisal`` to run on the same
  record, preserving the human-gate identity invariant.

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
        # Profile-only secondary records are intentionally NOT stored in this
        # parent table. The core regression suite proves that every secondary key
        # in CHECK_TABLE belongs to the core's own appraisal/PRISMA closure. This
        # wrapper owns and validates its extension in PROFILE_OPTIONAL_RECORDS.
        "optional_records": (),
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

# Wrapper-owned argv vocabulary. Keeping this separate from CHECK_TABLE is not a
# bypass: _validated_checks_with_profiles validates it against a closed schema,
# resolves every path through the same runner containment boundary, appends only
# the fixed flag declared here, and then enforces appraisal file identity.
PROFILE_OPTIONAL_RECORDS = {
    "grade_profile_current": (("rob_record", "--rob"),),
}
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
    if not declared_present:
        raise _core.InputError(
            "profile: cochrane_intervention requires explicit units_in_scope; "
            "profile activation may add U_cochrane but cannot define the rest of "
            "the frozen review scope"
        )
    scoped = list(declared)
    if "U_cochrane" not in scoped:
        scoped.append("U_cochrane")
    # A methodological profile augments an already-declared frozen scope. It must
    # never create scope by itself: doing so would turn an otherwise lenient record
    # into a singleton U_cochrane scope and silently discard other derived defects.
    return scoped, True


def _validated_checks_with_profiles(data, runner):
    """Validate core checks plus wrapper-owned profile secondary records.

    The core validator owns the base check schema. For a profile check, this layer
    first validates the extension keys against PROFILE_OPTIONAL_RECORDS, removes
    those keys from a shallow validation copy, and lets the unchanged core validate
    everything else. It then appends only the fixed flags declared above, resolves
    their paths through the same CheckRunner containment boundary, and closes the
    current-GRADE appraisal identity rule against ``rob_appraisal.record``.
    """
    raw = data.get("checks")
    if not isinstance(raw, dict):
        return _base_validated_checks(data, runner)

    # Build a validation-only copy in which wrapper-owned optional keys are removed.
    # The original record remains untouched and is used below to build the final
    # argv. Unknown extension keys fail here before any subprocess can run.
    sanitized = dict(data)
    sanitized_checks = dict(raw)
    for name, option_specs in PROFILE_OPTIONAL_RECORDS.items():
        entry = raw.get(name)
        if not isinstance(entry, dict):
            continue  # core validator owns the missing/wrong-type diagnostic
        allowed = {"record"} | {key for key, _ in option_specs}
        _core._reject_unknown_keys(entry, allowed, f"checks.{name}")
        option_keys = {key for key, _ in option_specs}
        sanitized_checks[name] = {
            key: value for key, value in entry.items() if key not in option_keys
        }
    sanitized["checks"] = sanitized_checks

    out = _base_validated_checks(sanitized, runner)

    # Add the wrapper-owned fixed argv. `runner.argv_for` already resolved and
    # validated the primary record; secondary paths go through contained_record.
    for name, option_specs in PROFILE_OPTIONAL_RECORDS.items():
        entry = raw.get(name)
        if not isinstance(entry, dict) or name not in out:
            continue
        argv, expected = out[name]
        argv = list(argv)
        for key, flag in option_specs:
            if key in entry:
                argv += [
                    flag,
                    runner.contained_record(entry[key], f"checks.{name}.{key}"),
                ]
        out[name] = (argv, expected)

    # A profile check that reads an appraisal must share the exact file with the
    # H_rob owner. This is structural, not scope-dependent: an out-of-scope unit
    # must not make a pending signature disappear from the verdict.
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

# Wrapper-owned integration vocabulary is exported after the core so callers and
# tests can distinguish parent closure from profile extension closure.
globals()["PROFILE_OPTIONAL_RECORDS"] = PROFILE_OPTIONAL_RECORDS
globals()["PROFILE_APPRAISAL_ROUTES"] = PROFILE_APPRAISAL_ROUTES


if __name__ == "__main__":
    raise SystemExit(_core.main())
