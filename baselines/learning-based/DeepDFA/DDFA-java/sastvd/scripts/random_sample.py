import csv
import random
import sys

def generate_label_csv(row_num):
    labels = ["train", "val"]
    probabilities = [0.8, 0.2]
    with open("./DDFA-java/storage/external/vulweaver_rand_splits.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "label"])
        for idx in range(0, row_num + 1):
            if idx < 300:
                label = "test"
            else:
                label = random.choices(labels, weights=probabilities, k=1)[0]
            writer.writerow([idx, label])
    

if __name__ == "__main__":
    
    try:
        total_rows = 4779
        if total_rows <= 0:
            sys.exit(1)
    except ValueError:
        sys.exit(1)
    generate_label_csv(total_rows)