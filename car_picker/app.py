from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:  # pragma: no cover - optional dependency guard
    st_autorefresh = None

from core import engine, options
from core.indexer import DatasetIndex, load_index
from core.models import QuizMode, QuizQuestion, QuizState
from core.timer import expired as timer_expired, remaining_seconds

PAGE_TITLE = "Car Picker Quiz"
TOTAL_QUESTIONS = 10
TIME_LIMIT_SECONDS = 10 * 60  # 10 minutes

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / ".cache"
THUMB_DIR = BASE_DIR / ".thumbnails"

logging.basicConfig(level=logging.INFO)


@st.cache_resource(show_spinner=True)
def get_index() -> DatasetIndex:
    progress = st.progress(0.0)

    def _on_progress(current: int, total: int) -> None:
        progress.progress(min(current / max(total, 1), 1.0))

    try:
        return load_index(DATA_DIR, CACHE_DIR, THUMB_DIR, progress_callback=_on_progress)
    finally:
        progress.empty()


def render_sidebar(state: QuizState) -> QuizMode:
    st.sidebar.header("Quiz Settings")
    mode = st.sidebar.radio(
        "Quiz Mode",
        options=list(QuizMode),
        format_func=lambda m: m.display_name,
        index=list(QuizMode).index(state.mode) if state.mode in QuizMode else 0,
    )

    if st.sidebar.button("Restart Quiz"):
        engine.reset_quiz_state(state, mode=mode, duration_seconds=TIME_LIMIT_SECONDS)
        st.rerun()

    st.sidebar.markdown(
        """
        ### 규칙
        - 총 10문제, 제한시간 10분
        - 각 문제는 10개의 선택지가 제공됩니다.
        - 부분 점수: 제조사 / 모델 / 연식을 단계적으로 채점합니다.
        - 제한시간이 지나면 자동으로 종료됩니다.
        """
    )

    return mode


def render_timer_and_score(state: QuizState) -> None:
    remaining = remaining_seconds(state)
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    st.subheader(f"남은 시간: {minutes:02d}:{seconds:02d}")

    score_display = f"{state.score:.1f} / {len(state.history):.0f}"
    st.caption(f"현재 점수: {score_display}")


def render_feedback(state: QuizState) -> None:
    if not state.history:
        return

    last_result = state.history[-1]
    correct_label = options.format_label(last_result.question.car, last_result.score.mode)
    selected_label = last_result.selected_choice.label
    detail = last_result.score

    if detail.points >= detail.max_points:
        st.success(f"정답! +{detail.points:.1f}점")
    elif detail.points > 0:
        st.info(f"부분 정답! +{detail.points:.1f}점 (총 {detail.max_points:.1f}점 중)")
    else:
        st.error("오답입니다.")

    st.markdown(
        f"""
        **정답:** {correct_label}  
        **선택:** {selected_label}  
        **세부 채점:** 제조사 {'✅' if detail.make_correct else '❌'}, 모델 {'✅' if detail.model_correct else '❌'}, 연식 {'✅' if detail.year_correct else '❌'}
        """
    )


def render_question(state: QuizState, index: DatasetIndex, question: QuizQuestion) -> None:
    st.markdown(f"### 문제 {question.number} / {state.total_questions}")

    image_path = index.ensure_thumbnail(question.car)
    st.image(str(image_path), caption="어떤 차인지 맞춰보세요!", use_container_width=True)

    option_labels = {choice.id: choice.label for choice in question.choices}

    with st.form(key=f"question-{question.number}"):
        selected_id = st.radio(
            "정답을 선택하세요",
            options=list(option_labels.keys()),
            format_func=lambda key: option_labels[key],
            key=f"choice-{question.number}",
        )
        submitted = st.form_submit_button("정답 제출")

    if submitted and selected_id:
        engine.submit_answer(state, selected_id)
        st.rerun()


def render_final_results(state: QuizState) -> None:
    st.header("퀴즈 종료")

    total_points = state.score
    st.metric("최종 점수", f"{total_points:.1f} / {state.total_questions:.0f}")

    if not state.history:
        return

    rows = []
    for result in state.history:
        car = result.question.car
        rows.append(
            {
                "문제": result.question.number,
                "정답": options.format_label(car, result.score.mode),
                "선택": result.selected_choice.label,
                "점수": f"{result.score.points:.1f} / {result.score.max_points:.1f}",
                "제조사": "O" if result.score.make_correct else "X",
                "모델": "O" if result.score.model_correct else "X",
                "연식": "O" if result.score.year_correct else "X",
            }
        )

    st.table(rows)

    if st.button("다시 시작하기"):
        engine.reset_quiz_state(state, mode=state.mode, duration_seconds=TIME_LIMIT_SECONDS)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title("Car Picker 퀴즈")

    try:
        dataset = get_index()
    except Exception as exc:
        st.error(f"이미지 인덱스를 불러오는데 실패했습니다: {exc}")
        st.stop()

    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = engine.create_quiz_state(
            QuizMode.MAKE_MODEL_YEAR, total_questions=TOTAL_QUESTIONS, duration_seconds=TIME_LIMIT_SECONDS
        )

    state: QuizState = st.session_state.quiz_state
    mode = render_sidebar(state)

    if state.mode != mode or state.duration_seconds != TIME_LIMIT_SECONDS:
        engine.reset_quiz_state(state, mode=mode, duration_seconds=TIME_LIMIT_SECONDS)

    if not state.completed and st_autorefresh is not None:
        st_autorefresh(interval=1_000, key="timer-refresh")

    render_timer_and_score(state)
    render_feedback(state)

    if timer_expired(state):
        state.completed = True

    if state.completed:
        render_final_results(state)
        return

    question = engine.ensure_question(state, dataset)
    if question is None:
        render_final_results(state)
        return

    render_question(state, dataset, question)


if __name__ == "__main__":
    main()
