from __future__ import annotations

from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from budget_calculator import vnd
from schemas import ChatRequest, ChatResponse, ResetResponse
from travel_agent import run_budget_travel_agent


FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(title="BudgetTrip Planner API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SESSION_CONTEXT: dict[str, dict[str, Any]] = {}


def should_start_new_trip(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in ["tour mới", "chuyến mới", "làm lại", "xóa lịch sử", "reset", "new trip"])


def is_cafe_followup(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(keyword in lowered for keyword in ["cafe", "cà phê", "coffee", "quán cà", "quán cafe"])


def build_strong_contextual_prompt(prompt: str, context: dict[str, Any]) -> str:
    captured = context.get("captured_fields", {})
    city = context.get("city") or captured.get("city_or_area")
    budget = captured.get("budget_cap")
    people = captured.get("number_of_people")
    start = captured.get("starting_location")
    return (
        f"Mình có {budget} VND, đi {people} người, xuất phát từ {start}, "
        f"muốn đi {city}. Yêu cầu bổ sung: {prompt}"
    )


def build_cafe_followup_answer(prompt: str, context: dict[str, Any], session_id: str) -> ChatResponse:
    captured = context.get("captured_fields", {})
    city = context.get("city") or captured.get("city_or_area") or "khu vực này"
    cafe_items = [item for item in context.get("itinerary", []) if item.get("type") == "cafe"]
    if not cafe_items:
        message = (
            f"Trong lịch trình hiện tại mình chưa có quán cafe cụ thể ở {city}. "
            "Bạn có thể hỏi rõ hơn theo khu vực, ví dụ: cafe gần trung tâm hoặc cafe gần điểm số 4."
        )
    else:
        lines = ["Có. Trong lịch trình hiện tại, lựa chọn cafe phù hợp nhất là:"]
        for item in cafe_items[:3]:
            lines.append(
                f"- {item.get('name')} ở khu vực {item.get('area', city)}, "
                f"khung giờ {item.get('recommended_time_slot', 'linh hoạt')}, "
                f"ước tính {vnd(item.get('average_cost_per_person'))}/người."
            )
        lines.append("Mình có thể đổi lịch trình để ưu tiên cafe view đẹp, gần trung tâm, hoặc rẻ hơn.")
        message = "\n".join(lines)

    return ChatResponse(
        session_id=session_id,
        response_type="text_answer",
        message=message,
        captured_fields=captured,
        city=city,
        tool_trace=["use_session_context", "answer_cafe_followup"],
        response_language=context.get("response_language"),
    )


def normalize_agent_response(result: dict[str, Any], session_id: str) -> ChatResponse:
    message = result.get("message") or result.get("follow_up_question") or result.get("budget_message")
    return ChatResponse(
        session_id=session_id,
        response_type=result.get("response_type", "unknown"),
        message=message,
        captured_fields=result.get("captured_fields", {}),
        missing_fields=result.get("missing_fields", []),
        follow_up_question=result.get("follow_up_question"),
        city=result.get("city"),
        itinerary=result.get("itinerary", []),
        cost_summary=result.get("cost_summary", {}),
        budget_message=result.get("budget_message"),
        saving_suggestions=result.get("saving_suggestions", []),
        transport_info=result.get("transport_info", {}),
        enrichment=result.get("enrichment", {}),
        tool_trace=result.get("tool_trace", []),
        log=result.get("log", {}),
        response_language=result.get("response_language"),
        data_source=result.get("data_source"),
        data_confidence=result.get("data_confidence"),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    message = request.message.strip()

    if should_start_new_trip(message):
        SESSION_CONTEXT.pop(session_id, None)

    context = SESSION_CONTEXT.get(session_id)
    if context and is_cafe_followup(message) and not should_start_new_trip(message):
        return build_cafe_followup_answer(message, context, session_id)

    result = run_budget_travel_agent(message)
    if result.get("response_type") == "missing_required_input" and context:
        result = run_budget_travel_agent(build_strong_contextual_prompt(message, context))

    if result.get("response_type") not in {"missing_required_input", "out_of_scope", "unsupported_destination"}:
        SESSION_CONTEXT[session_id] = result

    return normalize_agent_response(result, session_id)


@app.post("/api/sessions/{session_id}/reset", response_model=ResetResponse)
def reset_session(session_id: str) -> ResetResponse:
    SESSION_CONTEXT.pop(session_id, None)
    return ResetResponse(session_id=session_id, status="reset")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
