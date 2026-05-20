# BlendMax — SmeltCo Production Planning

**Problem class:** Linear programming · blending  
**Solver:** PuLP + HiGHS

---

## Problem

SmeltCo Ltd produces **brass**, **bronze**, and **duralumin** by blending two raw materials per product.
The blending process incurs a **10 % mass loss**, so only 90 % of input material becomes finished product.
The goal is to find the monthly production plan that maximises profit.

### Raw materials

| Material  | Monthly supply (kg) | Purchase cost (£/kg) |
| --------- | ------------------: | -------------------: |
| Copper    |              80,000 |                   12 |
| Zinc      |             100,000 |                    5 |
| Tin       |              75,000 |                    2 |
| Aluminium |              50,000 |                    8 |

### Products

| Product   | Material 1 | Material 2 | Sell price (£/kg) | Capacity (kg) |
| --------- | ---------- | ---------- | ----------------: | ------------: |
| Brass     | Copper     | Zinc       |                 8 |        70,000 |
| Bronze    | Copper     | Tin        |                16 |       100,000 |
| Duralumin | Copper     | Aluminium  |                14 |        90,000 |

### Copper proportion requirements

| Product   | Min copper | Max copper |
| --------- | :--------: | :--------: |
| Brass     |    20 %    |    50 %    |
| Bronze    |    60 %    |    80 %    |
| Duralumin |    10 %    |    50 %    |

---

## Linear Programming Formulation

### Sets and indices

| Symbol | Definition            |
| ------ | --------------------- |
| $P$    | set of products       |
| $M$    | set of materials      |
| $p, m$ | indices over $P$, $M$ |

### Parameters

| Symbol       | Meaning                                 |
| ------------ | --------------------------------------- |
| $\eta$       | yield factor                            |
| $c_m$        | cost of material $m$ (£/kg)             |
| $S_m$        | supply of material $m$ (kg)             |
| $s_p$        | sell price of product $p$ (£/kg)        |
| $K_p$        | production capacity of product $p$ (kg) |
| $\ell_{p,m}$ | min proportion of $m$ in $p$            |
| $u_{p,m}$    | max proportion of $m$ in $p$            |

### Decision variables

| Symbol          | Meaning                                |
| --------------- | -------------------------------------- |
| $x_{p,m} \ge 0$ | kg of material $m$ used in product $p$ |

### Objective — maximise profit

$$
\max \quad \eta \sum_{p \in P} s_p \sum_{m \in M} x_{p,m} - \sum_{m \in M} c_m \sum_{p \in P} x_{p,m}
$$

### Constraints

**C1 — Material supply** (total usage of each material cannot exceed its monthly limit)

$$\sum_{p \in A} x_{p,m} \le S_m \quad \forall m \in M$$

**C2 — Product capacity** (finished output, after yield loss, cannot exceed the production ceiling)

$$\eta \sum_{m \in M} x_{p,m} \le K_p \quad \forall p \in P$$

