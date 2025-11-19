from experta import KnowledgeEngine, Rule, DefFacts, Fact
from facts import Answer

class LeftRightBrainRules(KnowledgeEngine):
  

    @DefFacts()
    def _initial_action(self):
        yield Fact(action="lr_test")

    def calculate(self):
        # Recompute counts from the declared facts to avoid relying on
        # rule-side counters (keeps behavior deterministic).
        yes_count = 0
        total = 0

        for _id, fact in self.facts.items():
            # facts stored in the engine can be instances of Answer
            # or raw Fact objects. We only care about Answer facts.
            try:
                # experta's Fact behaves like a dict-like object
                if isinstance(fact, Answer) or (hasattr(fact, 'get') and fact.get('__class__', None) is None and 'question' in fact):
                    # Some environments store user facts as Answer(...) instances
                    val = None
                    if isinstance(fact, Answer):
                        val = getattr(fact, 'value', None)
                    else:
                        # fallback for dict-like facts
                        val = fact.get('value') if hasattr(fact, 'get') else None

                    if val is not None:
                        total += 1
                        if str(val).strip().lower() == 'yes' or str(val).strip().lower() == 'y':
                            yes_count += 1
            except Exception:
                # ignore facts we can't interpret as Answer
                continue

        percentage = int((yes_count / total) * 100) if total > 0 else 0

        if percentage > 60:
            result = "Left Brain Dominant"
            alternative = "You show a tendency toward left-brain thinking (analytical, logical)."
        elif percentage < 40:
            result = "Right Brain Dominant"
            alternative = "You show a tendency toward right-brain thinking (creative, intuitive)."
        else:
            result = "Balanced Thinker"
            alternative = "You have a balanced thinking style between left and right brain."

        out = {
            "yes_count": yes_count,
            "total": total,
            "percentage": percentage,
            "result": result,
            "alternative": alternative,
        }

        # expose a final_result attribute so callers that expect
        # engine.final_result (used by main.py / inference wrapper) get a value
        try:
            self.final_result = out
        except Exception:
            pass

        return out
