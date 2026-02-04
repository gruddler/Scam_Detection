import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from joblib import dump

BASE_DIR = Path(r"A:\HCL Project")
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CEAS_PATH = DATA_DIR / "CEAS_08.csv"
PHISH_PATH = DATA_DIR / "phishing.csv"
SPAM_PATH = DATA_DIR / "spam.csv"


def load_ceas():
    df = pd.read_csv(CEAS_PATH, encoding="utf-8", on_bad_lines="skip")
    df["subject"] = df["subject"].fillna("")
    df["body"] = df["body"].fillna("")
    df["text"] = (df["subject"].astype(str) + " \n" + df["body"].astype(str)).str.strip()
    df["label"] = df["label"].astype(int)
    return df[["text", "label"]]


def load_phishing():
    df = pd.read_csv(PHISH_PATH, encoding="utf-8", on_bad_lines="skip")
    df["subject"] = df["subject"].fillna("")
    df["body"] = df["body"].fillna("")
    df["text"] = (df["subject"].astype(str) + " \n" + df["body"].astype(str)).str.strip()
    df["label"] = df["label"].astype(int)
    return df[["text", "label"]]


def load_spam():
    df = pd.read_csv(SPAM_PATH, encoding="latin-1", on_bad_lines="skip")
    df = df.rename(columns={"v1": "label_raw", "v2": "text"})
    df["label"] = df["label_raw"].map({"spam": 1, "ham": 0}).astype(int)
    df["text"] = df["text"].fillna("")
    return df[["text", "label"]]


def main():
    df = pd.concat([load_ceas(), load_phishing(), load_spam()], ignore_index=True)
    df = df[df["text"].str.len() > 0].dropna(subset=["label"])

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.9,
                    stop_words="english",
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=200,
                    class_weight="balanced",
                    C=2.0,
                    n_jobs=1,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, preds, average="binary", zero_division=0
    )

    metrics = {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }

    dump(model, MODEL_DIR / "scam_model.joblib")
    with (MODEL_DIR / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
