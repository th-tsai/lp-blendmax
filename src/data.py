"""Data schema and loading for BlendMax."""

import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class BlendMaxRawData:
    """Raw input data loaded from CSV/TOML.

    - product: DataFrame indexed by product name, columns [price, capacity]
    - material: DataFrame indexed by material name, columns [cost, supply]
    - recipe: DataFrame indexed by (product, material), columns [min_pct, max_pct]
    - loss: scalar in [0, 1)  — 0 means no yield loss; 1 is invalid (all material destroyed)
    """

    product: pd.DataFrame
    material: pd.DataFrame
    recipe: pd.DataFrame
    loss: float
    result: Path | None = None
    description: str | None = None

    @classmethod
    def load_from_toml(cls, path: Path) -> "BlendMaxRawData":
        with open(path, "rb") as f:
            data: dict[str, Any] = tomllib.load(f)

        return cls(
            product=pd.read_csv(
                path.parent / data["table_path"]["product"],
                index_col="product",
                dtype={"price": float, "capacity": float},
            ),
            material=pd.read_csv(
                path.parent / data["table_path"]["material"],
                index_col="material",
                dtype={"cost": float, "supply": float},
            ),
            recipe=pd.read_csv(
                path.parent / data["table_path"]["recipe"],
                index_col=["product", "material"],
                dtype={"min_pct": float, "max_pct": float},
            ),
            loss=float(data["scalar"]["loss"]),
            result=Path(data["result"]["result"]),
            description=data["result"]["description"],
        )

    def structured(self) -> "BlendMaxStructuredData":
        return BlendMaxStructuredData.from_raw(self)


@dataclass(frozen=True)
class BlendMaxStructuredData:
    """Flattened, dict-indexed data ready for use in an optimization model."""

    products: tuple[str, ...]
    materials: tuple[str, ...]
    pairs: tuple[tuple[str, str], ...]
    materials_of: dict[str, tuple[str, ...]]
    products_of: dict[str, tuple[str, ...]]
    loss: float
    price: dict[str, float]
    cost: dict[str, float]
    supply: dict[str, float]
    capacity: dict[str, float]
    min_pct: dict[tuple[str, str], float]
    max_pct: dict[tuple[str, str], float]

    @classmethod
    def from_raw(cls, raw: BlendMaxRawData) -> "BlendMaxStructuredData":
        products: tuple[Any, ...] = tuple(raw.product.index.astype(str))
        materials: tuple[Any, ...] = tuple(raw.material.index.astype(str))
        pairs: tuple[tuple[str, str], ...] = tuple(
            (str(p), str(m)) for p, m in raw.recipe.index
        )

        materials_of: defaultdict[str, list[str]] = defaultdict(list)
        products_of: defaultdict[str, list[str]] = defaultdict(list)
        for p, m in pairs:
            materials_of[p].append(m)
            products_of[m].append(p)

        return cls(
            products=products,
            materials=materials,
            pairs=pairs,
            materials_of={p: tuple(materials_of[p]) for p in products},
            products_of={m: tuple(products_of[m]) for m in materials},
            loss=raw.loss,
            price={str(k): float(v) for k, v in raw.product["price"].items()},
            cost={str(k): float(v) for k, v in raw.material["cost"].items()},
            supply={str(k): float(v) for k, v in raw.material["supply"].items()},
            capacity={str(k): float(v) for k, v in raw.product["capacity"].items()},
            min_pct={pm: float(v) for pm, v in zip(pairs, raw.recipe["min_pct"].to_list())},
            max_pct={pm: float(v) for pm, v in zip(pairs, raw.recipe["max_pct"].to_list())},
        )
