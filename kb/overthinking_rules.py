from experta import KnowledgeEngine, Rule, DefFacts, Fact
from facts import Answer

class OverthinkingRules(KnowledgeEngine):


    @DefFacts()
    def _initial_action(self):
        yield Fact(action="overthinking_test")

    @Rule(Fact(action="overthinking_test"),
          Answer(value="yes"))
    def count_yes(self):
        # kept for compatibility if rules are used in a different way; actual
        # calculation will recompute counts from facts to remain deterministic
        # across runs.
        try:
            self.yes_count += 1
        except Exception:
            self.yes_count = 1

    def calculate(self):
        # Recompute yes_count and total from declared facts so the percentage
        # reflects exactly the number of answered questions in the UI.
        yes_count = 0
        total = 0

        for _id, fact in self.facts.items():
            try:
                if isinstance(fact, Answer):
                    val = getattr(fact, 'value', None)
                elif hasattr(fact, 'get'):
                    # dict-like Fact
                    val = fact.get('value') if callable(getattr(fact, 'get', None)) else None
                else:
                    val = None

                if val is not None:
                    total += 1
                    if str(val).strip().lower() == 'yes' or str(val).strip().lower() == 'y':
                        yes_count += 1
            except Exception:
                continue

        percentage = (yes_count / total) * 100 if total > 0 else 0.0

        if percentage >= 60:
            result = "High Overthinking"
            alternative = "40% still suggests you may NOT be an overthinker in all situations."
        elif percentage >= 35:
            result = "Moderate Overthinking"
            alternative = "You show patterns of overthinking only in certain conditions."
        else:
            result = "Low Overthinking / Not an Overthinker"
            alternative = "But some patterns can happen due to occasional stress or fatigue."

        out = {
            "score": yes_count,
            "percentage": percentage,
            "result": result,
            "alternative": alternative
        }

        try:
            self.final_result = out
        except Exception:
            pass

        return out


