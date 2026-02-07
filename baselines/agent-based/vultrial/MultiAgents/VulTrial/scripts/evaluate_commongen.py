import argparse
import json
import spacy
from tqdm import tqdm


nlp = spacy.load("en_core_web_sm")


def coverage_score(preds, concept_sets):
    covs = []
    missings = []
    for p, cs in tqdm(zip(preds, concept_sets), total=len(preds)):
        cs = set(cs)
        lemmas = set()
        for token in nlp(p):
            lemmas.add(token.lemma_)
        cov = len(lemmas & cs) / len(cs)
        covs.append(cov)
        missings.append(cs - lemmas)
    return sum(covs) / len(covs), missings


def scoring(preds, concept_sets):
    coverage, missing_tokens = coverage_score(preds, concept_sets)
    print(f"System level Coverage: {coverage*100:.2f}")
    return coverage, missing_tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="", type=str)
    args = parser.parse_args()

    preds_final = []
    preds_first = []
    concept_sets = []
    with open(args.path) as f:
        for line in f:
            line = json.loads(line)
            preds_final.append(line["response"])
            if line["logs"][0]["module"] == "Role Assigner":
                preds_first.append(line["logs"][1]["content"])
            else:
                preds_first.append(line["logs"][0]["content"])
            concept_sets.append(line["input"])

    scoring(preds_final, concept_sets)
    scoring(preds_first, concept_sets)
