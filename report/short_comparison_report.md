# VerSe-trained vs TotalSegmentator-trained model: short comparison

Same network, loss, optimiser, 11 000 training steps and checkpoint rule; same test sets. Only the training data (and with it the voxel size) differ:

- **TotalSeg-trained**: TotalSegmentator v3 train, 902 scans, 1.5 mm voxels.
- **VerSe-trained**: VerSe19 training set, 56 scans, 1 mm voxels.

## Table 1: header and label anomalies (number of scans)

The columns TS and VS test sets are the original report's Table 1, recomputed with the same rules; VS train is the VerSe19 training set used here.

| Anomaly | TS (1939) | VS test sets (80) | VS train (80) |
|---|---:|---:|---:|
| Image not stored axially (PIR, PSR, LAS) | 0 | 48 | 41 |
| Thick slices (more than 3x the in-plane size) | 0 | 4 | 0 |
| Only qform or only sform set | 1939 | 80 | 80 |
| CT stored as float, HU not whole numbers | 0 | 77 | 73 |
| Label and CT affines differ by <= 0.001 mm | 228 | 36 | 28 |
| Label mask stored as float | 0 | 1 | 0 |
| Two masks claim the same voxel (mostly S1 and L5) | 817 | 0 | 0 |
| Padding below -2000 HU outside the scan circle | 104 | 0 | 0 |
| Metal near the spine | 124 | 4 | 4 |
| Vertebra cut off by the scan edge | 431 | 8 | 4 |
| No lumbar vertebra in the scan | 720 | 13 | 15 |
| Sixth lumbar vertebra (L6) | 0 | 3 | 3 |

## Table 2: Dice per vertebra on the two test sets, mean / median

*Limit*: Dice of the ground truth after resampling to the model's voxel size and back (the best possible at that voxel size). *n*: scored vertebrae. Dice on the original CT grid.

| Test set | Trained on | L1 | L2 | L3 | L4 | L5 | All | Limit | n |
|---|---|---|---|---|---|---|---|---|---|
| TotalSegmentator test (78 scans) | TotalSeg-trained (1.5 mm) | .88 / .97 | .90 / .97 | .92 / .97 | .91 / .97 | .87 / .96 | **.89 / .97** | 1.00 | 328 |
| TotalSegmentator test (78 scans) | VerSe-trained (1 mm) | not evaluated yet |  |  |  |  |  |  |  |
| VerSe19 val + test (67 scans) | TotalSeg-trained (1.5 mm) | .90 / .94 | .91 / .94 | .92 / .94 | .91 / .94 | .89 / .93 | **.91 / .94** | 0.96 | 305 |
| VerSe19 val + test (67 scans) | VerSe-trained (1 mm) | .58 / .77 | .72 / .94 | .83 / .94 | .83 / .94 | .86 / .93 | **.76 / .93** | 1.00 | 305 |

## Extra comparison numbers

| | TotalSeg-trained, TotalSegmentator test | VerSe-trained, TotalSegmentator test | TotalSeg-trained, VerSe19 val + test | VerSe-trained, VerSe19 val + test |
|---|---|---|---|---|
| Dice, complete vertebrae only (mean) | 0.921 |  | 0.913 | 0.769 |
| Scans counted one level off | 2 | not evaluated yet | 1 | 7 |
| Scans with a false-positive level | 52 |  | 23 | 23 |
| Whole-vertebra false positives (>= 20 ml) | 11 |  | 26 | 72 |
| Body centre vs ground-truth body, median / 90th pct (mm) | 0.3 / 15.7 |  | 0.6 / 3.9 | 0.9 / 34.3 |

## Findings (VerSe test sets; the TotalSegmentator test set is not evaluated yet for the VerSe-trained model)

- **On a typical VerSe scan both models segment equally well** (median Dice .93 vs .94), even though the
  VerSe-trained model saw only 56 training scans and works at 1 mm, where VerSe loses nothing to resampling
  (limit 1.00 vs .96).
- **The VerSe-trained model is clearly worse on average** (mean Dice .76 vs .91). The loss is in *naming*,
  not in outlining: 7 scans are counted one level off (TotalSeg-trained: 1), and L1 suffers most
  (mean .58 vs .90).
- **It labels neck and upper thoracic vertebrae as lumbar far more often**: 72 whole-vertebra false
  positives (TotalSeg-trained: 26). Underneath them in the ground truth: neck vertebrae C1–C7 in 32 cases
  (TotalSeg-trained: 8), thoracic vertebrae in 13 (5), unlabelled bone in 21 (12), and real lumbar
  vertebrae with the wrong level name in 6 (1). Many VerSe test scans show the whole spine; both models were
  trained only on lumbar crops (T12 to sacrum), but with 56 instead of 902 scans the VerSe-trained model has
  learned much less well what is *not* a lumbar vertebra. Because the clean-up keeps only the largest piece
  per class, a wrongly named neck vertebra can even replace the real L1.
- **Body centres**: median distance similar (0.9 vs 0.6 mm), but the 90th percentile is 34 mm vs 4 mm:
  the same naming errors put a "body centre" on the wrong vertebra.
- **Takeaway**: more data from another domain beats less data from the target domain here. Training on the
  same kind of scans (VerSe) did not help, because 56 scans are too few to learn level counting on
  whole-spine scans. What would help: more training scans, patches outside the lumbar crop during training,
  or a rule-based level check.
