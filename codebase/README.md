# Budget Travel Planner AI

Demo trợ lý lập lịch trình du lịch theo ngân sách. User có thể nhập tự nhiên bằng tiếng Việt hoặc tiếng Anh; hệ thống sẽ kiểm tra input bắt buộc, tạo lịch trình, tính chi phí, gợi ý phương tiện, thời tiết, map/review và các mẹo tiết kiệm.

## Tính năng chính

- Chat nhiều lượt, có nhớ context trong cùng một chuyến đi.
- Input bắt buộc: ngân sách, số người, thành phố/khu vực muốn đi, điểm xuất phát.
- Hỗ trợ duration như `1 ngày`, `3 ngày`, `5 ngày`; lịch trình sẽ được chia theo từng ngày.
- Nếu thiếu input, agent hỏi lại và lưu phần đã có để lượt sau bổ sung tiếp.
- Dữ liệu chính lấy từ `Data/Data_10provinces.json`.
- Nếu điểm đến không có trong mock data, agent thử web fallback và lưu vào `Data/web_city_cache.json`.
- Có guardrail để tránh sinh lịch trình khi dữ liệu web không đủ tin cậy.
- Tính chi phí ăn uống, cafe, tham quan, di chuyển và tổng tiền.
- Gợi ý tiết kiệm khi vượt ngân sách; nếu còn dư nhiều, agent cố tối ưu lịch trình để trải nghiệm tốt hơn.
- Frontend chat có nút Stop để hủy request đang generate.

## Cấu trúc thư mục

```text
codebase/
├── api.py                         # FastAPI backend + session context
├── travel_agent.py                # Parser, guardrails, itinerary agent
├── budget_calculator.py           # Tính chi phí, budget status, transport estimate
├── data_loader.py                 # Load/search mock data
├── external_city_data.py          # Web fallback + cache
├── enrichment_tools.py            # Weather/map/review enrichment
├── agent_logger.py                # Log agent runs
├── schemas.py                     # Pydantic schemas
├── requirements.txt               # Python dependencies
├── Data/
│   ├── Data_10provinces.json
│   └── web_city_cache.json
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── tools/
    └── budget_travel_agent_tools_config.json
```

## Cài đặt

Từ thư mục gốc project:

```powershell
cd D:\Vin\Day06-C401-NhomA4
python -m venv venv
.\venv\Scripts\activate
pip install -r codebase\requirements.txt
```

Tạo file `.env` ở thư mục gốc `Day06-C401-NhomA4`:

```env
9_ROUTER_API_KEY=your_key
9ROUTER_BASE_URL=your_base_url
9ROUTER_MODEL=your_model
TAVILY_API_KEY=your_tavily_key
```

`TAVILY_API_KEY` dùng cho web fallback. Nếu thiếu key này, agent vẫn chạy với mock data nhưng khả năng xử lý tỉnh ngoài data sẽ hạn chế.

## Chạy project

```powershell
cd D:\Vin\Day06-C401-NhomA4
.\venv\Scripts\activate
python -m uvicorn codebase.api:app --host 127.0.0.1 --port 8000
```

Mở frontend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Test case gợi ý

Happy path một lượt:

```text
Mình có 2 triệu, đi 3 người, xuất phát từ Hội An, muốn đi Đà Nẵng 1 ngày, ưu tiên check-in và ăn uống rẻ.
```

Multi-turn thiếu điểm xuất phát:

```text
tôi muốn đi hà nội 5 triệu 3 người 5 ngày
```

Agent sẽ hỏi thiếu điểm xuất phát. Nhập tiếp:

```text
từ Hưng Yên lên Hà Nội
```

Agent sẽ tạo lịch trình nhiều ngày thay vì dồn toàn bộ hoạt động vào một ngày.

Follow-up trong cùng đoạn chat:

```text
có quán cafe nào ngon ở Hà Nội không?
```

Guardrail ngoài luồng:

```text
viết code Python cho tôi
```

Điểm đến ngoài mock data:

```text
Mình có 2 triệu, đi 2 người, xuất phát từ Hà Nội, muốn đi Cao Bằng, thích thiên nhiên và ăn uống rẻ.
```

## Ghi chú demo

- Giá trong hệ thống là ước lượng để demo, không phải báo giá thực tế.
- Dữ liệu web fallback có confidence thấp hơn mock data và nên kiểm tra lại nguồn trước khi demo thật.
- Log agent được ghi ở `logs/agent_runs.jsonl`.
- Cache web fallback nằm ở `Data/web_city_cache.json`; nếu cache bị nhiễu, có thể xóa record của tỉnh đó để agent tìm lại.
