"""Organisation of solution data structures and result printing."""

from .solution import LPSolution


def _section(lines: list[str], title: str) -> None:
    lines.append(f"\n{title}")
    lines.append("-" * len(title))


def print_results(solution: LPSolution, label: str = "BlendMax") -> str:
    lines: list[str] = []
    lines.append(f"{label} - SmeltCo Production Planning")
    lines.append("=" * (len(label) + 30))
    lines.append(f"Status:   {solution.meta.status}")
    if solution.meta.objective is not None:
        lines.append(f"Profit:   £{solution.meta.objective:,.2f}")
    lines.append(f"Runtime:  {solution.meta.runtime_seconds:.3f} s")

    if not solution.is_optimal:
        lines.append("No optimal solution found, skipping details.")
        result = "\n".join(lines)
        print(result)
        return result

    # --- Blend allocation ---
    _section(lines, "Blend Allocation (kg input)")
    blend = solution.get_primal("blend").copy()
    blend["usage"] = blend["usage"].map("{:,.1f}".format)
    blend["proportion"] = blend["proportion"].map("{:.1%}".format)
    lines.append(blend.to_string())

    # --- Supply sensitivity ---
    _section(lines, "Supply Sensitivity")
    supply = solution.get_dual("supply").copy()
    supply["material"] = supply["constraint"].str.removeprefix("Supply_")
    cols = [
        "material",
        "shadow_price",
        "rhs_current",
        "allowable_decrease",
        "allowable_increase",
        "is_binding",
        "degenerate_warning",
    ]
    supply = supply[cols].set_index("material")
    supply["shadow_price"] = supply["shadow_price"].map("{:,.4f}".format)
    supply["rhs_current"] = supply["rhs_current"].map("{:,.0f}".format)
    supply["allowable_decrease"] = supply["allowable_decrease"].map("{:,.1f}".format)
    supply["allowable_increase"] = supply["allowable_increase"].map(
        lambda x: "inf." if x == float("inf") else f"{x:,.1f}"
    )
    lines.append(supply.to_string())

    # --- Capacity sensitivity ---
    _section(lines, "Capacity Sensitivity")
    capacity = solution.get_dual("capacity").copy()
    capacity["product"] = capacity["constraint"].str.removeprefix("Capacity_")
    cols = [
        "product",
        "shadow_price",
        "rhs_current",
        "allowable_decrease",
        "allowable_increase",
        "is_binding",
    ]
    capacity = capacity[cols].set_index("product")
    capacity["shadow_price"] = capacity["shadow_price"].map("{:,.4f}".format)
    capacity["rhs_current"] = capacity["rhs_current"].map("{:,.0f}".format)
    capacity["allowable_decrease"] = capacity["allowable_decrease"].map(
        "{:,.1f}".format
    )
    capacity["allowable_increase"] = capacity["allowable_increase"].map(
        lambda x: "inf." if x == float("inf") else f"{x:,.1f}"
    )
    lines.append(capacity.to_string())

    result = "\n".join(lines)
    print(result)
    return result
