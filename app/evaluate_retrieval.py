import json
import os
from collections import defaultdict

from rag.retrieval import retrieve_relevant_documents


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_FILE = os.path.join(BASE_DIR, "evaluation_questions_strict.json")
REPORT_FILE = os.path.join(BASE_DIR, "retrieval_evaluation_report_strict.json")


def normalize(text):
    if not text:
        return ""
    return text.lower().strip()


def keyword_found(text, keyword):
    return normalize(keyword) in normalize(text)


def get_doc_text(doc):
    return doc.get("content", "")


def get_doc_category(doc):
    return doc.get("metadata", {}).get("category", "")


def get_doc_source(doc):
    return doc.get("metadata", {}).get("source", "")


def check_keywords_in_text(text, expected_keywords):
    matched = []
    missed = []

    for keyword in expected_keywords:
        if keyword_found(text, keyword):
            matched.append(keyword)
        else:
            missed.append(keyword)

    return matched, missed


def evaluate_question(item, k=5):
    question = item.get("question", "")
    expected_keywords = item.get("expected_keywords", [])
    expected_category = item.get("expected_category", "")
    expected_source = item.get("expected_source", "")

    docs = retrieve_relevant_documents(question, k=k)

    if not docs:
        return {
            "id": item.get("id", ""),
            "question": question,
            "question_type": item.get("question_type", ""),
            "difficulty": item.get("difficulty", ""),
            "expected_category": expected_category,
            "expected_source": expected_source,
            "expected_keywords": expected_keywords,
            "top_category": "",
            "top_source": "",
            "retrieved_categories": [],
            "retrieved_sources": [],
            "top1_keyword_match": False,
            "top1_category_match": False,
            "category_hit_at_5": False,
            "source_hit_at_5": False,
            "keyword_hit_at_5": False,
            "soft_pass": False,
            "strict_pass": False,
            "matched_keywords_top1": [],
            "missed_keywords_top1": expected_keywords,
            "matched_keywords_at_5": [],
            "missed_keywords_at_5": expected_keywords,
            "top_chunk_preview": "",
        }

    top_doc = docs[0]
    top_text = get_doc_text(top_doc)

    combined_text = " ".join(get_doc_text(doc) for doc in docs)

    retrieved_categories = [get_doc_category(doc) for doc in docs]
    retrieved_sources = [get_doc_source(doc) for doc in docs]

    top_category = get_doc_category(top_doc)
    top_source = get_doc_source(top_doc)

    matched_top1, missed_top1 = check_keywords_in_text(
        top_text,
        expected_keywords
    )

    matched_at_5, missed_at_5 = check_keywords_in_text(
        combined_text,
        expected_keywords
    )

    top1_keyword_match = len(matched_top1) > 0
    keyword_hit_at_5 = len(matched_at_5) > 0

    if expected_category:
        top1_category_match = top_category == expected_category
        category_hit_at_5 = expected_category in retrieved_categories
    else:
        top1_category_match = True
        category_hit_at_5 = True

    if expected_source:
        source_hit_at_5 = expected_source in retrieved_sources
    else:
        source_hit_at_5 = True

    soft_pass = category_hit_at_5 and keyword_hit_at_5

    strict_pass = top1_category_match and top1_keyword_match

    return {
        "id": item.get("id", ""),
        "question": question,
        "question_type": item.get("question_type", ""),
        "difficulty": item.get("difficulty", ""),
        "expected_category": expected_category,
        "expected_source": expected_source,
        "expected_keywords": expected_keywords,
        "top_category": top_category,
        "top_source": top_source,
        "retrieved_categories": retrieved_categories,
        "retrieved_sources": retrieved_sources,
        "top1_keyword_match": top1_keyword_match,
        "top1_category_match": top1_category_match,
        "category_hit_at_5": category_hit_at_5,
        "source_hit_at_5": source_hit_at_5,
        "keyword_hit_at_5": keyword_hit_at_5,
        "soft_pass": soft_pass,
        "strict_pass": strict_pass,
        "matched_keywords_top1": matched_top1,
        "missed_keywords_top1": missed_top1,
        "matched_keywords_at_5": matched_at_5,
        "missed_keywords_at_5": missed_at_5,
        "top_chunk_preview": top_text[:800],
    }


def percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def summarize(results):
    total = len(results)

    soft_passed = sum(1 for r in results if r["soft_pass"])
    strict_passed = sum(1 for r in results if r["strict_pass"])

    top1_category_matches = sum(1 for r in results if r["top1_category_match"])
    top1_keyword_matches = sum(1 for r in results if r["top1_keyword_match"])
    category_hits_at_5 = sum(1 for r in results if r["category_hit_at_5"])
    keyword_hits_at_5 = sum(1 for r in results if r["keyword_hit_at_5"])

    by_category = defaultdict(lambda: {
        "total": 0,
        "soft_passed": 0,
        "strict_passed": 0,
        "top1_category_matches": 0,
        "top1_keyword_matches": 0,
    })

    by_type = defaultdict(lambda: {
        "total": 0,
        "soft_passed": 0,
        "strict_passed": 0,
        "top1_category_matches": 0,
        "top1_keyword_matches": 0,
    })

    for result in results:
        category = result["expected_category"] or "unknown"
        question_type = result["question_type"] or "unknown"

        for group in [by_category[category], by_type[question_type]]:
            group["total"] += 1

            if result["soft_pass"]:
                group["soft_passed"] += 1

            if result["strict_pass"]:
                group["strict_passed"] += 1

            if result["top1_category_match"]:
                group["top1_category_matches"] += 1

            if result["top1_keyword_match"]:
                group["top1_keyword_matches"] += 1

    summary = {
        "total": total,

        "soft_passed": soft_passed,
        "soft_accuracy": percentage(soft_passed, total),

        "strict_passed": strict_passed,
        "strict_accuracy": percentage(strict_passed, total),

        "top1_category_matches": top1_category_matches,
        "top1_category_accuracy": percentage(top1_category_matches, total),

        "top1_keyword_matches": top1_keyword_matches,
        "top1_keyword_accuracy": percentage(top1_keyword_matches, total),

        "category_hits_at_5": category_hits_at_5,
        "category_hit_at_5_accuracy": percentage(category_hits_at_5, total),

        "keyword_hits_at_5": keyword_hits_at_5,
        "keyword_hit_at_5_accuracy": percentage(keyword_hits_at_5, total),

        "by_category": dict(by_category),
        "by_type": dict(by_type),
    }

    return summary


def print_group_scores(title, group_data):
    print(f"\n{title}")

    for name, data in sorted(group_data.items()):
        total = data["total"]
        soft = data["soft_passed"]
        strict = data["strict_passed"]
        top_cat = data["top1_category_matches"]
        top_kw = data["top1_keyword_matches"]

        print(
            f"- {name}: "
            f"Soft {soft}/{total} ({percentage(soft, total)}%) | "
            f"Strict {strict}/{total} ({percentage(strict, total)}%) | "
            f"Top1 Category {top_cat}/{total} ({percentage(top_cat, total)}%) | "
            f"Top1 Keyword {top_kw}/{total} ({percentage(top_kw, total)}%)"
        )


def print_summary(summary):
    print("\n" + "=" * 100)
    print("STRICT RETRIEVAL EVALUATION SUMMARY")
    print("=" * 100)

    print(f"Total Questions: {summary['total']}")

    print("\nOverall Scores:")
    print(f"Soft Accuracy: {summary['soft_passed']}/{summary['total']} ({summary['soft_accuracy']}%)")
    print(f"Strict Accuracy: {summary['strict_passed']}/{summary['total']} ({summary['strict_accuracy']}%)")
    print(f"Top1 Category Accuracy: {summary['top1_category_matches']}/{summary['total']} ({summary['top1_category_accuracy']}%)")
    print(f"Top1 Keyword Accuracy: {summary['top1_keyword_matches']}/{summary['total']} ({summary['top1_keyword_accuracy']}%)")
    print(f"Category Hit@5: {summary['category_hits_at_5']}/{summary['total']} ({summary['category_hit_at_5_accuracy']}%)")
    print(f"Keyword Hit@5: {summary['keyword_hits_at_5']}/{summary['total']} ({summary['keyword_hit_at_5_accuracy']}%)")

    print_group_scores("Category-wise Scores:", summary["by_category"])
    print_group_scores("Question-Type Scores:", summary["by_type"])


def save_report(results, summary):
    report = {
        "summary": summary,
        "results": results,
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print(f"\nStrict report saved to: {REPORT_FILE}")


def print_failed_strict_examples(results, limit=20):
    failed = [r for r in results if not r["strict_pass"]]

    print("\n" + "=" * 100)
    print(f"STRICT FAIL EXAMPLES | Showing first {min(limit, len(failed))} of {len(failed)}")
    print("=" * 100)

    for index, result in enumerate(failed[:limit], start=1):
        print(f"\nFail {index}")
        print("-" * 100)
        print(f"Question: {result['question']}")
        print(f"Expected Category: {result['expected_category']}")
        print(f"Top Category: {result['top_category']}")
        print(f"Top Source: {result['top_source']}")
        print(f"Expected Keywords: {result['expected_keywords']}")
        print(f"Matched Top1 Keywords: {result['matched_keywords_top1']}")
        print(f"Missed Top1 Keywords: {result['missed_keywords_top1']}")
        print("\nTop Chunk Preview:")
        print(result["top_chunk_preview"])


def main():
    if not os.path.exists(EVAL_FILE):
        print(f"Evaluation file not found: {EVAL_FILE}")
        print("Run this first: python generate_evaluation_questions.py")
        return

    with open(EVAL_FILE, "r", encoding="utf-8") as file:
        questions = json.load(file)

    print("\nIUB RAG Strict Retrieval Evaluation")
    print("=" * 100)
    print(f"Evaluation file: {EVAL_FILE}")
    print(f"Total questions loaded: {len(questions)}")

    results = []

    for item in questions:
        result = evaluate_question(item, k=5)
        results.append(result)

    summary = summarize(results)

    print_summary(summary)
    print_failed_strict_examples(results, limit=20)
    save_report(results, summary)


if __name__ == "__main__":
    main()