# Colleague Detector A/B Test

This directory preserves the experimental colleague's single-class tree detector (`tree_detector_v2.py` and model weights) archived as reference.

### Conclusion & Summary:
The A/B test showed no net improvement in model accuracy or resilience to domain-shift. In fact, it caused a regression in at least one test case by increasing the model's confidence in an incorrect prediction. The fallback logic and main model were preserved without integrating this detector.

See docs/assumptions.md, entry dated 2026-07-20, for the full test methodology and results (11-image and 16-image test-split comparison, domain-shift gap comparison, and 7-image known-species diagnostic set).
