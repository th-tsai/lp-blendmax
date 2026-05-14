"""RHS sensitivity ranging for PuLP models solved with pulp.HiGHS."""

from __future__ import annotations

import math
from typing import Any, cast

import pandas as pd
import pulp


def get_rhs_ranges(prob: pulp.LpProblem) -> pd.DataFrame:
    """Return RHS sensitivity ranges for every constraint as a DataFrame.

    Requires `prob` to have been solved with `pulp.HiGHS(...)` so the basis
    is retained on `prob.solverModel`. Non-binding inequalities get ±inf on
    the slackenable side.

    Columns: constraint, sense, shadow_price, is_binding, rhs_current,
    rhs_lower, rhs_upper, allowable_decrease, allowable_increase,
    degenerate_warning.

    `degenerate_warning` is True when the constraint is binding with a nonzero
    shadow price but one side of its allowable range collapses to zero — the
    basis is degenerate and the shadow price has different left- and
    right-derivatives. Re-solve before trusting it on the other side.
    """
    h = prob.solverModel
    if h is None:
        raise ValueError("Solve with pulp.HiGHS(...) first; solverModel is None.")

    h = cast(Any, h)
    _, ranging = h.getRanging()
    lp = h.getLp()
    # PuLP's HiGHS solver minimizes internally; flip duals back for max problems.
    sign = 1.0 if prob.sense == pulp.LpMinimize else -1.0

    rows = []
    for name, con in prob.constraints.items():
        con = cast(Any, con)
        idx = con.index
        sense = _sense_str(con.sense)
        rhs_current = lp.row_upper_[idx] if sense != ">=" else lp.row_lower_[idx]
        is_binding = abs(float(con.slack or 0.0)) <= 1e-6
        dn = ranging.row_bound_dn.value_[idx]
        up = ranging.row_bound_up.value_[idx]

        if is_binding:
            rhs_lower, rhs_upper = dn, up
        elif sense == "<=":
            # HiGHS may put the tightening endpoint in either slot for a slack
            # row; take the finite one and open the relaxing side to +inf.
            rhs_lower, rhs_upper = min(dn, up), math.inf
        elif sense == ">=":
            rhs_lower, rhs_upper = -math.inf, max(dn, up)
        else:
            rhs_lower, rhs_upper = dn, up

        shadow_price = sign * float(con.pi or 0.0)
        allowable_decrease = rhs_current - rhs_lower
        allowable_increase = rhs_upper - rhs_current
        degenerate_warning = (
            is_binding
            and abs(shadow_price) > 1e-9
            and (allowable_decrease <= 1e-9 or allowable_increase <= 1e-9)
        )

        rows.append({
            "constraint": name,
            "sense": sense,
            "shadow_price": shadow_price,
            "is_binding": is_binding,
            "rhs_current": rhs_current,
            "rhs_lower": rhs_lower,
            "rhs_upper": rhs_upper,
            "allowable_decrease": allowable_decrease,
            "allowable_increase": allowable_increase,
            "degenerate_warning": degenerate_warning,
        })

    return pd.DataFrame(rows)


def _sense_str(sense: int) -> str:
    if sense == pulp.LpConstraintLE:
        return "<="
    if sense == pulp.LpConstraintGE:
        return ">="
    return "=="
