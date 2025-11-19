from experta import KnowledgeEngine, Rule, DefFacts, Fact
from facts import Answer

class StressRules(KnowledgeEngine):
   

    @DefFacts()
    def _initial_action(self):
        yield Fact(action="stress_test")

    @Rule(Fact(action="stress_test"),
          Answer(value="yes"))
    def count_yes(self):
        try:
            self.yes_count += 1
        except Exception:
            self.yes_count = 1

    def calculate(self):
        # Recompute yes_count and total from declared facts
        yes_count = 0
        total = 0

        for _id, fact in self.facts.items():
            try:
                if isinstance(fact, Answer):
                    val = getattr(fact, 'value', None)
                elif hasattr(fact, 'get'):
                    val = fact.get('value') if callable(getattr(fact, 'get', None)) else None
                else:
                    val = None

                if val is not None:
                    total += 1
                    if str(val).strip().lower() in ('yes', 'y'):
                        yes_count += 1
            except Exception:
                continue

        percentage = (yes_count / total) * 100 if total > 0 else 0.0

        if percentage >= 60:
            result = "High Stress"
            alternative = "There is still a chance stress is situational rather than chronic."
        elif percentage >= 35:
            result = "Moderate Stress"
            alternative = "You may benefit from short daily recovery habits."
        else:
            result = "Low Stress"
            alternative = "Stress levels look low based on your answers."

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

