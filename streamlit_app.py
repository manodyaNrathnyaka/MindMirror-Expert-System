import streamlit as st
from kb.overthinking_rules import OverthinkingRules
from kb.stress_rules import StressRules
from kb.left_right_brain_rules import LeftRightBrainRules
from kb.question import OVERTHINKING_QUESTIONS, STRESS_QUESTIONS, LEFT_RIGHT_BRAIN_QUESTIONS
from facts import Answer

# Try to import LLM explainer; keep app usable if unavailable
try:
    from llm_explainer import generate_llm_explanation
    HAS_EXPLAINER = True
except Exception:
    HAS_EXPLAINER = False

# Simple mapping of tests
TESTS = {
    "Overthinking": ("overthinking", OVERTHINKING_QUESTIONS, OverthinkingRules),
    "Stress": ("stress", STRESS_QUESTIONS, StressRules),
    "Left/Right brain": ("left_right", LEFT_RIGHT_BRAIN_QUESTIONS, LeftRightBrainRules),
}

try:
    st.set_page_config(page_title="MIND MIRROR", page_icon="🪞", layout="wide")
except Exception:
    pass

st.title("MIND MIRROR")
try:
    st.sidebar.title("MIND MIRROR")
except Exception:
    pass

st.info("Please answer honestly — your results are only useful when you're truthful. This tool is for self-reflection, not diagnosis.")


# Minimal CSS to keep things readable
st.markdown(
    """
    <style>
      .question-card { background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding: 14px; border-radius: 10px; }
            .btn { border-radius: 8px }
            /* Answer pills */
            .answer-pill { display:inline-block; padding:8px 14px; border-radius:12px; margin-right:8px; border:1px solid rgba(255,255,255,0.06); color:#cfd8e3; background:transparent }
            .answer-pill.selected { background:#0b84ff; color:white; border-color:#0b84ff }
            /* Style navigation and action buttons to look consistent */
            .stButton>button {
                border-radius:8px !important; padding:8px 12px !important; background:#0f1720; color:#e6eef8; border:1px solid rgba(255,255,255,0.04);
            }
            .stButton>button:hover { transform:translateY(-1px); }
    </style>
    """,
    unsafe_allow_html=True,
)

selected = st.selectbox("Choose a test", list(TESTS.keys()))
test_key, questions, engine_cls = TESTS[selected]

# initialize session state for test
if "active_test" not in st.session_state or st.session_state.active_test != selected:
    st.session_state.active_test = selected
    st.session_state.questions = questions
    st.session_state.test_key = test_key
    st.session_state.engine_cls = engine_cls
    st.session_state.current_q = 0
    st.session_state.answers = [None] * len(questions)
    st.session_state.started = False
    st.session_state.initial_block = 10
    st.session_state.visible_count = min(st.session_state.initial_block, len(questions))

# Clean up old per-widget keys from previous runs that could conflict with
# current widgets. We only remove keys that look like per-question widget keys
# and keep core session keys intact. This runs before any widgets are created.
for _k in list(st.session_state.keys()):
    if _k.startswith("q_") or _k.startswith("btn_") or _k.startswith("prev_") or _k.startswith("next_"):
        if _k not in ("questions", "answers", "current_q", "active_test", "started", "visible_count", "initial_block", "test_key", "engine_cls"):
            try:
                del st.session_state[_k]
            except Exception:
                pass

# Navigation callbacks (use on_click to avoid relying on transient st.button return values)
def _go_prev():
    if st.session_state.get('current_q', 0) > 0:
        st.session_state.current_q = st.session_state.current_q - 1

def _go_next():
    idx = st.session_state.get('current_q', 0)
    # ensure answer exists for current index
    answers = st.session_state.get('answers', [])
    if idx < len(answers) and answers[idx] is not None:
        # only advance within visible range
        st.session_state.current_q = min(st.session_state.visible_count - 1, st.session_state.current_q + 1)
    else:
        st.session_state._need_answer_warning = True

if not st.session_state.started:
    if st.button("Start Test"):
        st.session_state.started = True

