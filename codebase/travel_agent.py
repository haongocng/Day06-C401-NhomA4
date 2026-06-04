from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, load_dotenv
from openai import OpenAI

from budget_calculator import (
    calculate_trip_cost,
    check_budget_status,
    estimate_transport_cost,
    generate_saving_suggestions,
    vnd,
)
from data_loader import find_city_data, list_supported_cities, load_all_city_data, search_places
from external_city_data import fetch_external_city_data


BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "tools" / "budget_travel_agent_tools_config.json"
ENV_PATH = BASE_DIR.parent / ".env"


FIELD_LABELS = {
    "budget_cap": "ngân sách tổng cho cả nhóm",
    "number_of_people": "số người tham gia",
    "city_or_area": "thành phố/khu vực muốn đi",
    "starting_location": "điểm xuất phát",
}


def load_agent_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_llm_client() -> tuple[OpenAI | None, str | None]:
    load_dotenv(ENV_PATH)
    values = dotenv_values(ENV_PATH)

    api_key = os.getenv("9_ROUTER_API_KEY") or values.get("9_ROUTER_API_KEY")
    base_url = os.getenv("9ROUTER_BASE_URL") or values.get("9ROUTER_BASE_URL")
    model = os.getenv("9ROUTER_MODEL") or values.get("9ROUTER_MODEL")

    if not api_key or not base_url or not model:
        return None, None
    return OpenAI(api_key=api_key, base_url=base_url, timeout=5, max_retries=0), model


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def parse_user_request_with_llm(user_text: str, config: dict[str, Any]) -> dict[str, Any] | None:
    client, model = load_llm_client()
    if not client or not model:
        return None

    supported_cities = ", ".join(list_supported_cities())
    prompt = f"""
Extract trip planning fields from the user's Vietnamese request.

Supported cities in mock data: {supported_cities}

Return only valid JSON with this schema:
{{
  "budget_cap": integer or null,
  "number_of_people": integer or null,
  "city_or_area": string or null,
  "starting_location": string or null,
  "desired_places": array of strings,
  "travel_date": string or null,
  "travel_preferences": array of strings,
  "transport_preference": string or null,
  "meal_preferences": array of strings
}}

Do not invent missing required fields. If the user says they do not know where to go,
leave desired_places empty but keep city_or_area if present.

User request:
{user_text}
""".strip()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": config.get("system_prompt", "")},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            timeout=8,
        )
        content = response.choices[0].message.content or ""
        return _extract_json_object(content)
    except Exception:
        return None


