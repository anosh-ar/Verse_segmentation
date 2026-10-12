# Part D: evaluation on the test sets

Made by `scripts/06_evaluate_on_test_sets.py`. Scoring rules: `lumbar/src/lumbar/evaluation.py`. Dice on the original CT grid; a level is scored only where the ground truth has it (label scraps < 2 ml excluded). Cells: mean / median (number of vertebrae).

### Dice per vertebra (strict)

| Test set | L1 | L2 | L3 | L4 | L5 | all |
|---|---|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 0.578 / 0.771 (66) | 0.717 / 0.945 (62) | 0.834 / 0.942 (60) | 0.826 / 0.936 (59) | 0.861 / 0.928 (58) | 0.758 / 0.933 (305) |

### Dice per vertebra, complete vertebrae only (not cut off by the scan edge)

| Test set | L1 | L2 | L3 | L4 | L5 | all |
|---|---|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 0.596 / 0.813 (63) | 0.729 / 0.945 (59) | 0.852 / 0.943 (57) | 0.836 / 0.935 (56) | 0.858 / 0.927 (55) | 0.769 / 0.934 (290) |

### Resampling ceiling (ground truth -> 1 mm -> back; best possible at 1 mm)

| Test set | L1 | L2 | L3 | L4 | L5 | all |
|---|---|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 0.999 / 1.000 (66) | 0.999 / 1.000 (62) | 0.999 / 1.000 (60) | 0.999 / 1.000 (59) | 0.999 / 1.000 (58) | 0.999 / 1.000 (305) |

### Dice per vertebra, without the L6 patients

| Test set | L1 | L2 | L3 | L4 | L5 | all |
|---|---|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 0.581 / 0.813 (63) | 0.730 / 0.945 (59) | 0.860 / 0.943 (57) | 0.853 / 0.937 (56) | 0.892 / 0.930 (55) | 0.778 / 0.935 (290) |

### Level counting: does renaming the predicted levels by one step fit better?

| Test set | cases with a scored level | best: as predicted | best: one level up | best: one level down |
|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 67 | 59 | 3 | 5 |

Cases where a one-level renaming raises the mean Dice by more than 0.1 (the model found the vertebrae but counted them wrong): sub-verse023 (one level up: 0.25 -> 0.59), sub-verse067 (one level down: 0.33 -> 0.49), sub-verse083 (one level up: 0.01 -> 0.95), sub-verse085 (one level up: 0.00 -> 0.84), sub-verse150 (one level down: 0.00 -> 0.83), sub-verse252 (one level down: 0.00 -> 0.96), sub-verse417_split-verse277 (one level down: 0.00 -> 0.96)

### Levels predicted where the ground truth has none

Size matters: a speck of a few voxels and a whole extra vertebra are different errors. A lumbar vertebra is about 60 ml; 'vertebra-sized' = 20 ml or more.

| Test set | cases | cases with a false-positive level | of these: no lumbar level in the ground truth | false-positive levels: median size | vertebra-sized ones |
|---|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 80 | 23 | 13 | 30.6 ml (94) | 72 |

