# fixture — malformed-signed-paths (`-P-Q-P`, `+-G`)

Two node records whose signed-path field uses the ASCII hyphen instead of the U+2212 descent operator.

Prediction: rejected — the validator refuses both, and the nodes read refused, never valid (commission §7, K2).
