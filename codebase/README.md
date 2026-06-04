# Codebase

Đây là nơi nhóm nộp toàn bộ phần code của prototype. Mục tiêu là để giảng viên và các nhóm khác nhìn được sản phẩm chạy như thế nào, và mỗi thành viên đã đóng góp ra sao.

## Prototype: BudgetTrip Planner

Demo Streamlit 1-agent cho bài toán lập tour 1 ngày theo ngân sách.

Agent chạy theo flow:

```text
parse_user_request
-> validate_required_inputs
-> search_mock_places / ask_missing_fields
-> estimate_transport_cost
-> build_itinerary
-> calculate_trip_cost
-> check_budget_status
-> generate_saving_suggestions
```

Các rule chính:

- Input bắt buộc: ngân sách, số người, thành phố/khu vực, điểm xuất phát.
- Địa điểm muốn đi là optional. Nếu thiếu, app bật inspire mode và gợi ý route tiết kiệm từ mock data.
- Nếu thiếu input bắt buộc, app hỏi lại và không tự bịa lịch trình.
- Nếu vượt ngân sách, app giữ địa điểm bắt buộc, cảnh báo số tiền vượt và gợi ý tiết kiệm.

## Cách chạy

Từ folder repo:

```powershell
cd .\Day06-C401-NhomA4
.\venv\Scripts\python.exe -m pip install -r .\codebase\requirements.txt
.\venv\Scripts\python.exe -m streamlit run .\codebase\app.py
```

App đọc biến môi trường 9router từ file `.env` ở root repo:

```text
9_ROUTER_API_KEY=...
9ROUTER_BASE_URL=http://localhost:20128/v1
9ROUTER_MODEL=oc/mimo-v2.5-free
```

Nếu 9router/local LLM chưa chạy, prototype vẫn có fallback parser đơn giản để demo các luồng chính.

## Web fallback cho tỉnh ngoài mock data

Nếu `Data/Data_10provinces.json` chưa có khu vực user nhập, agent sẽ thử:

```text
Tavily web search
-> 9router chuẩn hoá snippets thành schema địa điểm/chi phí
-> lưu vào Data/web_city_cache.json
-> lập lịch trình với confidence + source URLs
```

Cần thêm biến:

```text
TAVILY_API_KEY=...
```

Guardrail:

- Dữ liệu web-cache luôn hiển thị độ tin cậy `low/medium/high`.
- Giá có `cost_confidence`, nếu không chắc thì chỉ là ước lượng demo.
- Nếu web search hoặc LLM không trả đủ dữ liệu, app không tự bịa tour.

## Nhóm cần làm

- Đưa mã nguồn của prototype vào folder này. Nếu prototype được deploy hoặc host ở nơi khác, hãy để lại đường link kèm hướng dẫn truy cập.
- Trong file `README.md` của nhóm, ghi rõ ba điều: cách chạy prototype (các bước cài đặt và biến môi trường nếu cần), những công cụ và API đã dùng (model AI, framework, công cụ dựng giao diện…), và phần phân công ai làm gì.
- Mỗi thành viên nên có ít nhất một commit thực chất trong repo — đây là căn cứ để ghi nhận đóng góp của từng người.

## Lưu ý

Đừng commit những thông tin nhạy cảm như API key hay file `.env`. Nếu prototype cần các biến môi trường, hãy dùng một file `.env.example` để mô tả các biến đó thay vì để lộ giá trị thật.
