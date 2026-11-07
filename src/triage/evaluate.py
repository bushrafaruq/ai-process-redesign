"""Evaluate a classifier on the labelled test set.

Usage:
    python -m triage.evaluate                 # baseline, no API key needed
    python -m triage.evaluate --llm           # LLM classifier (needs ANTHROPIC_API_KEY or OPENAI_API_KEY)

Writes outputs/eval_<model>.json, outputs/eval_<model>.md and a confusion matrix PNG.

Metrics are chosen for the operational risk, not just accuracy:
* P1 recall          - share of truly urgent requests the agent marks urgent (a miss is the worst error)
* safety recall      - share of true safety requests that are escalated
* quick-approve precision - how often the one-click suggestion is right (drives coordinator trust)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from .agent import TriageAgent
from .classifier import BaselineClassifier, LLMClassifier
from .taxonomy import CATEGORIES

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f1_per_class(y_true, y_pred, labels):
    out = {}
    for lab in labels:
        tp = sum(t == lab and p == lab for t, p in zip(y_true, y_pred))
        fp = sum(t != lab and p == lab for t, p in zip(y_true, y_pred))
        fn = sum(t == lab and p != lab for t, p in zip(y_true, y_pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[lab] = {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3),
                    "support": sum(t == lab for t in y_true)}
    return out


def run(classifier, test_path: Path, out_dir: Path, threshold: float) -> dict:
    rows = load(test_path)
    agent = TriageAgent(classifier, audit_path=out_dir / "eval_audit_log.jsonl", threshold=threshold)
    (out_dir / "eval_audit_log.jsonl").unlink(missing_ok=True)
    results = []
    for r in rows:
        p = agent.propose(r["text"], request_id=r["id"])
        results.append({**r, "pred_category": p.category, "pred_priority": p.priority,
                        "confidence": p.confidence, "safety_flag": p.safety_flag,
                        "review_mode": p.review_mode, "model": p.model})

    n = len(results)
    yt = [r["category"] for r in results]
    yp = [r["pred_category"] for r in results]
    labels = list(CATEGORIES)
    per_class = f1_per_class(yt, yp, labels)
    present = [lab for lab in labels if per_class[lab]["support"]]
    macro_f1 = sum(per_class[lab]["f1"] for lab in present) / len(present)

    true_p1 = [r for r in results if r["priority"] == "P1"]
    true_safety = [r for r in results if r["category"] == "safety_security"]
    modes = Counter(r["review_mode"] for r in results)
    quick = [r for r in results if r["review_mode"] == "QUICK_APPROVE"]
    over_escalated = [r for r in results if r["pred_priority"] == "P1" and r["priority"] != "P1"]
    fallbacks = sum("fallback" in r["model"] for r in results)

    metrics = {
        "model": results[0]["model"] if results else "n/a",
        "n": n,
        "confidence_threshold": threshold,
        "category_accuracy": round(sum(a == b for a, b in zip(yt, yp)) / n, 3),
        "category_macro_f1": round(macro_f1, 3),
        "priority_accuracy": round(sum(r["priority"] == r["pred_priority"] for r in results) / n, 3),
        "p1_recall": round(sum(r["pred_priority"] == "P1" for r in true_p1) / len(true_p1), 3),
        "p1_count": len(true_p1),
        "safety_escalation_recall": round(
            sum(r["review_mode"] == "ESCALATE_NOW" for r in true_safety) / len(true_safety), 3),
        "over_escalated_to_p1": len(over_escalated),
        "review_mode_share": {k: round(v / n, 3) for k, v in sorted(modes.items())},
        "quick_approve_precision": round(
            sum(r["category"] == r["pred_category"] for r in quick) / len(quick), 3) if quick else None,
        "llm_fallbacks": fallbacks,
        "per_class": per_class,
        "errors": [{"id": r["id"], "text": r["text"], "true": f'{r["category"]}/{r["priority"]}',
                    "pred": f'{r["pred_category"]}/{r["pred_priority"]}', "conf": r["confidence"],
                    "mode": r["review_mode"]}
                   for r in results if (r["category"], r["priority"]) != (r["pred_category"], r["pred_priority"])],
    }

    slug = re.sub(r"[^a-z0-9]+", "_", metrics["model"].lower()).strip("_")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"eval_{slug}.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out_dir / f"eval_{slug}.md").write_text(to_markdown(metrics), encoding="utf-8")
    confusion_png(yt, yp, labels, out_dir / f"confusion_{slug}.png", metrics["model"])
    return metrics


def to_markdown(m: dict) -> str:
    lines = [f"# Evaluation: `{m['model']}`", "",
             f"Test set: {m['n']} hand-labelled synthetic requests. Confidence threshold: {m['confidence_threshold']}.", "",
             "| Metric | Value |", "|---|---|"]
    for k in ["category_accuracy", "category_macro_f1", "priority_accuracy", "p1_recall",
              "safety_escalation_recall", "over_escalated_to_p1", "quick_approve_precision", "llm_fallbacks"]:
        lines.append(f"| {k} | {m[k]} |")
    lines.append(f"| review_mode_share | {m['review_mode_share']} |")
    lines += ["", "## Per category", "", "| Category | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
    for lab, v in m["per_class"].items():
        lines.append(f"| {lab} | {v['precision']} | {v['recall']} | {v['f1']} | {v['support']} |")
    lines += ["", f"## Errors ({len(m['errors'])})", "", "| ID | True | Predicted | Conf | Mode | Text |", "|---|---|---|---|---|---|"]
    for e in m["errors"]:
        lines.append(f"| {e['id']} | {e['true']} | {e['pred']} | {e['conf']} | {e['mode']} | {e['text'].replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def confusion_png(yt, yp, labels, path: Path, title: str) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    idx = {lab: i for i, lab in enumerate(labels)}
    mat = [[0] * len(labels) for _ in labels]
    for t, p in zip(yt, yp):
        mat[idx[t]][idx[p]] += 1
    short = [CATEGORIES[lab].label for lab in labels]
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(mat, cmap="Blues")
    ax.set_xticks(range(len(labels)), short, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), short, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if mat[i][j]:
                ax.text(j, i, mat[i][j], ha="center", va="center", fontsize=8,
                        color="white" if mat[i][j] > 4 else "black")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Category confusion matrix: {title}", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use the LLM classifier")
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--test", default=str(ROOT / "data" / "test_set.csv"))
    ap.add_argument("--out", default=str(ROOT / "outputs"))
    args = ap.parse_args()
    clf = LLMClassifier() if args.llm else BaselineClassifier()
    m = run(clf, Path(args.test), Path(args.out), args.threshold)
    keys = ["model", "category_accuracy", "category_macro_f1", "priority_accuracy", "p1_recall",
            "safety_escalation_recall", "over_escalated_to_p1", "quick_approve_precision", "review_mode_share"]
    for k in keys:
        print(f"{k:28s} {m[k]}")
    print(f"{'errors':28s} {len(m['errors'])} (see outputs/eval_*.md)")


if __name__ == "__main__":
    main()