if st.session_state.started:
    total_q = len(st.session_state.questions)
    idx = st.session_state.current_q
    visible = st.session_state.visible_count

    st.write(f"### Question {idx+1} of {visible}")
    qtext = st.session_state.questions[idx]
    st.markdown(f"<div class='question-card'><strong>{idx+1}. {qtext}</strong></div>", unsafe_allow_html=True)

    # Use three side-by-side buttons to act like exclusive checkboxes.
    # Buttons update a single stored answer value so we never modify widget-backed
    # session_state keys after widget instantiation (avoids StreamlitAPIException).
    stored = st.session_state.answers[idx]
    # Use a horizontal radio (single-choice) to avoid session-state widget write issues.
    # Include a placeholder as the first option so questions can start unanswered.
    stored = st.session_state.answers[idx]
    options = ["", "Yes", "No", "Not sure"]
    try:
        start_index = options.index(stored.capitalize()) if stored else 0
    except Exception:
        start_index = 0

    selected = st.radio("Your answer", options, index=start_index, key=f"ans_{idx}", horizontal=True)
    if selected == "":
        st.session_state.answers[idx] = None
    else:
        st.session_state.answers[idx] = selected.lower()

    colp, coln, colr = st.columns([1,1,1])
    with colp:
        st.button("Previous", on_click=_go_prev, key="prev_btn")
    with coln:
        if st.session_state.current_q < visible - 1:
            st.button("Next", on_click=_go_next, key="next_btn")
            # show a warning if _go_next set the need-answer flag
            if st.session_state.pop('_need_answer_warning', None):
                st.warning("Please select an answer before moving to the next question.")
        else:
            submit_clicked = st.button("Submit answers", key="submit_answers")
            if submit_clicked:
                # gather answers for visible block
                answers = [a for a in st.session_state.answers[:st.session_state.visible_count]]
                not_sure_count = sum(1 for a in answers if str(a).strip().lower() == 'not sure')

                # if many not sure on first block, extend
                if st.session_state.visible_count == st.session_state.initial_block and not_sure_count >= 5 and total_q > st.session_state.initial_block:
                    extra = min(5, total_q - st.session_state.initial_block)
                    st.info(f"You answered {not_sure_count} 'Not sure' on the first {st.session_state.initial_block} questions. I'll ask {extra} more question(s).")
                    st.session_state.visible_count += extra
                    st.session_state.current_q = st.session_state.initial_block
                else:
                    # run engine
                    engine = st.session_state.engine_cls()
                    try:
                        engine.reset()
                    except Exception:
                        pass
                    for i, a in enumerate(answers, start=1):
                        try:
                            engine.declare(Answer(question=i, value=a))
                        except Exception:
                            pass
                    try:
                        engine.run()
                    except Exception:
                        pass

                    # prefer final_result or calculate()
                    result = getattr(engine, 'final_result', None)
                    if result is None and hasattr(engine, 'calculate'):
                        try:
                            result = engine.calculate()
                            engine.final_result = result
                        except Exception:
                            result = None

                    # Normalize to dict form
                    if isinstance(result, dict):
                        main_label = result.get('result', '')
                        alternative = result.get('alternative', '')
                        pct = result.get('percentage', None)
                    else:
                        main_label = str(result)
                        alternative = ''
                        pct = None

                    # ask LLM for explanation if available
                    explanation = None
                    if HAS_EXPLAINER:
                        try:
                            qa_pairs = [{"question": q, "answer": a} for q, a in zip(st.session_state.questions[:len(answers)], answers)]
                            explanation = generate_llm_explanation(st.session_state.test_key, qa_pairs, result)
                        except Exception:
                            explanation = None

                    # fallback deterministic explanation
                    if not explanation:
                        expl_lines = [f"Hello! The result suggests you are {main_label}."]
                        if alternative:
                            expl_lines.append(f"Note: {alternative}")
                        expl_lines.append("Some answers were 'not sure', which may have introduced ambiguity. Consider re-taking the test or answering more items clearly.")
                        expl_lines.append("Small steps: 1) Practice self-compassion; 2) Short mindfulness; 3) Talk with someone you trust if concerned.")
                        explanation = "\n\n".join(expl_lines)

                    # Display final view (only main, alternative, explanation)
                    st.markdown("### Result")
                    st.markdown(f"**You are a {main_label}**")
                    if alternative:
                        st.markdown(f"**Note:** {alternative}")

                    st.write(explanation)
    with colr:
        if st.button("Restart test"):
            st.session_state.current_q = 0
            st.session_state.answers = [None] * len(st.session_state.questions)

st.markdown(
    """
    <div style="margin-top:28px;padding:18px;border-radius:12px;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(90deg,#071726 0%,#08121a 100%);color:#e6eef8">
        <div style="font-weight:600">Thank you for using <span style="font-weight:800">MIND MIRROR</span></div>
        <div style="opacity:0.95">Reflect kindly. Answer honestly.</div>
    </div>
    """,
    unsafe_allow_html=True,
)