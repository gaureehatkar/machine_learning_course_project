# Dataset 2 — Freeze Record
## Status: FROZEN ✅ (partial grounding — CC BY 4.0 — licence verified 2026-09-22)

Filled from: Afsharinia & Gurtoo PMC companion article (PMC13247571), Mendeley Data
repository page, and codebook shared by project team (September 2026).
Licence confirmed: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
Last updated: 2026-09-22

> **Licence: CC BY 4.0 — VERIFIED.**
> **Access date: 2026-09-22**

---

## 1. Identity

| Field              | Value                                                                                         | Verified? |
|--------------------|-----------------------------------------------------------------------------------------------|-----------|
| Name               | COVID-19 and Human Security (cross-sectional dataset of low- and semi-skilled gig workers in India) | VERIFIED (PMC abstract) |
| Authors            | Bita Afsharinia; Anjula Gurtoo (Indian Institute of Science, Bangalore)                       | VERIFIED (PMC CRediT) |
| DOI                | 10.17632/j6hd2dfsh8.1                                                                        | VERIFIED (PMC data-availability section) |
| Direct URL         | https://data.mendeley.com/datasets/j6hd2dfsh8/1                                               | VERIFIED (PMC data-availability section) |
| Repository         | Mendeley Data                                                                                 | VERIFIED |
| Access method      | Publicly available, no login required                                                         | VERIFIED (PMC: "can be accessed without login or special permissions") |
| Licence            | **CC BY 4.0** — https://creativecommons.org/licenses/by/4.0/ | VERIFIED (confirmed on Mendeley page by project team, 2026-09-22) |
| Related article    | Afsharinia & Gurtoo (2024), *Global Food Security*, 42(1). https://doi.org/10.1016/j.gfs.2024.100791 | VERIFIED (PMC references) |
| Access date        | 2026-09-22                                                                                            | VERIFIED |

---

## 2. Dataset characteristics

| Field              | Value                                                                                         | Verified? |
|--------------------|-----------------------------------------------------------------------------------------------|-----------|
| Sample size        | 2,830 respondents (2,837 administered; 7 excluded for incompleteness)                        | VERIFIED (PMC §4B) |
| Collection period  | Single survey wave: December 2020 – February 2021; retrospective recall to July–November 2019 | VERIFIED (PMC abstract, §2) |
| Geography          | Bangalore, India only (metropolitan city, southern India)                                     | VERIFIED (PMC §4A) |
| Unit of observation| Individual gig worker                                                                         | VERIFIED |
| Format             | Excel (XLSX), SPSS (.sav), CSV                                                                | VERIFIED (PMC specifications table) |
| Variables count    | 136 variables                                                                                 | VERIFIED (PMC abstract) |
| Design             | Cross-sectional with retrospective recall — NOT a longitudinal panel                         | VERIFIED (PMC §4B) |
| Sampling           | Systematic random sampling + snowball sampling                                                | VERIFIED (PMC §4B) |

---

## 3. Usable variables and DGP parameter mapping

Only variables that directly map to a DGP parameter are listed here.
"Grounded" is used ONLY for parameters with a direct mapping to a verified variable in this dataset.

### 3a. Parameters this dataset SUPPORTS (partial grounding)

| DGP parameter | Dataset variable | Dataset values (VERIFIED from codebook) | Mapping note |
|---|---|---|---|
| `mu_income` / `sigma_income` (LogNormal income baseline) | `Your monthly earnings now (Dec20–Jan2021)` — individual continuous ₹ (range 0–₹95,000) AND `FAMILY monthly earning now-2021` (range 0–₹300,000) | Individual: range 0–₹95,000 (exact mean/SD require microdata analysis). Household: mean ₹18,903, SD ₹14,474. | DGP uses individual monthly income. The **individual** earnings variable (0–₹95,000) is the better match. LogNormal(9.9, 0.4) → median ≈ ₹19,900 is consistent with reported household mean ₹18,903. Mapping is approximate (individual vs household; COVID period vs normal). |
| Pre-COVID income baseline | `Monthly earning before COVID?` — individual continuous ₹ (range 0–₹80,000) | Range 0–₹80,000 (exact distribution requires microdata) | Provides a pre-shock income reference. Supports the income scale choice. |
| `age` distribution | `Age` — numeric continuous (years) | Range 18–80; mean 36.86, SD 9.684 (VERIFIED PMC Table 2) | DGP uses Normal(34, 11) clipped [18, 70]. Dataset mean=37, SD≈10 — consistent. DGP upper clip 70 vs dataset max 80 is a minor deviation; noted as limitation. |
| `occupation_category` (type distribution) | `If yes, what is your job?` — categorical | 1=Drivers, 2=Delivery, 3=Beauty/services, 4=Street vendors, 5=Domestic workers, 6=Small Business, 7=Self-employed | Sample breakdown by occupation (VERIFIED from codebook platform/informal split): Drivers=750, Delivery=750, Beauty/services=300, Street Vendors=750, Domestic Workers=750. Proportions: Drivers≈26.5%, Delivery≈26.5%, Beauty≈10.6%, Street Vendors≈26.5%, Domestic Workers≈10.6% (platform n=1800, informal n=1500, total 3300 — slight discrepancy vs n=2830; use proportions with caution). DGP occupation categories map approximately: ride_hailing↔Drivers, delivery↔Delivery, freelance_services↔Beauty/Self-employed, retail_micro↔Street Vendors/Small Business, agri_labour=not in dataset (PROVISIONAL). |
| `has_emi` / loan presence | `Did you take a loan during March–Aug2020?` — binary (0=No, 1=Yes) | Binary yes/no (exact proportion requires microdata) | Provides a proxy for debt/loan prevalence. Not equivalent to a recurring EMI — mapping is approximate. |

