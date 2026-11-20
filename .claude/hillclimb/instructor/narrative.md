| round | change | pass | judge | $/run |
|---|---|---|---|---|
| 0 | baseline, original rubric | 0.81 | Opus 5.5 | $2.89 |
| 0 | baseline re-graded, clarified rubric | 0.74 | Opus 5.5 | (re-grade $2.00) |
| - | calibration: same answers, clarified rubric | 0.44 | Haiku 5.5 (65% agreement) | (re-grade $0.07) |

Stopped before round 1 (owner's decision, cost). The calibration showed the
original rubric left claims about exams undefined, so Opus graded them
inconsistently; the clarified rubric fixed that and lowered the baseline
to 0.74. Haiku cannot replace Opus as judge (65% agreement). The planned
changes (labels, prompt, effort, page split) are untried.