Vertebra-sized false-positive levels: sub-verse116 L3 118 ml, sub-verse252 L5 77 ml (touches scan edge), sub-verse205 L5 74 ml (touches scan edge), sub-verse205 L4 69 ml (touches scan edge), sub-verse011 L2 61 ml (touches scan edge), sub-verse116 L2 60 ml, sub-verse011 L1 59 ml (touches scan edge), sub-verse011 L5 57 ml, sub-verse011 L4 56 ml (touches scan edge), sub-verse150 L3 56 ml, sub-verse116 L1 55 ml, sub-verse059 L3 54 ml (touches scan edge), sub-verse119 L3 53 ml, sub-verse011 L3 53 ml (touches scan edge), sub-verse242 L3 53 ml, sub-verse412_split-verse235 L1 49 ml, sub-verse059 L2 48 ml (touches scan edge), sub-verse119 L2 48 ml, sub-verse416_split-verse247 L4 47 ml, sub-verse221 L4 46 ml, sub-verse205 L1 46 ml (touches scan edge), sub-verse205 L3 44 ml (touches scan edge), sub-verse417_split-verse277 L2 44 ml, sub-verse221 L2 43 ml, sub-verse404_split-verse209 L5 43 ml, sub-verse250 L4 42 ml, sub-verse125 L3 41 ml, sub-verse417_split-verse277 L3 40 ml (touches scan edge), sub-verse416_split-verse247 L5 39 ml (touches scan edge), sub-verse250 L5 39 ml (touches scan edge), sub-verse116 L4 38 ml, sub-verse217 L4 37 ml, sub-verse125 L2 37 ml, sub-verse400_split-verse090 L3 36 ml, sub-verse404_split-verse209 L4 35 ml, sub-verse221 L5 35 ml, sub-verse416_split-verse247 L3 34 ml, sub-verse225 L2 33 ml, sub-verse242 L1 33 ml (touches scan edge), sub-verse400_split-verse090 L4 32 ml, sub-verse250 L2 32 ml, sub-verse221 L3 32 ml, sub-verse412_split-verse235 L4 32 ml, sub-verse414_split-verse241 L2 31 ml, sub-verse400_split-verse090 L5 31 ml, sub-verse414_split-verse241 L4 31 ml, sub-verse416_split-verse247 L2 31 ml (touches scan edge), sub-verse225 L1 30 ml, sub-verse012 L4 30 ml, sub-verse217 L5 30 ml, sub-verse250 L3 30 ml, sub-verse404_split-verse209 L2 30 ml, sub-verse217 L1 29 ml, sub-verse414_split-verse241 L5 29 ml, sub-verse230 L3 29 ml, sub-verse230 L1 29 ml, sub-verse230 L4 29 ml, sub-verse225 L5 28 ml, sub-verse217 L2 28 ml, sub-verse250 L1 28 ml (touches scan edge), sub-verse205 L2 28 ml (touches scan edge), sub-verse230 L5 26 ml, sub-verse225 L4 26 ml, sub-verse217 L3 25 ml, sub-verse404_split-verse209 L3 25 ml, sub-verse400_split-verse090 L1 25 ml, sub-verse414_split-verse241 L3 24 ml, sub-verse225 L3 23 ml, sub-verse059 L4 21 ml, sub-verse414_split-verse241 L1 21 ml, sub-verse412_split-verse235 L3 21 ml, sub-verse125 L4 20 ml

### Patients with a sixth lumbar vertebra (L6)

| Case | L1 | L2 | L3 | L4 | L5 | best renaming |
|---|---|---|---|---|---|---|
| sub-verse023 | 0.77 | 0.40 | 0.05 | 0.02 | 0.01 | one level up |
| sub-verse083 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | one level up |
| sub-verse131 | 0.74 | 0.95 | 0.96 | 0.96 | 0.87 | as predicted |

### Lowest mean Dice per test set (for a visual check)

- VerSe19 val + test (out-of-domain): sub-verse059 0.00 [NONAXIAL LABEL_AFFINE_EPS TRUNCATED]; sub-verse119 0.00 [NONAXIAL LABEL_AFFINE_EPS TRUNCATED]; sub-verse125 0.00 []; sub-verse150 0.00 []; sub-verse417_split-verse277 0.00 [NONAXIAL LABEL_AFFINE_EPS SPLIT_SCAN]; sub-verse252 0.00 [NONAXIAL LABEL_AFFINE_EPS TRUNCATED]; sub-verse085 0.00 []; sub-verse083 0.01 [NONAXIAL LABEL_AFFINE_EPS TRANSITIONAL_L6]

## Part C: vertebral body centres

Distances in mm: median / 90th percentile (number of vertebrae). 'VerSe point' = the annotated centroid in VerSe, which marks the vertebral body centre (Part A).

| Test set | predicted body vs ground-truth body | predicted body vs VerSe point | ground-truth body vs VerSe point | ground-truth whole vertebra vs VerSe point |
|---|---|---|---|---|
| VerSe19 val + test (out-of-domain) | 0.9 / 34.3 (305) | 2.0 / 34.3 (305) | 0.9 / 4.1 (305) | 12.4 / 14.6 (305) |

Of 305 predicted vertebrae that also exist in the ground truth, 1 were too small to separate the body (mostly cut off by the scan edge); their whole-vertebra centre is used.

Inference + scoring time per case on this machine: median 16 s, max 152 s.