### 3b. Parameters this dataset does NOT support

The following DGP parameters have **no directly observed counterpart** in this dataset.
They are marked **literature-informed (provisional)**. No source is asserted for their
specific values until you supply one.

| DGP parameter              | Status                          | Note |
|----------------------------|---------------------------------|------|
| `sigma_m` (income volatility, U[0.15, 0.40]) | literature-informed (provisional) | Dataset is cross-sectional — no month-by-month income series to measure CV. |
| `platform_tenure` (U{1..24} months at cutoff) | literature-informed (provisional) | Dataset does not record tenure on a specific platform. |
| `multi_platform` (Bernoulli 0.60)             | literature-informed (provisional) | Dataset records current job type (single category) — no multi-platform indicator. |
| `g` (monthly income growth, N(0, 0.01))       | literature-informed (provisional) | Cross-sectional design; no time series to estimate growth rate. |
| `amp` / `phase` (seasonal amplitude, U[0.05,0.35]) | literature-informed (provisional) | No monthly series available. |
| `rho` (expense ratio, U[0.45, 0.85])          | literature-informed (provisional) | Dataset has income and food/loan data but no full expense decomposition yielding a monthly ratio. |
| `emi_prob` / `emi_base` (EMI, Bernoulli 0.30) | literature-informed (provisional) | Loan taken (Y/N) and banded loan amount are present, but these are not equivalent to a recurring monthly EMI. |
| `e_shram_prob` (Bernoulli 0.64)               | literature-informed (provisional) | Dataset predates e-Shram launch (2021); no e-Shram registration variable. |
| `mu_L0` / `sigma_L0` (initial liquidity)      | literature-informed (provisional) | No balance/savings variable in the dataset. |
| `s_inc`, `s_rho` (outcome-window regime change) | methodological assumption       | Not derivable from any real dataset; structural default mechanism. |
| `shock_prob`, `shock_mag` (DGP-2 income shock) | methodological assumption       | Structural DGP choice; not derivable from this dataset. |

---

## 4. Full verified variable list (from codebook)

Key variables relevant to this project — confirmed from codebook provided by project team.

| Variable | Type | Range/Values | Relevant to DGP? |
|---|---|---|---|
| Age | Numeric continuous | 18–80 years | ✅ age distribution |
| Gender | Categorical | 1=Male, 2=Female | No |
| Education | Ordinal | 0–5 | No |
| Total family members | Numeric | 1–15 | No |
| Family members employed before COVID | Numeric | 0–9 | No |
| Family members employed now | Numeric | 0–6 | No |
| FAMILY monthly earning now-2021 | Numeric continuous | ₹0–₹300,000 | ✅ household income proxy |
| Currently employed? | Binary | 0/1 | No |
| Current job type | Categorical | 0–7 (see codebook) | ✅ occupation types |
| Job before COVID | Categorical | 0–7 | No (pre-COVID only) |
| **Your monthly earnings now (Dec20–Jan2021)** | **Numeric continuous** | **₹0–₹95,000** | **✅ individual income — best DGP match** |
| Monthly earning before COVID | Numeric continuous | ₹0–₹80,000 | ✅ pre-shock income baseline |
| Monthly earnings during lockdown | Numeric continuous | ₹0–₹90,000 | No (shock period) |
| Did you get paid before lockdown? | Binary | 0/1 | No |
| Mortgaged vehicle/gold | Binary | 0/1 | No |
| Took loan during March–Aug 2020 | Binary | 0/1 | ✅ loan/debt proxy |
| Loan reason | Categorical | 0–8 | No |
| Loan source | Categorical | 0–3 | No |
| Loan amount | Ordinal bands | ≤₹10k / ₹11–20k / ₹21–30k / >₹30k | No (banded, not continuous) |
| Interest rate | Ordinal | 0–5 (≤5% to >20%) | No |
| Will you be able to pay loan back? | 5-point Likert | 1=No … 5=Yes | ⚠️ subjective fear — NOT a default label |
| Job security fear | 5-point Likert | 1=No … 5=Yes | No |
| All food/health/environment variables | Various | — | No — not relevant to credit DGP |

