"""Step 10: the tables of the short report comparing the model trained on TotalSegmentator
with the one trained on the VerSe19 training set.

What it does
  Writes the two tables of the original project's report, in the same layout, with the
  new numbers added, plus one table of extra comparison numbers:
  Table 1  header and label anomalies (columns TS and VS as in the original report, plus
           VS train: the VerSe19 training set this project trains on),
  Table 2  Dice per vertebra on the same two test sets, one row per model and test set,
  Table 3  counting errors, false-positive levels, body centres.
  Every number is read from the result files; nothing is typed in by hand. A test set that
  a model has not been evaluated on yet is marked as such.

Needs
  outputs/qc/anomalies_per_case_<source>.csv            step 1, all five sources
  outputs/evaluation_totalseg_1.5mm/, predictions_...   TotalSegmentator-trained model (copied
                                                        from the original project, step 6 there)
  outputs/evaluation_verse_1mm/, predictions_...        VerSe-trained model (step 6 here)

Output
  report/comparison_tables.tex   included by report/short_comparison_report.tex (hand-written
                                 text); build the PDF with: tectonic report/short_comparison_report.tex

    python scripts/10_write_short_comparison_report.py
"""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from lumbar.labels import NAME_TO_ID, TARGET_LEVELS
from lumbar.sources import PROJECT_ROOT, QC_REPORTS_DIR

OUTPUTS = PROJECT_ROOT / "outputs"
TABLES = PROJECT_ROOT / "report" / "comparison_tables.tex"
MODELS = {  # row name -> (evaluation tag, voxel size in mm)
    "TotalSegmentator (902 scans)": ("totalseg_1.5mm", 1.5),
    "VerSe19 training set (56 scans)": ("verse_1mm", 1.0),
}
TEST_SETS = {"TotalSegmentator v3 test (in-domain)": "TotalSegmentator test (78 scans)",
             "VerSe19 val + test (out-of-domain)": "VerSe19 val + test (67 scans)"}

# Table 1 of the original report: (anomaly, how detected, how handled, how it is counted
# from the step-1 CSV). A None row is the line between the header block and the content block.
ANOMALY_ROWS = [
    ("Image not stored axially (PIR, PSR, LAS)", "orientation codes of the affine", "resampled to RAS",
     lambda a, f: f("NONAXIAL")),
    ("Thick slices (more than 3$\\times$ the in-plane size)$^{a}$", "voxel sizes", "smoothed before downsampling",
     lambda a, f: f("ANISO")),
    ("Only qform or only sform set", "header codes", "the one that is set is used",
     lambda a, f: int(((a["img_qform_code"] == 0) | (a["img_sform_code"] == 0)).sum())),
    ("CT stored as float, HU not whole numbers", "data type and values", "accepted (resampled by provider)",
     lambda a, f: int((a["img_dtype"] == "float32").sum())),
    ("Label and CT affines differ by $\\le$\\,0.001\\,mm", "affine difference", "treated as the same grid",
     lambda a, f: f("LABEL_AFFINE_EPS")),
    ("Label mask stored as float", "data type", "rounded to whole numbers", lambda a, f: f("LABEL_FLOAT")),
    None,
    ("Two masks claim the same voxel (mostly S1 and L5)", "overlap of the masks", "the lumbar level wins",
     lambda a, f: f("MASK_OVERLAP")),
    ("Padding below $-2000$\\,HU outside the scan circle", "share of such voxels", "set to air by the HU window",
     lambda a, f: f("PAD_OUTSIDE_FOV")),
    ("Metal near the spine", "$>$\\,0.5\\,ml above 3000\\,HU", "clipped at 1500\\,HU, flagged", lambda a, f: f("METAL")),
    ("Vertebra cut off by the scan edge", "mask touches the border", "kept; Dice also reported without",
     lambda a, f: f("TRUNCATED")),
    ("No lumbar vertebra in the scan", "label content", "excluded from training", lambda a, f: f("NO_LUMBAR")),
    ("Sixth lumbar vertebra (L6)", "VerSe label 25", "own class; excluded from training$^{b}$",
     lambda a, f: f("TRANSITIONAL_L6")),
]
ANOMALY_COLUMNS = {"TS": ["totalseg_v3_train", "totalseg_v3_test"],
                   "VS": ["verse19_validation", "verse19_test"],
                   "VS train": ["verse19_training"]}


