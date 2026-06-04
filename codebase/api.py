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

from budget_calculator import calculate_trip_cost, check_budget_status, vnd
from data_loader import find_city_data, load_all_city_data, normalize_text, search_places
from external_city_data import fetch_external_cafe_recommendations, fetch_external_city_data
from schemas import ChatRequest, ChatResponse, ResetResponse
from travel_agent import detect_response_language, load_agent_config, parse_user_request, run_budget_travel_agent


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
    normalized = normalize_text(prompt)
    if any(keyword in lowered for keyword in ["cafe", "coffee", "coffee shop"]):
        return True
    if any(keyword in normalized for keyword in ["cafe", "ca phe", "quan ca", "quan cafe"]):
        return True
    return any(keyword in lowered for keyword in ["cà phê", "quán cà", "quán cafe"])


def is_improvement_followup(prompt: str) -> bool:
    normalized = normalize_text(prompt)
    keywords = [
        "cai thien",
        "nang cap",
        "tot hon",
        "them trai nghiem",
        "them diem",
        "them hoat dong",
        "view dep",
        "chat luong hon",
        "improve",
        "upgrade",
        "better experience",
    ]
    return any(keyword in normalized for keyword in keywords)


def is_same_city(left: str | None, right: str | None) -> bool:
    left_key = normalize_text(left)
    right_key = normalize_text(right)
    return bool(left_key and right_key and (left_key == right_key or left_key in right_key or right_key in left_key))


def filter_cafes(places: list[dict[str, Any]], strict: bool = False) -> list[dict[str, Any]]:
    cafes: list[dict[str, Any]] = []
    for place in places:
        name = str(place.get("name", ""))
        searchable = normalize_text(
            " ".join(
                [
                    name,
                    str(place.get("type", "")),
                    str(place.get("area", "")),
                    " ".join(str(tag) for tag in place.get("tags", [])),
                ]
            )
        )
        name_key = normalize_text(name)
        bad_terms = [
            "gia ve",
            "bang gia",
            "du lich",
            "tour",
            "khach san",
            "combo",
            "instagram",
            "facebook",
            "youtube",
            "tuyen dung",
            "viec lam",
            "kinh nghiem",
            "cam nang",
        ]
        if any(term in name_key for term in bad_terms):
            continue
        has_cafe_signal = any(keyword in searchable for keyword in ["cafe", "ca phe", "coffee"])
        if has_cafe_signal or (not strict and place.get("type") == "cafe"):
            cafes.append(place)
    return cafes


def resolve_city_for_followup(prompt: str, context: dict[str, Any]) -> str | None:
    parsed = parse_user_request(prompt, load_agent_config())
    if parsed.get("city_or_area"):
        return parsed["city_or_area"]
    captured = context.get("captured_fields", {})
    return context.get("city") or captured.get("city_or_area")


