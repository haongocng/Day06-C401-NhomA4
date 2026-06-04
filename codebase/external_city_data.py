from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import dotenv_values, load_dotenv
from openai import OpenAI

from data_loader import CityData, normalize_text


BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR.parent / ".env"
CACHE_PATH = BASE_DIR / "Data" / "web_city_cache.json"


def _load_env() -> dict[str, str | None]:
    load_dotenv(ENV_PATH)
    values = dotenv_values(ENV_PATH)
    return {
        "tavily_api_key": os.getenv("TAVILY_API_KEY") or values.get("TAVILY_API_KEY"),
        "llm_api_key": os.getenv("9_ROUTER_API_KEY") or values.get("9_ROUTER_API_KEY"),
        "llm_base_url": os.getenv("9ROUTER_BASE_URL") or values.get("9ROUTER_BASE_URL"),
        "llm_model": os.getenv("9ROUTER_MODEL") or values.get("9ROUTER_MODEL"),
    }


def _read_cache() -> list[dict[str, Any]]:
    if not CACHE_PATH.exists():
        return []
    with CACHE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_cache(records: list[dict[str, Any]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def _record_to_city_data(record: dict[str, Any]) -> CityData:
    return CityData(
        metadata=record.get("metadata", {}),
        budget_planning_rules=record.get("budget_planning_rules", {}),
        transport_options=record.get("transport_options", []),
        places=record.get("places", []),
    )


def get_cached_external_city(city_or_area: str) -> CityData | None:
    query = normalize_text(city_or_area)
    for record in _read_cache():
        city = normalize_text(record.get("metadata", {}).get("city"))
        if city and (city == query or city in query or query in city):
            return _record_to_city_data(record)
    return None


def _save_external_city(record: dict[str, Any]) -> None:
    records = _read_cache()
    city_key = normalize_text(record.get("metadata", {}).get("city"))
    records = [
        item
        for item in records
        if normalize_text(item.get("metadata", {}).get("city")) != city_key
    ]
    records.append(record)
    _write_cache(records)


def _tavily_search(city_or_area: str) -> dict[str, Any] | None:
    env = _load_env()
    api_key = env.get("tavily_api_key")
    if not api_key:
        return None

    query = (
        f"{city_or_area} du lịch 1 ngày địa điểm tham quan ăn uống giá vé "
        "chi phí di chuyển nguồn chính thức hoặc review"
    )
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 8,
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=12,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _llm_extract_city_data(city_or_area: str, search_payload: dict[str, Any]) -> dict[str, Any] | None:
    env = _load_env()
    api_key = env.get("llm_api_key")
    base_url = env.get("llm_base_url")
    model = env.get("llm_model")
    if not api_key or not base_url or not model:
        return None

    sources = []
    for item in search_payload.get("results", [])[:8]:
        sources.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
            }
        )

    prompt = f"""
You convert web search snippets into safe mock travel planning data.

City/area: {city_or_area}

Rules:
- Use only information supported by the snippets and source URLs.
- If a price is not clearly available, use a conservative estimated price and mark cost_confidence as "low".
- Return Vietnamese names.
- Do not create hotels or booking flows.
- Build enough places for a one-day demo: attractions, breakfast/lunch/dinner/cafe if possible.
- Use types only from: tham_quan, an_sang, an_trua, an_toi, cafe.
- Confidence must be:
  high: at least 5 useful places and 4 distinct source URLs
  medium: at least 4 useful places and 2 distinct source URLs
  low: otherwise

Return only JSON:
{{
  "city": "string",
  "confidence": "low|medium|high",
  "confidence_note": "string",
  "source_urls": ["string"],
  "places": [
    {{
      "name": "string",
      "type": "tham_quan|an_sang|an_trua|an_toi|cafe",
      "area": "string",
      "average_cost_per_person": integer,
      "cost_confidence": "low|medium|high",
      "estimated_duration_minutes": integer,
      "recommended_time_slot": "HH:MM-HH:MM",
      "tags": ["string"],
      "is_good_for_budget_travelers": boolean,
      "saving_tips": ["string"],
      "source_urls": ["string"]
    }}
  ]
}}

Search snippets:
{json.dumps(sources, ensure_ascii=False)}
""".strip()

    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=10, max_retries=0)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful extraction tool. Return strict JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        return _extract_json(content)
    except Exception:
        return None


