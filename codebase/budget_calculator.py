from __future__ import annotations

import math
from typing import Any


FOOD_TYPES = {"an_sang", "an_trua", "an_toi", "food", "restaurant"}
CAFE_TYPES = {"cafe", "coffee"}


def vnd(value: int | float | None) -> str:
    if value is None:
        amount = 0
    elif isinstance(value, float) and math.isnan(value):
        amount = 0
    else:
        amount = int(value or 0)
    return f"{amount:,}".replace(",", ".") + " VND"


def estimate_transport_cost(
    transport_options: list[dict[str, Any]],
    number_of_people: int,
    transport_preference: str | None,
    number_of_segments: int,
) -> dict[str, Any]:
    preference = (transport_preference or "").lower()
    options = transport_options or []

    if not options:
        return {
            "transport_mode": "Ước lượng di chuyển",
            "estimated_transport_cost": 0,
            "saving_tip": "Chưa có dữ liệu phương tiện trong mock data.",
        }

    def option_cost(option: dict[str, Any]) -> int:
        cost = int(option.get("estimated_cost_per_trip") or 0)
        name = str(option.get("name", "")).lower()
        if "grab" in name or "taxi" in name:
            return cost * max(number_of_segments, 1)
        if "xe máy" in name or "rental" in name:
            bikes_needed = max((number_of_people + 1) // 2, 1)
            return cost * bikes_needed
        return cost * max(number_of_segments, 1)

    if "đi bộ" in preference or "walk" in preference:
        selected = next((item for item in options if "đi bộ" in str(item.get("name", "")).lower()), options[0])
    elif "grab" in preference or "taxi" in preference:
        selected = next((item for item in options if "grab" in str(item.get("name", "")).lower() or "taxi" in str(item.get("name", "")).lower()), options[0])
    elif "xe máy" in preference or "thuê" in preference:
        selected = next((item for item in options if "xe máy" in str(item.get("name", "")).lower()), options[0])
    else:
        selected = min(options, key=option_cost)

    return {
        "transport_mode": selected.get("name", "Phương tiện đề xuất"),
        "estimated_transport_cost": option_cost(selected),
        "saving_tip": selected.get("saving_tip", ""),
        "best_for": selected.get("best_for", ""),
    }


def calculate_trip_cost(
    itinerary: list[dict[str, Any]],
    number_of_people: int,
    transport_cost: int,
) -> dict[str, Any]:
    food_cost = 0
    cafe_cost = 0
    activity_cost = 0
    rows: list[dict[str, Any]] = []

    for item in itinerary:
        place_type = str(item.get("type", "tham_quan"))
        cost_per_person = int(item.get("average_cost_per_person") or 0)
        total = cost_per_person * number_of_people

        if place_type in FOOD_TYPES:
            category = "Ăn uống"
            food_cost += total
        elif place_type in CAFE_TYPES:
            category = "Cafe"
            cafe_cost += total
        else:
            category = "Đi chơi / tham quan"
            activity_cost += total

        rows.append(
            {
                "Hạng mục": category,
                "Tên": item.get("name", ""),
                "Chi phí/người": cost_per_person,
                "Số người": number_of_people,
                "Tổng chi phí": total,
            }
        )

    rows.append(
        {
            "Hạng mục": "Di chuyển",
            "Tên": "Chi phí di chuyển dự kiến",
            "Chi phí/người": None,
            "Số người": number_of_people,
            "Tổng chi phí": transport_cost,
        }
    )

    total_cost = food_cost + cafe_cost + activity_cost + int(transport_cost or 0)
    return {
        "food_cost": food_cost,
        "cafe_cost": cafe_cost,
        "activity_cost": activity_cost,
        "transport_cost": int(transport_cost or 0),
        "total_cost": total_cost,
        "cost_rows": rows,
    }


def check_budget_status(budget_cap: int, total_cost: int) -> dict[str, Any]:
    remaining = int(budget_cap or 0) - int(total_cost or 0)
    if remaining >= 0:
        ratio = total_cost / budget_cap if budget_cap else 1
        status = "NEAR_LIMIT" if ratio >= 0.85 else "WITHIN_BUDGET"
        return {
            "status": status,
            "remaining_budget": remaining,
            "over_budget_amount": 0,
        }

    return {
        "status": "OVER_BUDGET",
        "remaining_budget": 0,
        "over_budget_amount": abs(remaining),
    }


def generate_saving_suggestions(
    itinerary: list[dict[str, Any]],
    over_budget_amount: int,
    transport_info: dict[str, Any],
    number_of_people: int,
) -> dict[str, Any]:
    suggestions: list[dict[str, Any]] = []

    saving_tip = transport_info.get("saving_tip")
    if saving_tip:
        suggestions.append(
            {
                "type": "transport",
                "title": "Tối ưu chi phí di chuyển",
                "detail": saving_tip,
                "estimated_saving": None,
            }
        )

    for item in itinerary:
        alternative = item.get("cheaper_alternative")
        if not alternative:
            continue
        saving_per_person = int(alternative.get("estimated_saving_per_person") or 0)
        suggestions.append(
            {
                "type": "place_alternative",
                "title": f"Đổi '{item.get('name')}'",
                "detail": f"Cân nhắc '{alternative.get('name')}'. {alternative.get('note', '')}".strip(),
                "estimated_saving": saving_per_person * number_of_people,
            }
        )

    for item in itinerary:
        for tip in item.get("saving_tips", [])[:1]:
            suggestions.append(
                {
                    "type": "saving_tip",
                    "title": f"Mẹo tiết kiệm tại {item.get('name')}",
                    "detail": tip,
                    "estimated_saving": None,
                }
            )

    minimum_budget = None
    if over_budget_amount > 0:
        current_total_from_required = sum(
            int(item.get("average_cost_per_person") or 0) * number_of_people
            for item in itinerary
            if item.get("required")
        )
        if current_total_from_required:
            minimum_budget = current_total_from_required + int(transport_info.get("estimated_transport_cost") or 0)

    return {
        "suggestions": suggestions[:5],
        "minimum_budget_to_keep_required_places": minimum_budget,
    }