def find_cafe_recommendations(city_or_area: str, context: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    all_city_data = load_all_city_data()
    city_data = find_city_data(city_or_area, all_city_data)
    source = "mock_data"
    if not city_data:
        city_data = fetch_external_city_data(city_or_area)
        source = "web_cache" if city_data else "none"

    cafes: list[dict[str, Any]] = []
    if city_data:
        place_result = search_places(city_data, preferences=["cafe", "check-in"], limit=10)
        cafes = filter_cafes(place_result.get("matched_places", []) + place_result.get("suggested_places", []), strict=source == "web_cache")

    if not cafes and source == "mock_data":
        external_city_data = fetch_external_city_data(city_or_area)
        if external_city_data:
            place_result = search_places(external_city_data, preferences=["cafe", "check-in"], limit=10)
            cafes = filter_cafes(
                place_result.get("matched_places", []) + place_result.get("suggested_places", []),
                strict=True,
            )
            source = "web_cache" if cafes else source
        if not cafes:
            cafes = fetch_external_cafe_recommendations(city_or_area)
            source = "web_search" if cafes else source
    elif not cafes and source == "web_cache":
        cafes = fetch_external_cafe_recommendations(city_or_area)
        source = "web_search" if cafes else source

    context_city = context.get("city") or context.get("captured_fields", {}).get("city_or_area")
    if not cafes and is_same_city(city_or_area, context_city):
        cafes = [item for item in context.get("itinerary", []) if item.get("type") == "cafe"]
        source = "current_itinerary" if cafes else source
    return cafes[:4], source


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


def has_pending_required_fields(context: dict[str, Any] | None) -> bool:
    if not context:
        return False
    return context.get("response_type") == "missing_required_input" or bool(context.get("missing_fields"))


def build_merged_contextual_prompt(prompt: str, context: dict[str, Any]) -> str:
    captured = dict(context.get("captured_fields", {}))
    parsed_followup = parse_user_request(prompt, load_agent_config())

    for field in [
        "budget_cap",
        "number_of_people",
        "number_of_days",
        "city_or_area",
        "starting_location",
        "transport_preference",
        "travel_date",
    ]:
        value = parsed_followup.get(field)
        if field == "number_of_days" and int(value or 1) <= 1 and int(captured.get("number_of_days") or 1) > 1:
            continue
        if value not in [None, "", []]:
            captured[field] = value

    for field in ["desired_places", "travel_preferences", "meal_preferences"]:
        current = captured.get(field) or []
        new_values = parsed_followup.get(field) or []
        merged: list[Any] = []
        for value in [*current, *new_values]:
            if value and value not in merged:
                merged.append(value)
        captured[field] = merged

    parts = []
    if captured.get("budget_cap"):
        parts.append(f"Mình có {captured['budget_cap']} VND")
    if captured.get("number_of_people"):
        parts.append(f"đi {captured['number_of_people']} người")
    if captured.get("starting_location"):
        parts.append(f"xuất phát từ {captured['starting_location']}")
    if captured.get("city_or_area"):
        parts.append(f"muốn đi {captured['city_or_area']}")
    if captured.get("number_of_days"):
        parts.append(f"trong {captured['number_of_days']} ngày")
    if captured.get("travel_preferences"):
        parts.append("ưu tiên " + ", ".join(str(item) for item in captured["travel_preferences"]))
    parts.append(f"Yêu cầu bổ sung: {prompt}")
    return ", ".join(parts)


def build_cafe_followup_answer(prompt: str, context: dict[str, Any], session_id: str) -> ChatResponse:
    captured = context.get("captured_fields", {})
    language = detect_response_language(prompt)
    city = resolve_city_for_followup(prompt, context) or context.get("city") or captured.get("city_or_area") or "khu vực này"
    cafe_items, source = find_cafe_recommendations(city, context)
    if not cafe_items:
        if language == "en":
            message = (
                f"I do not have reliable cafe data for {city} yet. "
                "You can ask for a narrower area, for example: cafes near the center, near the beach, or near a specific itinerary stop."
            )
        else:
            message = (
                f"Mình chưa có dữ liệu cafe đủ tin cậy cho {city}. "
                "Bạn có thể hỏi theo khu vực cụ thể hơn, ví dụ: cafe gần trung tâm, gần biển, hoặc gần điểm tham quan số 4."
            )
    else:
        if language == "en":
            lines = [f"Yes. A few cafe suggestions for {city}:"]
            for item in cafe_items[:3]:
                lines.append(
                    f"- {item.get('name')} in {item.get('area', city)}, "
                    f"time: {item.get('recommended_time_slot', 'flexible')}, "
                    f"estimated {vnd(item.get('average_cost_per_person'))}/person."
                )
            if source in {"web_cache", "web_search"}:
                lines.append("These suggestions come from web sources, so please re-check opening hours and prices before going.")
            lines.append("I can also adjust the itinerary to prioritize better views, central locations, or lower prices.")
        else:
            lines = [f"Có. Một vài gợi ý cafe phù hợp ở {city} là:"]
            for item in cafe_items[:3]:
                lines.append(
                    f"- {item.get('name')} ở khu vực {item.get('area', city)}, "
                    f"khung giờ {item.get('recommended_time_slot', 'linh hoạt')}, "
                    f"ước tính {vnd(item.get('average_cost_per_person'))}/người."
                )
            if source in {"web_cache", "web_search"}:
                lines.append("Các gợi ý này lấy từ nguồn web nên bạn nên kiểm tra lại giờ mở cửa và giá trước khi đi.")
            lines.append("Mình có thể đổi lịch trình để ưu tiên cafe view đẹp, gần trung tâm, hoặc rẻ hơn.")
        message = "\n".join(lines)

    return ChatResponse(
        session_id=session_id,
        response_type="text_answer",
        message=message,
        captured_fields=captured,
        city=city,
        tool_trace=["use_session_context", "search_cafe_recommendations", f"use_{source}", "answer_cafe_followup"],
        response_language=language,
    )


def build_improved_itinerary_answer(prompt: str, context: dict[str, Any], session_id: str) -> ChatResponse:
    captured = dict(context.get("captured_fields", {}))
    city_name = context.get("city") or captured.get("city_or_area")
    budget_cap = int(captured.get("budget_cap") or 0)
    number_of_people = int(captured.get("number_of_people") or 1)
    itinerary = [dict(item) for item in context.get("itinerary", [])]
    cost_summary = dict(context.get("cost_summary", {}))
    transport_info = dict(context.get("transport_info", {}))
    transport_cost = int(transport_info.get("estimated_transport_cost") or cost_summary.get("transport_cost") or 0)
    current_total = int(cost_summary.get("total_cost") or 0)
    remaining = max(budget_cap - current_total, 0)

    city_data = find_city_data(city_name, load_all_city_data()) if city_name else None
    if not city_data or not itinerary or remaining <= 0:
        message = "Mình chưa có đủ ngân sách hoặc dữ liệu để cải thiện lịch trình hiện tại mà vẫn đảm bảo không vượt ngân sách."
        return ChatResponse(
            session_id=session_id,
            response_type="text_answer",
            message=message,
            captured_fields=captured,
            city=city_name,
            tool_trace=["use_session_context", "improve_itinerary_failed"],
            response_language=detect_response_language(prompt),
        )

    used_ids = {item.get("id") for item in itinerary}
    used_names = {normalize_text(item.get("name")) for item in itinerary}

    def candidate_score(place: dict[str, Any]) -> tuple[int, int, str]:
        cost = int(place.get("average_cost_per_person") or 0)
        place_type = str(place.get("type", "tham_quan"))
        premium = 3 if cost > 0 else 0
        experience = 2 if place_type in {"tham_quan", "cafe"} else 1
        budget_fit = 1 if place.get("is_good_for_budget_travelers") else 0
        return (premium + experience + budget_fit, cost, str(place.get("name", "")))

    candidates = [
        dict(place)
        for place in city_data.places
        if place.get("id") not in used_ids
        and normalize_text(place.get("name")) not in used_names
        and int(place.get("average_cost_per_person") or 0) * number_of_people <= max(remaining - 50000, 0)
    ]
    candidates.sort(key=candidate_score, reverse=True)

    added: list[dict[str, Any]] = []
    for candidate in candidates:
        added_cost = int(candidate.get("average_cost_per_person") or 0) * number_of_people
        if added_cost > remaining:
            continue
        if itinerary and any(item.get("day") for item in itinerary):
            day_counts: dict[int, int] = {}
            for item in itinerary:
                day = int(item.get("day") or 1)
                day_counts[day] = day_counts.get(day, 0) + 1
            target_day = min(day_counts, key=day_counts.get)
            candidate["day"] = target_day
        candidate["budget_reason"] = "Thêm sau yêu cầu cải thiện: dùng phần ngân sách còn dư để tăng trải nghiệm nhưng vẫn kiểm tra không vượt trần."
        itinerary.append(candidate)
        added.append(candidate)
        remaining -= added_cost
        if len(added) >= 2:
            break

    if not added:
        message = "Mình chưa tìm được hoạt động phù hợp để thêm mà vẫn nằm trong ngân sách. Có thể thử tăng ngân sách hoặc yêu cầu rõ hơn: thêm cafe, thêm điểm check-in, hoặc nâng cấp bữa tối."
        return ChatResponse(
            session_id=session_id,
            response_type="text_answer",
            message=message,
            captured_fields=captured,
            city=city_name,
            tool_trace=["use_session_context", "search_upgrade_candidates", "no_budget_safe_upgrade"],
            response_language=detect_response_language(prompt),
        )

    itinerary.sort(key=lambda item: (int(item.get("day") or 1), item.get("recommended_time_slot") or "99:99"))
    new_cost_summary = calculate_trip_cost(itinerary, number_of_people, transport_cost)
    budget_status = check_budget_status(budget_cap, int(new_cost_summary["total_cost"]))
    if budget_status["status"] == "OVER_BUDGET":
        message = "Mình đã thử cải thiện nhưng phương án mới sẽ vượt ngân sách, nên chưa cập nhật lịch trình."
        return ChatResponse(
            session_id=session_id,
            response_type="text_answer",
            message=message,
            captured_fields=captured,
            city=city_name,
            tool_trace=["use_session_context", "reject_over_budget_upgrade"],
            response_language=detect_response_language(prompt),
        )

    upgraded = dict(context)
    upgraded["itinerary"] = itinerary
    upgraded["cost_summary"] = {**new_cost_summary, **budget_status}
    upgraded["budget_message"] = (
        f"Mình đã cải thiện lịch trình bằng cách thêm {len(added)} trải nghiệm mới. "
        f"Tổng mới là {vnd(new_cost_summary['total_cost'])}, còn dư {vnd(budget_status['remaining_budget'])}."
    )
    upgraded["tool_trace"] = [
        *context.get("tool_trace", []),
        "use_session_context",
        "search_upgrade_candidates",
        "add_budget_safe_experiences",
        "recalculate_trip_cost",
    ]
    SESSION_CONTEXT[session_id] = upgraded
    return normalize_agent_response(upgraded, session_id)


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
    if context and is_improvement_followup(message) and context.get("itinerary") and not should_start_new_trip(message):
        return build_improved_itinerary_answer(message, context, session_id)

    if has_pending_required_fields(context) and not should_start_new_trip(message):
        result = run_budget_travel_agent(build_merged_contextual_prompt(message, context))
    else:
        result = run_budget_travel_agent(message)
        if result.get("response_type") == "missing_required_input" and context:
            result = run_budget_travel_agent(build_strong_contextual_prompt(message, context))

    if result.get("response_type") != "out_of_scope":
        SESSION_CONTEXT[session_id] = result

    return normalize_agent_response(result, session_id)


@app.post("/api/sessions/{session_id}/reset", response_model=ResetResponse)
def reset_session(session_id: str) -> ResetResponse:
    SESSION_CONTEXT.pop(session_id, None)
    return ResetResponse(session_id=session_id, status="reset")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