def _extract_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _build_record(extracted: dict[str, Any]) -> dict[str, Any]:
    city = extracted.get("city") or ""
    source_urls = extracted.get("source_urls", [])
    confidence = extracted.get("confidence", "low")

    places = []
    for index, place in enumerate(extracted.get("places", []), start=1):
        places.append(
            {
                "id": f"web_{normalize_text(city).replace(' ', '_')}_{index:03d}",
                "name": place.get("name", ""),
                "type": place.get("type", "tham_quan"),
                "area": place.get("area", city),
                "average_cost_per_person": int(place.get("average_cost_per_person") or 0),
                "cost_confidence": place.get("cost_confidence", "low"),
                "estimated_duration_minutes": int(place.get("estimated_duration_minutes") or 60),
                "recommended_time_slot": place.get("recommended_time_slot", "Linh hoạt"),
                "tags": place.get("tags", []),
                "is_good_for_budget_travelers": bool(place.get("is_good_for_budget_travelers", True)),
                "saving_tips": place.get("saving_tips", []),
                "source_urls": place.get("source_urls", source_urls),
            }
        )

    return {
        "metadata": {
            "project_name": "AI Travel Budget Planner",
            "city": city,
            "currency": "VND",
            "version": "web-cache-1.0",
            "description": "Dữ liệu lấy từ web fallback, cần hiển thị confidence và nguồn.",
            "data_source": "web_cache",
            "confidence": confidence,
            "confidence_note": extracted.get("confidence_note", ""),
            "source_urls": source_urls,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "budget_planning_rules": {
            "budget_status": {
                "within_budget": "Tổng chi phí <= ngân sách người dùng",
                "over_budget": "Tổng chi phí > ngân sách người dùng",
            },
            "required_place_policy": "Các địa điểm có required=true phải được giữ lại trong lịch trình, kể cả khi làm vượt ngân sách.",
            "suggestion_policy": "Dữ liệu web-cache phải hiển thị confidence; giá low-confidence chỉ là ước lượng.",
            "cost_formula": "total_cost = sum(place_cost_per_person * number_of_people) + transport_cost_total",
        },
        "transport_options": [
            {
                "id": f"web_transport_walk_{normalize_text(city).replace(' ', '_')}",
                "name": "Đi bộ / gom điểm gần nhau",
                "estimated_cost_per_trip": 0,
                "best_for": "Các lịch trình trung tâm hoặc các điểm gần nhau.",
                "saving_tip": "Vì đây là dữ liệu web fallback, hãy ưu tiên gom các điểm gần nhau và kiểm tra lại quãng đường trước khi đi.",
            },
            {
                "id": f"web_transport_grab_{normalize_text(city).replace(' ', '_')}",
                "name": "Taxi công nghệ / xe ôm công nghệ",
                "estimated_cost_per_trip": 50000,
                "best_for": "Di chuyển linh hoạt khi chưa có dữ liệu tuyến đường chính xác.",
                "saving_tip": "So sánh giá trên app trước khi đặt; chi phí này chỉ là ước lượng demo.",
            },
        ],
        "places": places,
    }


def _heuristic_extract_city_data(city_or_area: str, search_payload: dict[str, Any]) -> dict[str, Any] | None:
    results = search_payload.get("results", [])
    if not results:
        return None

    source_urls = [item.get("url") for item in results if item.get("url")][:6]
    if len(source_urls) < 2:
        return None

    type_cycle = ["tham_quan", "an_sang", "an_trua", "cafe", "tham_quan", "an_toi"]
    default_costs = {
        "tham_quan": 50000,
        "an_sang": 40000,
        "an_trua": 80000,
        "cafe": 45000,
        "an_toi": 80000,
    }
    time_slots = {
        "an_sang": "07:30-08:15",
        "tham_quan": "09:00-10:30",
        "an_trua": "12:00-13:00",
        "cafe": "15:00-15:45",
        "an_toi": "18:30-19:30",
    }

    places = []
    used_names: set[str] = set()
    for index, item in enumerate(results[:6]):
        place_type = type_cycle[index % len(type_cycle)]
        raw_title = item.get("title") or f"Gợi ý tại {city_or_area}"
        name = raw_title.split("|")[0].split("-")[0].strip()
        if len(name) > 80:
            name = name[:77].strip() + "..."
        normalized_name = normalize_text(name)
        if not normalized_name or normalized_name in used_names:
            continue
        used_names.add(normalized_name)
        places.append(
            {
                "name": name,
                "type": place_type,
                "area": city_or_area,
                "average_cost_per_person": default_costs[place_type],
                "cost_confidence": "low",
                "estimated_duration_minutes": 60,
                "recommended_time_slot": time_slots[place_type],
                "tags": ["web_fallback", "ước lượng"],
                "is_good_for_budget_travelers": default_costs[place_type] <= 50000,
                "saving_tips": [
                    "Dữ liệu này được suy luận từ web search, hãy kiểm tra lại giá/giờ mở cửa trước khi đi."
                ],
                "source_urls": [item.get("url")] if item.get("url") else source_urls[:2],
            }
        )

    if len(places) < 3:
        return None

    return {
        "city": city_or_area,
        "confidence": "low",
        "confidence_note": "LLM chuẩn hóa không phản hồi, nên agent dùng heuristic từ kết quả Tavily. Giá chỉ là ước lượng demo.",
        "source_urls": source_urls,
        "places": places,
    }


def fetch_external_city_data(city_or_area: str) -> CityData | None:
    cached = get_cached_external_city(city_or_area)
    if cached:
        return cached

    search_payload = _tavily_search(city_or_area)
    if not search_payload:
        return None

    extracted = _llm_extract_city_data(city_or_area, search_payload)
    if not extracted or not extracted.get("places"):
        extracted = _heuristic_extract_city_data(city_or_area, search_payload)
    if not extracted or not extracted.get("places"):
        return None

    record = _build_record(extracted)
    _save_external_city(record)
    return _record_to_city_data(record)
