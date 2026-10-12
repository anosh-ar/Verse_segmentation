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
