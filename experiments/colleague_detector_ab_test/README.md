# Colleague Detector A/B Test

This directory preserves the experimental colleague's single-class tree detector (`tree_detector_v2.py` and model weights) archived as reference.

### Conclusion & Summary:
The A/B test showed no net improvement in model accuracy or resilience to domain-shift. In fact, it caused a regression in at least one test case by increasing the model's confidence in an incorrect prediction. The fallback logic and main model were preserved without integrating this detector.

For more details, please refer to the submissions/readiness guidelines or historical documentation if applicable.