def anomaly_table() -> list[str]:
    counts = {}
    for col, sources in ANOMALY_COLUMNS.items():
        a = pd.concat([pd.read_csv(QC_REPORTS_DIR / f"anomalies_per_case_{s}.csv") for s in sources])
        flags = a["flags"].fillna("").str.split()
        has = lambda code, flags=flags: int(flags.map(lambda x: code in x).sum())
        counts[col] = [None if row is None else row[3](a, has) for row in ANOMALY_ROWS]
    L = [r"\begin{table}[h]", r"\centering\footnotesize",
         r"\caption{Anomalies found by the automatic check (Table~1 of the original report, same rules), with the "
         r"detection and handling of each. Counts are numbers of scans: TS = TotalSegmentator (1939), "
         r"VS = VerSe19 validation + test (80), \textbf{VS train = VerSe19 training set (80), used here for training}. "
         r"Upper block: header; lower block: image and label content. "
         r"$^{a}$Five VS-train scans have exactly 3$\times$ (1\,$\times$\,1\,$\times$\,3\,mm) and are not counted. "
         r"$^{b}$The network has no L6 class; the 3 VS-train scans with L6 are not used for training.}",
         r"\label{tab:anom}",
         r"\begin{tabularx}{\linewidth}{@{}l>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}Xrrr@{}}",
         r"\toprule", r"Anomaly & How detected & How handled & TS & VS & \textbf{VS train}\\", r"\midrule"]
    for i, row in enumerate(ANOMALY_ROWS):
        if row is None:
            L.append(r"\midrule")
            continue
        L.append(f"{row[0]} & {row[1]} & {row[2]} & {counts['TS'][i]} & {counts['VS'][i]} & "
                 f"\\textbf{{{counts['VS train'][i]}}}\\\\")
    return L + [r"\bottomrule", r"\end{tabularx}", r"\end{table}"]


def dice_cell(s: pd.Series) -> str:
    return f"{s.mean():.2f} / {s.median():.2f}".replace("0.", ".")


def dice_table() -> list[str]:
    L = [r"\begin{table}[h]", r"\centering\footnotesize",
         r"\caption{Dice per vertebra on the two test sets, mean / median (Table~2 of the original report, with a "
         r"row for each model). \emph{Limit}: Dice of the ground truth after resampling to the model's voxel size "
         r"and back, i.e.\ the highest score possible at that voxel size. $n$: number of scored vertebrae.}",
         r"\label{tab:dice}", r"\begin{tabular}{@{}llcccccccc@{}}", r"\toprule",
         r"Test set & Trained on (voxel size) & L1 & L2 & L3 & L4 & L5 & All & Limit & $n$\\", r"\midrule"]
    for k, (group, test_name) in enumerate(TEST_SETS.items()):
        if k:
            L.append(r"\midrule")
        for j, (model, (tag, mm)) in enumerate(MODELS.items()):
            lv = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "dice_per_level.csv")
            d = lv[(lv["group"] == group) & ~lv["fragment"]]
            first = test_name if j == 0 else ""
            if d.empty:
                L.append(f"{first} & {model} ({mm:g}\\,mm) & \\multicolumn{{8}}{{c}}{{\\emph{{not evaluated yet}}}}\\\\")
                continue
            levels = " & ".join(dice_cell(d.loc[d["level"] == n, "dice"]) for n in TARGET_LEVELS)
            L.append(f"{first} & {model} ({mm:g}\\,mm) & {levels} & \\textbf{{{dice_cell(d['dice'])}}} & "
                     f"{d['dice_ceiling'].mean():.2f} & {len(d)}\\\\".replace("& 0.", "& ."))
    return L + [r"\bottomrule", r"\end{tabular}", r"\end{table}"]


