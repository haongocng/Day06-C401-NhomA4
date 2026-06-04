from __future__ import annotations

import pandas as pd
import streamlit as st

from budget_calculator import vnd
from data_loader import list_supported_cities
from travel_agent import run_budget_travel_agent


MAX_USER_TURNS = 5


st.set_page_config(
    page_title="BudgetTrip Planner",
    layout="wide",
)


def format_cost_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for column in ["Chi phí/người", "Tổng chi phí"]:
        df[column] = df[column].apply(lambda value: "" if pd.isna(value) else vnd(value))
    return df


PLACE_TYPE_LABELS = {
    "tham_quan": "Tham quan",
    "an_sang": "Ăn sáng",
    "an_trua": "Ăn trưa",
    "an_toi": "Ăn tối",
    "cafe": "Cafe",
    "food": "Ăn uống",
    "restaurant": "Nhà hàng",
}


MODE_LABELS = {
    "inspire_mode": "Gợi ý điểm đến",
    "itinerary_result": "Theo yêu cầu",
}


STATUS_LABELS = {
    "WITHIN_BUDGET": "Trong ngân sách",
    "NEAR_LIMIT": "Gần chạm ngân sách",
    "OVER_BUDGET": "Vượt ngân sách",
}


def format_place_type(place_type: str | None) -> str:
    return PLACE_TYPE_LABELS.get(place_type or "", (place_type or "tham_quan").replace("_", " ").title())


def should_start_new_trip(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in ["tour mới", "chuyến mới", "làm lại", "xóa lịch sử", "reset"])


def build_contextual_prompt(prompt: str) -> str:
    context = st.session_state.get("trip_context")
    if not context or should_start_new_trip(prompt):
        return prompt

    captured = context.get("captured_fields", {})
    city = context.get("city") or captured.get("city_or_area")
    budget = captured.get("budget_cap")
    people = captured.get("number_of_people")
    start = captured.get("starting_location")

    context_lines = [
        "Bối cảnh chuyến đi trước đó, chỉ dùng để hiểu câu hỏi nối tiếp:",
        f"- Ngân sách: {budget} VND" if budget else "",
        f"- Số người: {people}" if people else "",
        f"- Khu vực: {city}" if city else "",
        f"- Điểm xuất phát: {start}" if start else "",
        "Yêu cầu mới của user:",
        prompt,
    ]
    return "\n".join(line for line in context_lines if line)


def render_missing_input(result: dict) -> None:
    st.warning(result.get("follow_up_question", "Mình cần thêm thông tin trước khi tạo tour."))
    with st.expander("Thông tin đã hiểu"):
        st.json(result.get("captured_fields", {}))


