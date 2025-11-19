from kb.overthinking_rules import OverthinkingRules
from kb.stress_rules import StressRules
from kb.left_right_brain_rules import LeftRightBrainRules
from facts import Answer
from llm_explainer import generate_llm_explanation
from kb.question import OVERTHINKING_QUESTIONS, STRESS_QUESTIONS, LEFT_RIGHT_BRAIN_QUESTIONS


print("\nSelect a test:")
print("1. Overthinking Test")
print("2. Stress Test")
print("3. Left-Right Brain Test")

choice = input("Enter number: ").strip()

# map numeric choice to canonical test key and question list
choice_map = {
    "1": ("overthinking", OVERTHINKING_QUESTIONS, OverthinkingRules),
    "2": ("stress", STRESS_QUESTIONS, StressRules),
    "3": ("left-right", LEFT_RIGHT_BRAIN_QUESTIONS, LeftRightBrainRules),
}

if choice not in choice_map:
    print("Invalid choice. Exiting.")
    raise SystemExit(1)

test_key, question_list, engine_cls = choice_map[choice]


def prompt_menu(prompt: str, options: dict) -> str:
    """Show a numbered menu and return the selected value (not the number).

    options: mapping of string-number -> returned-value (e.g. {"1":"yes"})
    """
    while True:
        # show prompt with options on separate lines
        print(prompt)
        for num, val in options.items():
            print(f"  {num}. {val}")

        sel = input("Choose (number): ")

        # accept numeric selection
        if sel in options:
            return options[sel]

        # # accept full-word selection (yes/no/not sure)
        # for val in options.values():
        #     if sel == val.lower():
        #         return val

        # # accept shortcut letters: y / n / s
        # shortcuts = {v[0].lower(): v for v in options.values()}
        # if sel in shortcuts:
        #     return shortcuts[sel]

        print("Invalid choice — please try again.\n")


answer_options = {"1": "yes", "2": "no", "3": "not sure"}

# Ask initial block of questions (first 10), then optionally ask 5 more if many "not sure"
answers = []
not_sure_count = 0
initial_block = 10
total_qs = len(question_list)

# Ask first block (up to total questions)
first_block = min(initial_block, total_qs)
for i, q in enumerate(question_list[:first_block], start=1):
    ans = prompt_menu(f"Q{i}: {q}", answer_options)
    answers.append(ans)
    if ans == "not sure":
        not_sure_count += 1

# Build a list of question/answer pairs for explanations (used by the LLM explainer)
qa_pairs = [
    {"question": q, "answer": a}
    for q, a in zip(question_list[:first_block], answers)
]

# If user was unsure often, ask an extra 5 questions (if available)
if not_sure_count >= 5 and total_qs > first_block:
    extra = min(5, total_qs - first_block)
    print("\nYou seemed unsure on several items. Asking a few more questions to clarify...\n")
    for j, q in enumerate(question_list[first_block:first_block + extra], start=first_block + 1):
        ans = prompt_menu(f"Q{j}: {q}", answer_options)
        answers.append(ans)
        qa_pairs.append({"question": q, "answer": ans})


# Run the selected knowledge-engine directly
engine = engine_cls()
engine.reset()
for i, a in enumerate(answers, start=1):
    engine.declare(Answer(question=i, value=a))

engine.run()

# Prefer a final_result attribute if the KB set it. If not present,
# some KBs provide a calculate() helper we can call to obtain the same
# information — use that as a fallback so callers (and the CLI) get a value.
result = getattr(engine, "final_result", None)
if result is None and hasattr(engine, 'calculate'):
    try:
        result = engine.calculate()
        # ensure attribute is present for other callers
        try:
            engine.final_result = result
        except Exception:
            pass
    except Exception:
        result = None

# Safe explainer wrapper: try the LLM-based explainer, fall back to a simple local summary
def explain(result_data):
    """Return an explanation string for the given result_data.

    Tries to call the LLM explainer (generate_llm_explanation). If that fails
    (missing API key, network error, etc.), return a concise local explanation.
    """
    try:
        # generate_llm_explanation expects (test_name, qa_pairs, result_data)
        return generate_llm_explanation(test_key, qa_pairs, result_data)
    except Exception as e:
        # graceful fallback — include the exception message so the user can see why
        yes_count = sum(1 for a in answers if a == "yes")
        total = len(answers)
        percentage = None
        alternative = ""
        if isinstance(result_data, dict):
            percentage = result_data.get("percentage")
            alternative = result_data.get("alternative", "")

        parts = [f"Result: {result_data.get('result') if isinstance(result_data, dict) else result_data}",
                 f"Yes count: {yes_count}/{total}"]
        if percentage is not None:
            parts.append(f"Estimated probability: {percentage}")
        if alternative:
            parts.append(f"Alternative: {alternative}")

        # Append a note including the caught exception for easier debugging
        parts.append(f"\n(Note: LLM explanation unavailable — showing fallback summary. LLM error: {type(e).__name__}: {e})")
        return "\n".join(parts)

print("\nResult:", result)

if result:
    print("\nExplanation:")
    print(explain(result))
else:
    print("\nNo clear conclusion was reached by the rules engine.")

# Also print a simple answer-distribution summary (yes/no/not sure) and
# interpret them as suggested by the user: main probability = yes% and
# alternative percentages coming from no% and not_sure%.
def answer_distribution(answers_list):
    total = len(answers_list)
    counts = {"yes": 0, "no": 0, "not sure": 0}
    for a in answers_list:
        key = str(a).strip().lower()
        if key in counts:
            counts[key] += 1
        elif key == 'y':
            counts['yes'] += 1
        elif key == 'n':
            counts['no'] += 1
        else:
            # unexpected answers count as 'not sure'
            counts['not sure'] += 1

    pct = {k: (v / total * 100 if total > 0 else 0.0) for k, v in counts.items()}
    return counts, pct

counts, pct = answer_distribution(answers)
print("\nAnswer distribution:")
print(f"  Yes: {counts['yes']} ({pct['yes']:.1f}%)")
print(f"  No: {counts['no']} ({pct['no']:.1f}%)")
print(f"  Not sure: {counts['not sure']} ({pct['not sure']:.1f}%)")

# Friendly interpretation lines
print("\nInterpretation:")
print(f"  Main probability (based on 'Yes'): {pct['yes']:.1f}% chance of being labeled '{result.get('result') if isinstance(result, dict) else result}'")
print(f"  Alternative (based on 'No'): {pct['no']:.1f}% — may indicate not matching the condition")
print(f"  Uncertain (based on 'Not sure'): {pct['not sure']:.1f}% — suggests ambiguity; consider re-taking the test or answering more items clearly.")
