"""Solution data structures for optimisation models.

Defines a layered hierarchy:
- SolveMeta: metadata about the solve call itself (status, runtime, etc.)
- OptimisationSolution: abstract base, holds meta + primal/dual data
- LPSolution: linear programs, supports dual variables and ranging analysis
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SolveMeta:
    status: str
    objective: float | None
    runtime_seconds: float
    solver: str


@dataclass(frozen=True)
class OptimisationSolution:
    """Abstract base for optimisation solutions.

    Subclasses should inherit from LPSolution, not this directly.
    """
    meta: SolveMeta
    primal: dict[str, pd.DataFrame]
    dual: dict[str, pd.DataFrame]

    @property
    def is_optimal(self) -> bool:
        return self.meta.status == "Optimal"

    def get_primal(self, name: str) -> pd.DataFrame:
        if name not in self.primal:
            raise KeyError(f"No primal data named {name!r}. Available: {list(self.primal)}")
        return self.primal[name]


@dataclass(frozen=True)
class LPSolution(OptimisationSolution):
    """Solution to a linear program. Supports dual variables and ranging."""

    def get_dual(self, name: str) -> pd.DataFrame:
        if name not in self.dual:
            raise KeyError(f"No dual data named {name!r}. Available: {list(self.dual)}")
        return self.dual[name]