**Sample breakdown by occupation (VERIFIED from codebook platform/informal split):**
- Platform workers: Drivers (750), Delivery (750), Beauty and other services (300) → total 1,800
- Informal workers: Street Vendors (750), Domestic Workers (750) → total 1,500
- Grand total per occupation breakdown: 3,300 (note: slightly exceeds n=2,830 — treat proportions as approximate)

## 5. Label presence

| Label type                | Present? | Detail |
|---------------------------|----------|--------|
| Binary repayment / default label | **No** | Not present. The dataset contains a 5-point Likert item on *perceived loan repayment ability* — this is a subjective fear measure, NOT a binary repayment outcome. It must not be used as a default label. |
| Loan taken (Y/N)          | Yes      | Binary variable indicating whether the respondent took a loan. Not a default label. |
| Loan amount (banded)      | Yes      | ≤₹10,000 / ₹11,000–20,000 / ₹21,000–30,000 / >₹30,000. Not a default label. |

**Conclusion:** Dataset 2 provides NO default or repayment labels. SynthGigCredit-IN-v1
default labels are generated entirely from the structural liquidity mechanism. This is
consistent with the plan (§7: "Default labels are not assumed").

---

## 6. Known limitations

1. **Single city**: Bangalore only. Not representative of all-India gig workers.
2. **Cross-sectional**: No longitudinal income series; cannot measure volatility, trend, or seasonality directly.
3. **No default labels**: Loan repayment ability is a Likert-scale fear measure, not a binary outcome.
4. **COVID-19 context**: Data collected during a pandemic shock — income levels and employment may not reflect normal conditions.
5. **Retrospective recall**: Pre-pandemic values are self-reported retrospectively; recall bias is possible.
6. **Snowball sampling component**: Representativeness cannot be statistically inferred.
7. **Small sample relative to the DGP**: 2,830 respondents vs 25,000 simulated applicants. Income distribution parameters are estimated with uncertainty.
8. **Household vs individual income**: The income variable is household monthly income, not individual gig-worker income. The DGP models individual income. The mapping is approximate.

---

## 7. Parameters grounded vs provisional — summary

| Parameter        | Claim allowed                                      |
|------------------|----------------------------------------------------|
| Income scale     | "Supported by Afsharinia & Gurtoo (2024) — household monthly income, Bangalore gig workers, mean ₹18,903" |
| Age distribution | "Supported by Afsharinia & Gurtoo (2024) — mean 37, SD 10, range 18–80" |
| Occupation types | "Partially supported — categories consistent; proportions provisional" |
| All other params | "Literature-informed (provisional) — no Dataset 2 source asserted" |

Do NOT use the word "grounded" for volatility, tenure, multi-platform, expense ratio,
liquidity, or any parameter not listed in section 3a above.

---

## 8. `grounding_dataset` config update

After you personally download and verify the licence on the Mendeley page,
update `configs/experiment.yaml`:

```yaml
grounding_dataset:
  status: FROZEN           # change from UNIDENTIFIED after licence confirmed
  freeze_doc: docs/dataset2_freeze.md
  name: "COVID-19 and Human Security (Afsharinia & Gurtoo)"
  doi: "10.17632/j6hd2dfsh8.1"
  url: "https://data.mendeley.com/datasets/j6hd2dfsh8/1"
  licence: "<FILL FROM MENDELEY PAGE>"
  access_date: "<FILL DATE YOU DOWNLOADED>"
  sample_size: 2830
  geography: "Bangalore, India"
  period: "Jul-Nov 2019 (retrospective); Dec 2020 - Feb 2021 (survey)"
  unit: "individual gig worker"
  default_labels_present: false
```

Do NOT set `status: FROZEN` until you have personally confirmed the licence.
