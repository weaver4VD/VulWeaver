import numpy as np
from sklearn.metrics import cohen_kappa_score

def calculate_binary_kappa(annotator1_labels, annotator2_labels):
    ann1 = np.array(annotator1_labels, dtype=int)
    ann2 = np.array(annotator2_labels, dtype=int)
    if len(ann1) != len(ann2):
        raise ValueError("Error: Both annotators must have the same number of labels!")
    if not np.all(np.isin(ann1, [0, 1])) or not np.all(np.isin(ann2, [0, 1])):
        raise ValueError("Error: Labels must be bit vectors containing only 0 and 1!")
    if len(ann1) == 0:
        raise ValueError("Error: Label arrays cannot be empty!")
    kappa = cohen_kappa_score(ann1, ann2)
    def interpret_kappa(k):
        if k >= 0.8:
            return "Almost perfect agreement"
        elif k >= 0.6:
            return "Substantial agreement"
        elif k >= 0.4:
            return "Moderate agreement"
        elif k >= 0.2:
            return "Fair agreement"
        elif k >= 0:
            return "Slight agreement"
        else:
            return "Agreement worse than random (anomalous)"
    
    interpretation = interpret_kappa(kappa)
    print(f"===== Kappa Calculation Results =====")
    print(f"Kappa value between two annotators: {kappa:.4f}")
    print(f"Agreement interpretation: {interpretation}")
    
    return kappa
if __name__ == "__main__":
    annotator1 = [0, 1, 1, 1, 0, 1, 0, 1]
    annotator2 = [0, 1, 1, 1, 1, 1, 0, 1]
    kappa_value = calculate_binary_kappa(annotator1, annotator2)