def render_itinerary_result(result: dict) -> None:
    captured = result.get("captured_fields", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ngân sách", vnd(captured.get("budget_cap")))
    col2.metric("Số người", captured.get("number_of_people"))
    col3.metric("Khu vực", result.get("city") or captured.get("city_or_area"))
    col4.metric("Chế độ", MODE_LABELS.get(result["response_type"], "Theo yêu cầu"))

    if result.get("unmatched_places"):
        st.info("Một số địa điểm bạn nhập chưa có trong dữ liệu: " + ", ".join(result["unmatched_places"]))

    st.subheader("Lịch trình đề xuất")
    for index, item in enumerate(result.get("itinerary", []), start=1):
        required_badge = " · điểm bắt buộc" if item.get("required") else ""
        st.markdown(
            f"**{index}. {item.get('recommended_time_slot', 'Linh hoạt')} - {item.get('name')}**{required_badge}"
        )
        st.write(
            f"Khu vực: {item.get('area', 'Chưa rõ')} · "
            f"Loại: {format_place_type(item.get('type'))} · "
            f"Chi phí/người: {vnd(item.get('average_cost_per_person'))}"
        )

    st.subheader("Chi phí")
    cost_summary = result.get("cost_summary", {})
    st.dataframe(format_cost_dataframe(cost_summary.get("cost_rows", [])), use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ăn uống", vnd(cost_summary.get("food_cost")))
    col2.metric("Cafe", vnd(cost_summary.get("cafe_cost")))
    col3.metric("Đi chơi", vnd(cost_summary.get("activity_cost")))
    col4.metric("Di chuyển", vnd(cost_summary.get("transport_cost")))

    st.metric("Tổng tiền dự kiến", vnd(cost_summary.get("total_cost")))

    status = cost_summary.get("status")
    st.caption(f"Trạng thái: {STATUS_LABELS.get(status, 'Chưa rõ')}")
    if status == "OVER_BUDGET":
        st.error(result.get("budget_message"))
    elif status == "NEAR_LIMIT":
        st.warning(result.get("budget_message"))
        st.info("Bạn có thể dùng phần ngân sách còn lại để thêm một điểm cafe/view đẹp, đổi bữa ăn tốt hơn, hoặc giảm các điểm xa nhau để chuyến đi đỡ mệt.")
    else:
        st.success(result.get("budget_message"))
        st.info("Bạn có muốn cải thiện lịch trình để trải nghiệm tốt hơn không? Ví dụ: thêm điểm check-in, đổi bữa ăn chất lượng hơn, hoặc tối ưu thứ tự di chuyển.")

    transport = result.get("transport_info", {})
    with st.expander("Phương tiện đề xuất"):
        st.write(f"**{transport.get('transport_mode')}**")
        st.write(transport.get("best_for", ""))
        if transport.get("saving_tip"):
            st.info(transport["saving_tip"])

    st.subheader("Gợi ý tiết kiệm")
    suggestions = result.get("saving_suggestions") or []
    if suggestions:
        for suggestion in suggestions:
            saving = suggestion.get("estimated_saving")
            suffix = f" - tiết kiệm khoảng {vnd(saving)}" if saving else ""
            st.markdown(f"**{suggestion.get('title')}**{suffix}")
            st.write(suggestion.get("detail"))
    else:
        st.write("Lịch trình hiện chưa vượt ngân sách. Bạn vẫn có thể giảm thêm bằng cách ưu tiên đi bộ hoặc chọn các điểm miễn phí gần nhau.")

    if result.get("minimum_budget_to_keep_required_places"):
        st.info(
            "Ngân sách tối thiểu để giữ các điểm bắt buộc khoảng "
            + vnd(result["minimum_budget_to_keep_required_places"])
            + "."
        )

    with st.expander("Debug agent"):
        st.write(" -> ".join(result.get("tool_trace", [])))
        st.json(
            {
                "captured_fields": result.get("captured_fields", {}),
                "data_source": result.get("data_source"),
                "data_confidence": result.get("data_confidence"),
                "confidence_note": result.get("confidence_note"),
                "source_urls": result.get("source_urls", []),
            }
        )


def render_assistant_message(result: dict) -> None:
    if result.get("response_type") == "missing_required_input":
        render_missing_input(result)
    else:
        render_itinerary_result(result)


def handle_prompt(prompt: str) -> None:
    if should_start_new_trip(prompt):
        st.session_state.messages = []
        st.session_state.user_turns = 0
        st.session_state.trip_context = None

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.user_turns += 1

    with st.spinner("Agent đang xử lý yêu cầu..."):
        result = run_budget_travel_agent(build_contextual_prompt(prompt))

    st.session_state.messages.append({"role": "assistant", "result": result})
    if result.get("response_type") != "missing_required_input":
        st.session_state.trip_context = result


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Bạn cho mình ngân sách, số người, khu vực muốn đi và điểm xuất phát nhé. "
                "Nếu chưa biết đi đâu, mình sẽ bật chế độ gợi ý điểm đến."
            ),
        }
    ]
if "user_turns" not in st.session_state:
    st.session_state.user_turns = 0
if "trip_context" not in st.session_state:
    st.session_state.trip_context = None


st.title("BudgetTrip Planner")
st.caption("Chat lập tour 1 ngày theo ngân sách. Bạn có thể hỏi nối tiếp tối đa 5 lượt trong một phiên.")

with st.sidebar:
    st.subheader("Thành phố trong dữ liệu mẫu")
    st.write(", ".join(list_supported_cities()))

    if st.button("Bắt đầu chuyến mới", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Mình đã làm mới cuộc trò chuyện. Bạn muốn lên tour ở đâu?",
            }
        ]
        st.session_state.user_turns = 0
        st.session_state.trip_context = None
        st.rerun()

    with st.expander("Luồng xử lý nội bộ"):
        st.code(
            "\n".join(
                [
                    "parse_user_request",
                    "validate_required_inputs",
                    "search_mock_places / web fallback",
                    "estimate_transport_cost",
                    "build_itinerary",
                    "calculate_trip_cost",
                    "check_budget_status",
                    "generate_saving_suggestions",
                ]
            ),
            language="text",
        )


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "result" in message:
            render_assistant_message(message["result"])
        else:
            st.write(message.get("content", ""))


limit_reached = st.session_state.user_turns >= MAX_USER_TURNS
if limit_reached:
    st.info("Bạn đã dùng hết 5 lượt hỏi trong phiên demo. Hãy nạp lại trang hoặc bấm 'Bắt đầu chuyến mới' để trải nghiệm thêm.")

prompt = st.chat_input(
    "Nhập yêu cầu hoặc hỏi tiếp về lịch trình...",
    disabled=limit_reached,
)

if prompt:
    handle_prompt(prompt)
    st.rerun()