def extra_numbers(tag: str) -> dict:
    """Counting errors, false-positive levels and body-centre distances per test set."""
    lv = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "dice_per_level.csv")
    ct = pd.read_csv(OUTPUTS / f"evaluation_{tag}" / "centroid_distances.csv")
    out = {}
    for group in TEST_SETS:
        d = lv[(lv["group"] == group) & ~lv["fragment"]]
        if d.empty:                  # this test set has not been evaluated (step 6 --source)
            out[group] = None
            continue
        per_case = d.groupby("case_id")[["dice", "dice_if_pred_one_level_up", "dice_if_pred_one_level_down"]].mean()
        gain = per_case[["dice_if_pred_one_level_up", "dice_if_pred_one_level_down"]].max(axis=1) - per_case["dice"]
        c = ct[ct["group"] == group]["pred_body_to_gt_body_mm"].dropna()
        out[group] = {"complete": f"{d.loc[~d['truncated'], 'dice'].mean():.2f}".replace("0.", "."),
                      "miscounted": str(int((gain > 0.1).sum())),
                      "centre": f"{c.median():.1f} / {c.quantile(0.9):.1f}", "fp_cases": 0, "fp_big": 0}
    pred_dir = OUTPUTS / f"predictions_{tag}"
    for p in sorted((OUTPUTS / f"evaluation_{tag}" / "per_case").glob("*/*.json")):
        r = json.loads(p.read_text())
        group = next(g for g in TEST_SETS if g.startswith("TotalSeg" if r["source"].startswith("totalseg") else "VerSe"))
        if not r["false_positive_levels"] or out[group] is None:   # skip cached cases of an unfinished test set
            continue
        img = nib.load(pred_dir / r["source"] / f"{r['case_id']}_predicted_labels.nii.gz")
        lab, voxel_ml = np.asarray(img.dataobj), float(abs(np.linalg.det(img.affine[:3, :3]))) / 1000
        out[group]["fp_cases"] += 1
        out[group]["fp_big"] += sum(float((lab == NAME_TO_ID[n]).sum()) * voxel_ml >= 20 for n in r["false_positive_levels"])
    return out


def extra_table() -> list[str]:
    extras = {m: extra_numbers(tag) for m, (tag, _) in MODELS.items()}
    short = {m: m.split(" (")[0].replace("VerSe19 training set", "VerSe19 train") for m in MODELS}
    L = [r"\begin{table}[h]", r"\centering\footnotesize",
         r"\caption{Further comparison numbers. \emph{Counted one level off}: renaming all predicted levels by one "
         r"raises the scan's mean Dice by more than 0.1. \emph{Whole-vertebra false positives}: predicted levels "
         r"absent from the ground truth and at least 20\,ml large. \emph{Body centre}: distance between the "
         r"predicted and the ground-truth vertebral body centre, median / 90th percentile.}",
         r"\label{tab:extra}", r"\begin{tabular}{@{}l" + "c" * (len(MODELS) * len(TEST_SETS)) + "@{}}", r"\toprule",
         " & " + " & ".join(f"\\multicolumn{{{len(MODELS)}}}{{c}}{{{t}}}" for t in TEST_SETS.values()) + r"\\",
         "Trained on & " + " & ".join(short[m] for _ in TEST_SETS for m in MODELS) + r"\\", r"\midrule"]
    rows = [("Dice, complete vertebrae only (mean)", "complete"), ("Scans counted one level off", "miscounted"),
            ("Scans with a false-positive level", "fp_cases"), ("Whole-vertebra false positives", "fp_big"),
            ("Body centre distance (mm)", "centre")]
    for text, key in rows:
        cells = [("--" if extras[m][g] is None else str(extras[m][g][key])) for g in TEST_SETS for m in MODELS]
        L.append(f"{text} & " + " & ".join(cells) + r"\\")
    return L + [r"\bottomrule", r"\end{tabular}", r"\end{table}"]


def main():
    L = ["% Generated by lumbar/scripts/10_write_short_comparison_report.py -- do not edit by hand.", ""]
    L += anomaly_table() + [""] + dice_table() + [""] + extra_table()
    TABLES.parent.mkdir(parents=True, exist_ok=True)
    TABLES.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[report] tables -> {TABLES}")


if __name__ == "__main__":
    main()