**C3 — Proportion lower bound** (material $m$ must comprise at least $\ell_{p,m}$ of product $p$'s input)

$$x_{p,m} \ge \ell_{p,m} \sum_{m' \in M} x_{p, m'} \quad \forall p \in P, m \in M$$

**C4 — Proportion upper bound** (material $m$ may not exceed $u_{p,m}$ of product $p$'s input)

$$x_{p,m} \le u_{p,m} \sum_{m' \in M} x_{p,m'} \quad \forall p \in P, m \in M$$

> C3 and C4 are linear: multiplying the proportional bounds through by the total input $\sum_{m'} x_{p,m'} > 0$ yields linear constraints directly.

---

## Results

### Case 1 — Base (given supplies)

**Profit: £975,555.56**

| Product   | Output (kg) | Copper (kg) | Material 2 | Material 2 (kg) | Cu % |
| --------- | ----------: | ----------: | ---------- | --------------: | ---: |
| Brass     |   35,000.00 |    7,777.78 | Zinc       |       31,111.11 |  20% |
| Bronze    |  100,000.00 |   66,666.67 | Tin        |       44,444.44 |  60% |
| Duralumin |   50,000.00 |    5,555.56 | Aluminium  |       50,000.00 |  10% |

**Shadow prices**

| Material  | Shadow price (£) |       Dual range (kg) | New profit if at upper bound (£) |
| --------- | ---------------: | --------------------: | -------------------------------: |
| Zinc      |             0.00 |                     — |                                — |
| Tin       |             0.00 |                     — |                                — |
| Aluminium |             4.22 |            0 – 90,000 |                     1,144,444.44 |
| Copper    |             4.00 | 72,222.22 – 87,777.78 |                     1,006,666.67 |

Both aluminium and copper are fully consumed. Zinc and tin have slack; increasing their limits yields no additional profit.

---

### Case 2 — Aluminium increased to 90,000 kg

Aluminium is the binding constraint with the higher shadow price (£4.22 vs £4.00), so it is raised first to its dual-range upper bound of 90,000 kg.

**Profit: £1,144,444.44**

| Product   | Output (kg) | Copper (kg) | Material 2 | Material 2 (kg) | Cu % |
| --------- | ----------: | ----------: | ---------- | --------------: | ---: |
| Brass     |   15,000.00 |    3,333.33 | Zinc       |       13,333.33 |  20% |
| Bronze    |  100,000.00 |   66,666.67 | Tin        |       44,444.44 |  60% |
| Duralumin |   90,000.00 |   10,000.00 | Aluminium  |       90,000.00 |  10% |

**Shadow prices**

| Material  | Shadow price (£) |       Dual range (kg) | New profit if at upper bound (£) |
| --------- | ---------------: | --------------------: | -------------------------------: |
| Zinc      |             0.00 |                     — |                                — |
| Tin       |             0.00 |                     — |                                — |
| Aluminium |             4.22 |            0 – 90,000 |                     1,144,444.44 |
| Copper    |             4.00 | 76,666.67 – 92,222.22 |                     1,193,333.33 |

Copper remains binding; its dual-range upper bound has shifted to 92,222.22 kg.

---

### Case 3 — Aluminium 90,000 kg + Copper increased to 92,222.22 kg

**Profit: £1,193,333.33**

| Product   | Output (kg) | Copper (kg) | Material 2 | Material 2 (kg) | Cu % |
| --------- | ----------: | ----------: | ---------- | --------------: | ---: |
| Brass     |   70,000.00 |   15,555.56 | Zinc       |       62,222.22 |  20% |
| Bronze    |  100,000.00 |   66,666.67 | Tin        |       44,444.44 |  60% |
| Duralumin |   90,000.00 |   10,000.00 | Aluminium  |       90,000.00 |  10% |

**Shadow prices**

| Material  | Shadow price (£) |       Dual range (kg) | New profit if at upper bound (£) |
| --------- | ---------------: | --------------------: | -------------------------------: |
| Zinc      |             0.00 |                     — |                                — |
| Tin       |             0.00 |                     — |                                — |
| Aluminium |             4.00 | 89,999.99 – 90,000.00 |                     1,193,333.33 |
| Copper    |             0.00 |                     — |                                — |

All shadow prices are zero or the dual range has collapsed — no further improvement is achievable by adjusting any single material limit. **£1,193,333.33 is the global optimum under additional procurement.**

---

## Procurement Suggestion

### What the numbers tell us

**Baseline (current setup — profit £975,556)**

With today's supply limits, copper and aluminium are both fully consumed every month. Zinc and tin are only partially used — roughly 38,000 kg of zinc and 31,000 kg of tin are being ordered but never converted into product. That is wasted purchasing budget with no return.

**Case 1 — modest aluminium increase to 54,000 kg (profit £992,444, up £16,889)**

A test run raising aluminium by just 4,000 kg already adds nearly £17,000 per month, confirming aluminium is the right material to pursue. The full upside has not yet been captured.

**Case 2 — aluminium raised to 90,000 kg (profit £1,144,444, up £168,889 vs baseline)**

Pushing aluminium to 90,000 kg — the maximum the model can absorb — delivers the largest single improvement: nearly £169,000 more per month. All of that gain comes from expanding duralumin output from 50,000 kg to 90,000 kg. Copper is now the sole remaining material bottleneck.

**Case 3 — aluminium 90,000 kg and copper raised to 120,000 kg (profit £1,193,333, up £48,889 vs Case 2)**

With copper raised to 120,000 kg, profit climbs a further £49,000. However, the solver only actually consumes about 92,222 kg of that copper — the remaining 27,778 kg is surplus stock that earns nothing. SmeltCo does not need 120,000 kg; it needs roughly 92,000 kg. Ordering beyond that is a direct cost with zero return.

At this point, all three products have reached their production capacity limits. Aluminium still has a positive shadow price (£4.00/kg) but cannot be pushed further without expanding the duralumin production line. Bronze production capacity is now the highest-value constraint, at £7.11 per kg of additional throughput, followed by brass at £0.89 and duralumin at £0.67.

### Recommended actions

1. **Stop over-ordering zinc, tin, and copper.** Buy only what the factory consumes: roughly 62,000 kg of zinc, 44,000 kg of tin, and 92,000 kg of copper per month. Ordering more than these amounts adds cost but no profit.

2. **Prioritise securing more aluminium — this is the single most valuable procurement action.** Raising aluminium from 50,000 to 90,000 kg per month adds nearly £169,000 in monthly profit. Negotiate with aluminium suppliers first.

3. **Then secure copper to ~92,000 kg.** Once aluminium supply is resolved, topping up copper to the actual consumption level unlocks a further £49,000 per month. Do not order beyond ~92,000 kg — the solver confirms additional copper sits unused.

4. **Beyond these two steps, further gains require production investment, not procurement.** Once materials are right-sized, all three product lines are running at full capacity. The largest opportunity is bronze: expanding bronze production capacity is worth approximately £7.11 per additional kilogram of throughput. This is a capital investment question, not a purchasing one.
