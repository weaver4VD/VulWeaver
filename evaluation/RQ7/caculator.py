import numpy as np
from sklearn.metrics import cohen_kappa_score

def calculate_binary_kappa(annotator1_labels, annotator2_labels):
    # Step 1: Data type conversion and validation (for bit vector scenarios)
    # Convert to numpy array, ensure integer type with 0/1 values
    ann1 = np.array(annotator1_labels, dtype=int)
    ann2 = np.array(annotator2_labels, dtype=int)
    
    # Validation 1: Both label arrays must have the same length
    if len(ann1) != len(ann2):
        raise ValueError("Error: Both annotators must have the same number of labels!")
    
    # Validation 2: Labels can only be 0 or 1 (bit vector validity check)
    if not np.all(np.isin(ann1, [0, 1])) or not np.all(np.isin(ann2, [0, 1])):
        raise ValueError("Error: Labels must be bit vectors containing only 0 and 1!")
    
    # Validation 3: Avoid empty arrays
    if len(ann1) == 0:
        raise ValueError("Error: Label arrays cannot be empty!")
    
    # Step 2: Call sklearn library function to calculate kappa value (core)
    kappa = cohen_kappa_score(ann1, ann2)
    
    # Step 3: Interpret kappa value (based on common standards)
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
    
    # Output results
    print(f"===== Kappa Calculation Results =====")
    print(f"Kappa value between two annotators: {kappa:.4f}")
    print(f"Agreement interpretation: {interpretation}")
    
    return kappa

# ------------------- Test Example (replace with your own bit vectors) -------------------
if __name__ == "__main__":
    # Simulated 0/1 bit vector labels (replace with actual data)
    annotator1 = [0, 1, 1, 1, 0, 1, 0, 1]  # First annotator's labels
    annotator2 = [0, 1, 1, 1, 1, 1, 0, 1]  # Second annotator's labels
    
    # Call function to calculate
    kappa_value = calculate_binary_kappa(annotator1, annotator2)