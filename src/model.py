"""Maximises profit subject to material supply, capacity, and blend proportionconstraints."""

import time

import pandas as pd
import pulp

from .data import BlendMaxStructuredData
from .dual import get_rhs_ranges
from .solution import LPSolution, SolveMeta


class BlendMax:
    """PuLP/HiGHS LP for BlendMax production planning.

    Build once, call solve() for results.
    """

    def __init__(self, data: BlendMaxStructuredData) -> None:
        self.data = data
        self.model = pulp.LpProblem("BlendMax", pulp.LpMaximize)
        self.vars: dict[tuple[str, str], pulp.LpVariable] = {}
        self._build_model()

    def _build_model(self) -> None:
        d = self.data

        # Decision variables: x[(p,m)] = kg of material m used in product p
        for p, m in d.pairs:
            self.vars[(p, m)] = pulp.LpVariable(f"x_{p}_{m}", lowBound=0)

        # Objective: maximise Σ (price_p × (1 − loss) − cost_m) × x[(p,m)]
        self.model += (
            pulp.lpSum(
                (d.price[p] * (1.0 - d.loss) - d.cost[m]) * self.vars[(p, m)]
                for p, m in d.pairs
            ),
            "Total_Profit",
        )

        # Supply: total usage of m across all products ≤ supply_m
        for m in d.materials:
            self.model += (
                pulp.lpSum(self.vars[(p, m)] for p in d.products_of[m]) <= d.supply[m],
                f"Supply_{m}",
            )

        # Capacity: total output for p ≤ capacity_p  (output = (1-loss) × input)
        for p in d.products:
            self.model += (
                (1 - d.loss) * pulp.lpSum(self.vars[(p, m)] for m in d.materials_of[p])
                <= d.capacity[p],
                f"Capacity_{p}",
            )

        # Blend proportions: min_pct ≤ x[(p,m)] / total_input_p ≤ max_pct
        for p in d.products:
            total_input = pulp.lpSum(self.vars[(p, m)] for m in d.materials_of[p])
            for m in d.materials_of[p]:
                if d.min_pct[(p, m)] > 0:
                    self.model += (
                        self.vars[(p, m)] >= d.min_pct[(p, m)] * total_input,
                        f"MinPct_{p}_{m}",
                    )
                if d.max_pct[(p, m)] < 1:
                    self.model += (
                        self.vars[(p, m)] <= d.max_pct[(p, m)] * total_input,
                        f"MaxPct_{p}_{m}",
                    )

    def solve(self) -> LPSolution:
        """Solve and return the optimal blend allocation."""
        t0 = time.perf_counter()
        self.model.solve(pulp.HiGHS(msg=False))
        runtime = time.perf_counter() - t0

        status = pulp.LpStatus[self.model.status]
        obj_val = pulp.value(self.model.objective)

        primal: dict[str, pd.DataFrame] = {}
        dual: dict[str, pd.DataFrame] = {}

        if status == "Optimal":
            d = self.data

            blend_rows = []
            for p in d.products:
                total = sum(
                    pulp.value(self.vars[(p, m)]) or 0.0 for m in d.materials_of[p]
                )
                for m in d.materials_of[p]:
                    usage = pulp.value(self.vars[(p, m)]) or 0.0
                    blend_rows.append(
                        {
                            "product": p,
                            "material": m,
                            "usage": usage,
                            "proportion": usage / total if total > 0 else 0.0,
                        }
                    )
            primal["blend"] = pd.DataFrame(blend_rows).set_index(
                ["product", "material"]
            )

            ranging = get_rhs_ranges(self.model)
            dual["supply"] = ranging[
                ranging["constraint"].str.startswith("Supply_")
            ].reset_index(drop=True)
            dual["capacity"] = ranging[
                ranging["constraint"].str.startswith("Capacity_")
            ].reset_index(drop=True)

        return LPSolution(
            meta=SolveMeta(
                status=status,
                objective=float(obj_val) if obj_val is not None else None,  # type: ignore[arg-type]
                runtime_seconds=runtime,
                solver="HiGHS",
            ),
            primal=primal,
            dual=dual,
        )
