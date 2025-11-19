from kb.overthinking_rules import OverthinkingRules
from kb.stress_rules import StressRules
from kb.left_right_brain_rules import LeftRightBrainRules
from facts import Answer
from kb.question import OVERTHINKING_QUESTIONS, STRESS_QUESTIONS, LEFT_RIGHT_BRAIN_QUESTIONS
from llm_explainer import generate_llm_explanation



class ExpertSystemEngine:
    def __init__(self, test_name):
        self.test_name = test_name
        self.answers = []
        self.not_sure_count = 0
        self.current_question_index = 0

        if test_name == "overthinking":
            self.engine = OverthinkingRules()
            self.questions = OVERTHINKING_QUESTIONS

        elif test_name == "stress":
            self.engine = StressRules()
            self.questions = STRESS_QUESTIONS

        elif test_name == "left-right":
            self.engine = LeftRightBrainRules()
            self.questions = LEFT_RIGHT_BRAIN_QUESTIONS

        self.first_batch_limit = 10  # ask first 10
        # prepare engine for facts
        try:
            # experta engines require reset before declaring facts
            self.engine.reset()
        except Exception:
            pass

    def get_next_question(self):
        # stop if we've exhausted the question list
        if self.current_question_index >= len(self.questions):
            return None

        # always ask the first batch
        if self.current_question_index < self.first_batch_limit:
            return self.questions[self.current_question_index]

        # after the first batch, only continue if user had many 'not sure' answers
        if self.not_sure_count >= (self.first_batch_limit // 2):
            return self.questions[self.current_question_index]

        return None

    def add_answer(self, answer):
        self.answers.append(answer)

        if answer == "not sure":
            self.not_sure_count += 1

        # declare the fact (use 1-based question numbering to match KB rules)
        qnum = self.current_question_index + 1
        try:
            self.engine.declare(Answer(question=qnum, value=answer))
        except Exception:
            # if engine doesn't support declare here, ignore and continue
            pass

        self.current_question_index += 1

        # nothing to return; caller can query state
        return None

    def compute_result(self):
        # run the rules engine and collect result
        try:
            self.engine.run()
        except Exception:
            pass

        # many KB classes set `final_result` — use that if available
        final = getattr(self.engine, "final_result", None)
        result_data = {"result": final}

        qa_pairs = [
            {"question": self.questions[i], "answer": self.answers[i]}
            for i in range(len(self.answers))
        ]

        # ask the LLM for a human-friendly explanation (if configured)
        try:
            explanation = generate_llm_explanation(self.test_name, qa_pairs, result_data)
        except Exception:
            explanation = None

        return {
            "engine_result": result_data,
            "qa_pairs": qa_pairs,
            "llm_explanation": explanation
        }