def _parse_budget(text: str) -> int | None:
    normalized = text.lower()
    patterns = [
        r"(\d+(?:[\.,]\d+)?)\s*(triệu|trieu|m)\b",
        r"(\d+(?:[\.,]\d+)?)\s*(k|nghìn|nghin)\b",
        r"(\d[\d\.,\s]{3,})\s*(đ|vnd|vnđ)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if not match:
            continue
        raw_amount = match.group(1)
        unit = match.group(2) if len(match.groups()) > 1 else ""
        if unit in {"triệu", "trieu", "m", "k", "nghìn", "nghin"}:
            amount = float(raw_amount.replace(",", "."))
        else:
            return _parse_vnd_integer(raw_amount)
        if unit in {"triệu", "trieu", "m"}:
            return int(amount * 1_000_000)
        if unit in {"k", "nghìn", "nghin"}:
            return int(amount * 1_000)
    return None


def _parse_vnd_integer(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text = str(value).lower().strip()
    if not text:
        return None

    compact = re.sub(r"\s+", "", text)
    compact = compact.replace("vnd", "").replace("vnđ", "").replace("đ", "")

    unit_match = re.fullmatch(r"(\d+(?:[\.,]\d+)?)(triệu|trieu|m|k|nghìn|nghin)", compact)
    if unit_match:
        number = float(unit_match.group(1).replace(",", "."))
        unit = unit_match.group(2)
        return int(number * (1_000_000 if unit in {"triệu", "trieu", "m"} else 1_000))

    digits_only = re.sub(r"[^\d]", "", compact)
    if not digits_only:
        return None
    return int(digits_only)


def _parse_people(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(người|nguoi|bạn|ban)", text.lower())
    if match:
        return int(match.group(1))
    return None


def _clean_city_or_area(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip(" .,")
    if not text:
        return None
    text = re.split(r"\b(?:thích|thich|và thích|va thich|chưa biết|chua biet)\b", text, maxsplit=1)[0]
    text = re.sub(r"\b\d+\s*(ngày|ngay|đêm|dem|hôm|hom)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(1 ngày|mot ngay|một ngày)\b", "", text, flags=re.IGNORECASE)
    return " ".join(text.strip(" .,").split()) or None


def _coerce_parsed_request(parsed: dict[str, Any]) -> dict[str, Any]:
    parsed["budget_cap"] = _parse_vnd_integer(parsed.get("budget_cap"))
    parsed["city_or_area"] = _clean_city_or_area(parsed.get("city_or_area"))

    people = parsed.get("number_of_people")
    if isinstance(people, str):
        match = re.search(r"\d+", people)
        parsed["number_of_people"] = int(match.group(0)) if match else None
    elif isinstance(people, float):
        parsed["number_of_people"] = int(people)

    for field in ["desired_places", "travel_preferences", "meal_preferences"]:
        value = parsed.get(field)
        if value is None:
            parsed[field] = []
        elif isinstance(value, str):
            parsed[field] = [value] if value.strip() else []

    return parsed


def _fallback_parse_user_request(user_text: str) -> dict[str, Any]:
    city_data = load_all_city_data()
    lower = user_text.lower()
    starting_location = None
    start_patterns = [
        r"(?:xuất phát từ|xuat phat tu|bắt đầu từ|bat dau tu|đi từ|di tu)\s+([^,.]+)",
        r"(?:ở|o)\s+([^,.]+)\s+(?:muốn|muon|đi|di)",
    ]
    for pattern in start_patterns:
        match = re.search(pattern, lower)
        if match:
            starting_location = match.group(1).strip()
            break

    target_segment = None
    target_match = re.search(
        r"(?:muốn đi|muon di|đến|den|du lịch|du lich|tham quan)\s+([^,.]+)",
        lower,
    )
    if target_match:
        target_segment = _clean_city_or_area(target_match.group(1))

    city_or_area = None
    supported_cities = list_supported_cities(city_data)
    search_texts = [target_segment] if target_segment else [lower]
    for search_text in search_texts:
        if not search_text:
            continue
        for city in supported_cities:
            if city.lower() in search_text:
                city_or_area = city
                break
        if city_or_area:
            break

    if not city_or_area and not target_segment:
        for city in supported_cities:
            if city.lower() in lower:
                city_or_area = city
                break
    if not city_or_area and target_segment:
        city_or_area = target_segment.strip()

    desired_places: list[str] = []
    for item in city_data:
        for place in item.places:
            name = place.get("name", "")
            compact_name = name.split("&")[0].split("(")[0].strip()
            if compact_name and compact_name.lower() in lower:
                desired_places.append(compact_name)

    no_destination_words = ["chưa biết đi đâu", "chua biet di dau", "gợi ý", "goi y", "inspire"]
    if any(phrase in lower for phrase in no_destination_words):
        desired_places = []

    preferences = []
    for keyword in ["rẻ", "re", "check-in", "ăn uống", "an uong", "văn hóa", "van hoa", "đi bộ", "di bo"]:
        if keyword in lower:
            preferences.append(keyword)

    transport_preference = None
    for keyword in ["đi bộ", "di bo", "grab", "taxi", "xe máy", "xe may", "thuê xe"]:
        if keyword in lower:
            transport_preference = keyword
            break

    return {
        "budget_cap": _parse_budget(user_text),
        "number_of_people": _parse_people(user_text),
        "city_or_area": city_or_area,
        "starting_location": starting_location,
        "desired_places": desired_places,
        "travel_date": None,
        "travel_preferences": preferences,
        "transport_preference": transport_preference,
        "meal_preferences": [],
    }


def parse_user_request(user_text: str, config: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_user_request_with_llm(user_text, config)
    fallback_parsed = _fallback_parse_user_request(user_text)
    if not parsed:
        parsed = fallback_parsed
    else:
        for field, value in fallback_parsed.items():
            if parsed.get(field) in [None, "", []] and value not in [None, "", []]:
                parsed[field] = value

    defaults = {
        "budget_cap": None,
        "number_of_people": None,
        "city_or_area": None,
        "starting_location": None,
        "desired_places": [],
        "travel_date": None,
        "travel_preferences": [],
        "transport_preference": None,
        "meal_preferences": [],
    }
    defaults.update(parsed)
    return _coerce_parsed_request(defaults)


def validate_required_inputs(parsed_request: dict[str, Any]) -> dict[str, Any]:
    missing = [
        field
        for field in FIELD_LABELS
        if parsed_request.get(field) in [None, "", []]
    ]
    if missing:
        return {
            "is_valid": False,
            "missing_fields": missing,
            "mode": "missing_required_input",
        }
    return {
        "is_valid": True,
        "missing_fields": [],
        "mode": "normal" if parsed_request.get("desired_places") else "inspire_mode",
    }


def build_itinerary(
    matched_places: list[dict[str, Any]],
    suggested_places: list[dict[str, Any]],
    mode: str,
    limit: int = 6,
) -> list[dict[str, Any]]:
    itinerary = [dict(place) for place in matched_places]

    preferred_order = ["an_sang", "tham_quan", "an_trua", "cafe", "tham_quan", "an_toi"]
    if mode == "inspire_mode":
        pool = suggested_places
    else:
        pool = [place for place in suggested_places if place.get("id") not in {p.get("id") for p in itinerary}]

    for place_type in preferred_order:
        if len(itinerary) >= limit:
            break
        match = next(
            (
                place
                for place in pool
                if place.get("type") == place_type and place.get("id") not in {p.get("id") for p in itinerary}
            ),
            None,
        )
        if match:
            itinerary.append(dict(match))

    for place in pool:
        if len(itinerary) >= limit:
            break
        if place.get("id") not in {p.get("id") for p in itinerary}:
            itinerary.append(dict(place))

    itinerary.sort(key=lambda item: item.get("recommended_time_slot") or "99:99")
    return itinerary


def run_budget_travel_agent(user_text: str) -> dict[str, Any]:
    config = load_agent_config()
    parsed = parse_user_request(user_text, config)
    validation = validate_required_inputs(parsed)

    if not validation["is_valid"]:
        labels = [FIELD_LABELS[field] for field in validation["missing_fields"]]
        return {
            "response_type": "missing_required_input",
            "captured_fields": parsed,
            "missing_fields": validation["missing_fields"],
            "follow_up_question": "Mình còn thiếu: " + ", ".join(labels) + ". Bạn bổ sung giúp mình để mình tạo tour nhé.",
            "itinerary": [],
            "cost_summary": {},
            "budget_message": "",
            "saving_suggestions": [],
            "tool_trace": ["parse_user_request", "validate_required_inputs", "ask_missing_fields"],
        }

    all_city_data = load_all_city_data()
    city = find_city_data(parsed["city_or_area"], all_city_data)
    used_web_fallback = False
    if not city:
        city = fetch_external_city_data(parsed["city_or_area"])
        used_web_fallback = city is not None
        if not city:
            return {
                "response_type": "missing_required_input",
                "captured_fields": parsed,
                "missing_fields": ["city_or_area"],
                "follow_up_question": "Hiện mock data chưa hỗ trợ khu vực này và web fallback chưa lấy được dữ liệu đủ tin cậy. Bạn thử lại với một khu vực khác hoặc bật Tavily/9router rồi chạy lại nhé. Các nơi có sẵn: "
                + ", ".join(list_supported_cities(all_city_data)),
                "itinerary": [],
                "cost_summary": {},
                "budget_message": "",
                "saving_suggestions": [],
                "tool_trace": ["parse_user_request", "validate_required_inputs", "search_mock_places", "web_search_costs_failed"],
            }

    place_result = search_places(
        city,
        query_places=parsed.get("desired_places", []),
        preferences=parsed.get("travel_preferences", []),
        limit=8,
    )
    mode = validation["mode"]
    itinerary = build_itinerary(place_result["matched_places"], place_result["suggested_places"], mode)
    transport_info = estimate_transport_cost(
        city.transport_options,
        int(parsed["number_of_people"]),
        parsed.get("transport_preference"),
        number_of_segments=max(len(itinerary) - 1, 1),
    )
    cost_summary = calculate_trip_cost(
        itinerary,
        int(parsed["number_of_people"]),
        int(transport_info["estimated_transport_cost"]),
    )
    budget_status = check_budget_status(int(parsed["budget_cap"]), int(cost_summary["total_cost"]))

    saving_result = {"suggestions": [], "minimum_budget_to_keep_required_places": None}
    if budget_status["status"] == "OVER_BUDGET":
        saving_result = generate_saving_suggestions(
            itinerary,
            budget_status["over_budget_amount"],
            transport_info,
            int(parsed["number_of_people"]),
        )

    status_text = {
        "WITHIN_BUDGET": f"Trong ngân sách. Còn dư {vnd(budget_status['remaining_budget'])}.",
        "NEAR_LIMIT": f"Vẫn trong ngân sách nhưng đã gần chạm trần. Còn dư {vnd(budget_status['remaining_budget'])}.",
        "OVER_BUDGET": f"Vượt ngân sách {vnd(budget_status['over_budget_amount'])}. Mình giữ các điểm bắt buộc và đề xuất cách tiết kiệm bên dưới.",
    }[budget_status["status"]]
    if budget_status["status"] != "OVER_BUDGET":
        status_text += " Bạn có muốn mình cải thiện lịch trình để trải nghiệm tốt hơn trong phần ngân sách còn lại không?"

    metadata = city.metadata or {}

    return {
        "response_type": mode if mode == "inspire_mode" else "itinerary_result",
        "captured_fields": parsed,
        "city": city.metadata.get("city"),
        "data_source": metadata.get("data_source", "mock_data"),
        "data_confidence": metadata.get("confidence", "high"),
        "confidence_note": metadata.get("confidence_note", ""),
        "source_urls": metadata.get("source_urls", []),
        "fetched_at": metadata.get("fetched_at"),
        "unmatched_places": place_result["unmatched_places"],
        "itinerary": itinerary,
        "transport_info": transport_info,
        "cost_summary": {**cost_summary, **budget_status},
        "budget_message": status_text,
        "saving_suggestions": saving_result["suggestions"],
        "minimum_budget_to_keep_required_places": saving_result["minimum_budget_to_keep_required_places"],
        "tool_trace": [
            "parse_user_request",
            "validate_required_inputs",
            "search_mock_places" if not used_web_fallback else "web_search_costs",
            "cache_external_city_data" if used_web_fallback else "use_mock_data",
            "estimate_transport_cost",
            "build_itinerary",
            "calculate_trip_cost",
            "check_budget_status",
            "generate_saving_suggestions" if budget_status["status"] == "OVER_BUDGET" else "skip_saving_suggestions",
        ],
    }
