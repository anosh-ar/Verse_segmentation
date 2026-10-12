"""Step 10: short report comparing the model trained on TotalSegmentator with the one
trained on the VerSe19 training set.

What it does
  Rebuilds the two tables of the original project's report with the new numbers added:
  Table 1  header and label anomalies (columns TS, VS as in the original report, plus
           the VerSe19 training set that this project trains on),
  Table 2  Dice per vertebra on the same two test sets, one row per model and test set,
  plus a few extra comparison numbers (counting errors, false-positive levels, body centres).
  Every number is read from the result files; nothing is typed in by hand.

Needs
  outputs/qc/anomalies_per_case_<source>.csv            step 1, all five sources
  outputs/evaluation_totalseg_1.5mm/, predictions_...   TotalSegmentator-trained model (copied
                                                        from the original project, step 6 there)
  outputs/evaluation_verse_1mm/, predictions_...        VerSe-trained model (step 6 here)

Output
  report/short_comparison_report.md

    python scripts/10_write_short_comparison_report.py
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from lumbar.labels import NAME_TO_ID, TARGET_LEVELS
from lumbar.sources import PROJECT_ROOT, QC_REPORTS_DIR

OUTPUTS = PROJECT_ROOT / "outputs"
REPORT = PROJECT_ROOT / "report" / "short_comparison_report.md"
MODELS = {  # column name -> (evaluation tag, voxel size, training data)
    "TotalSeg-trained": ("totalseg_1.5mm", "1.5 mm", "TotalSegmentator v3 train, 902 scans"),
    "VerSe-trained": ("verse_1mm", "1 mm", "VerSe19 training set, 56 scans"),
}
TEST_SETS = {"TotalSegmentator v3 test (in-domain)": "TotalSegmentator test (78 scans)",
             "VerSe19 val + test (out-of-domain)": "VerSe19 val + test (67 scans)"}

# Table 1 of the original report: (row text, how it is counted from the step-1 CSV)
ANOMALY_ROWS = [
    ("Image not stored axially (PIR, PSR, LAS)", lambda a, f: f("NONAXIAL")),
    ("Thick slices (more than 3x the in-plane size)", lambda a, f: f("ANISO")),
    ("Only qform or only sform set", lambda a, f: int(((a["img_qform_code"] == 0) | (a["img_sform_code"] == 0)).sum())),
    ("CT stored as float, HU not whole numbers", lambda a, f: int((a["img_dtype"] == "float32").sum())),
    ("Label and CT affines differ by <= 0.001 mm", lambda a, f: f("LABEL_AFFINE_EPS")),
    ("Label mask stored as float", lambda a, f: f("LABEL_FLOAT")),
    ("Two masks claim the same voxel (mostly S1 and L5)", lambda a, f: f("MASK_OVERLAP")),
    ("Padding below -2000 HU outside the scan circle", lambda a, f: f("PAD_OUTSIDE_FOV")),
    ("Metal near the spine", lambda a, f: f("METAL")),
    ("Vertebra cut off by the scan edge", lambda a, f: f("TRUNCATED")),
    ("No lumbar vertebra in the scan", lambda a, f: f("NO_LUMBAR")),
    ("Sixth lumbar vertebra (L6)", lambda a, f: f("TRANSITIONAL_L6")),
]
ANOMALY_COLUMNS = {"TS (1939)": ["totalseg_v3_train", "totalseg_v3_test"],
                   "VS test sets (80)": ["verse19_validation", "verse19_test"],
                   "VS train (80)": ["verse19_training"]}


def anomaly_table() -> list[str]:
    counts = {}
    for col, sources in ANOMALY_COLUMNS.items():
        a = pd.concat([pd.read_csv(QC_REPORTS_DIR / f"anomalies_per_case_{s}.csv") for s in sources])
        flags = a["flags"].fillna("").str.split()
        has = lambda code, flags=flags: int(flags.map(lambda x: code in x).sum())
        counts[col] = [rule(a, has) for _, rule in ANOMALY_ROWS]
    L = ["| Anomaly | " + " | ".join(ANOMALY_COLUMNS) + " |", "|---|" + "---:|" * len(ANOMALY_COLUMNS)]
    for i, (text, _) in enumerate(ANOMALY_ROWS):
        L.append(f"| {text} | " + " | ".join(str(counts[c][i]) for c in ANOMALY_COLUMNS) + " |")
    return L


def dice_table() -> list[str]:
    L = ["| Test set | Trained on | " + " | ".join(TARGET_LEVELS) + " | All | Limit | n |",
         "|---|---|" + "---|" * (len(TARGET_LEVELS) + 3)]
    for group, test_name in TEST_SETS.items():
        for model, (tag, mm, _) in MODELS.items():
            lv = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "dice_per_level.csv")
            d = lv[(lv["group"] == group) & ~lv["fragment"]]
            cell = lambda s: f"{s.mean():.2f} / {s.median():.2f}".replace("0.", ".")
            L.append(f"| {test_name} | {model} ({mm}) | "
                     + " | ".join(cell(d.loc[d["level"] == n, "dice"]) for n in TARGET_LEVELS)
                     + f" | **{cell(d['dice'])}** | {d['dice_ceiling'].mean():.2f} | {len(d)} |")
    return L


def extra_numbers(tag: str) -> dict:
    """Counting errors, false-positive levels and body-centre distances per test set."""
    lv = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "dice_per_level.csv")
    ct = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "centroid_distances.csv")
    out = {}
    for group in TEST_SETS:
        d = lv[(lv["group"] == group) & ~lv["fragment"]]
        per_case = d.groupby("case_id")[["dice", "dice_if_pred_one_level_up", "dice_if_pred_one_level_down"]].mean()
        gain = per_case[["dice_if_pred_one_level_up", "dice_if_pred_one_level_down"]].max(axis=1) - per_case["dice"]
        c = ct[ct["group"] == group]["pred_body_to_gt_body_mm"].dropna()
        out[group] = {"miscounted": int((gain > 0.1).sum()),
                      "complete": d.loc[~d["truncated"], "dice"].mean(),
                      "centre": f"{c.median():.1f} / {c.quantile(0.9):.1f}", "fp_cases": 0, "fp_big": 0}
    pred_dir = OUTPUTS / f"predictions_{tag}"
    for p in sorted((OUTPUTS / f"evaluation_{tag}" / "per_case").glob("*/*.json")):
        r = json.loads(p.read_text())
        if not r["false_positive_levels"]:
            continue
        group = next(g for g in TEST_SETS if g.startswith("TotalSeg" if r["source"].startswith("totalseg") else "VerSe"))
        img = nib.load(pred_dir / r["source"] / f"{r['case_id']}_predicted_labels.nii.gz")
        lab, voxel_ml = np.asarray(img.dataobj), float(abs(np.linalg.det(img.affine[:3, :3]))) / 1000
        out[group]["fp_cases"] += 1
        out[group]["fp_big"] += sum(float((lab == NAME_TO_ID[n]).sum()) * voxel_ml >= 20 for n in r["false_positive_levels"])
    return out


def main():
    extras = {m: extra_numbers(tag) for m, (tag, _, _) in MODELS.items()}
    L = ["# VerSe-trained vs TotalSegmentator-trained model: short comparison", "",
         "Same network, loss, optimiser, 11 000 training steps and checkpoint rule; same test sets. "
         "Only the training data (and with it the voxel size) differ:", ""]
    L += [f"- **{m}**: {train}, {mm} voxels." for m, (_, mm, train) in MODELS.items()]
    L += ["", "## Table 1: header and label anomalies (number of scans)", "",
          "The columns TS and VS test sets are the original report's Table 1, recomputed with the same rules; "
          "VS train is the VerSe19 training set used here.", ""]
    L += anomaly_table()
    L += ["", "## Table 2: Dice per vertebra on the two test sets, mean / median", "",
          "*Limit*: Dice of the ground truth after resampling to the model's voxel size and back (the best "
          "possible at that voxel size). *n*: scored vertebrae. Dice on the original CT grid.", ""]
    L += dice_table()
    L += ["", "## Extra comparison numbers", "",
          "| | " + " | ".join(f"{m}, {t.split(' (')[0]}" for t in TEST_SETS.values() for m in MODELS) + " |",
          "|---|" + "---|" * (len(MODELS) * len(TEST_SETS))]
    rows = [("Dice, complete vertebrae only (mean)", lambda e: f"{e['complete']:.3f}"),
            ("Scans counted one level off", lambda e: str(e["miscounted"])),
            ("Scans with a false-positive level", lambda e: str(e["fp_cases"])),
            ("Whole-vertebra false positives (>= 20 ml)", lambda e: str(e["fp_big"])),
            ("Body centre vs ground-truth body, median / 90th pct (mm)", lambda e: e["centre"])]
    for text, get in rows:
        L.append(f"| {text} | " + " | ".join(get(extras[m][g]) for g in TEST_SETS for m in MODELS) + " |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[report] -> {REPORT}")


if __name__ == "__main__":
    main()
