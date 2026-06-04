# Toolkit — Từ Evidence Đến Build Slice

Dùng sau khi nhóm đã có evidence. Mục tiêu là chốt một build slice đủ nhỏ cho Day 06.

## 1. Gom evidence thành cụm

Các cụm pain chính rút ra từ evidence:

- "Phải mở nhiều app và tự cộng chi phí" — (evidence: self-use, interviews).
- "Ngân sách dễ bị vượt do chi phí phát sinh/giá thay đổi" — (quotes từ phỏng vấn, self-use cảnh báo vượt ngân sách).
- "Cần xác nhận đầu vào và chuẩn hoá thông tin" — (self-use observation: app yêu cầu xác nhận trước khi sinh lịch trình).
- "Muốn gợi ý cắt giảm chi phí/alternative options" — (competitor/app Layla pattern + user quotes).

## 2. Insight (theo form)

User [người trẻ / sinh viên hoặc khách du lịch tự túc có ngân sách hạn chế] không chỉ cần [danh sách địa điểm giá rẻ hoặc lọc theo mức giá].
Họ thật ra cần [sự an tâm tài chính: biết tổng chi tiêu sẽ nằm trong giới hạn và được cảnh báo/kéo lại kịp thời],
vì [evidence cho thấy họ mở nhiều ứng dụng, tự cộng tay và vẫn bị vượt ngân sách do chi phí phát sinh hoặc giá thay đổi].

## 3. Opportunity

Cơ hội là dùng AI để [augment: tự động tra cứu và tính toán tổ hợp chi phí (vé, ăn uống, di chuyển, vé tham quan) theo thời gian thực],
giúp user [biết ngay tổng chi tiêu dự kiến, nhận cảnh báo khi có nguy cơ vượt ngân sách và nhận gợi ý thay thế rẻ hơn],
trong khi vẫn kiểm soát [rủi ro bằng cách yêu cầu user xác nhận thay đổi quan trọng và hiển thị nguồn/giả định tính toán].

## 4. Chọn build slice (đề xuất)

Build slice đề xuất (demo 3–5 phút):

- Input: user nhập `điểm đến`, `số ngày`, và `tổng ngân sách` (hoặc chọn ngân sách theo ngày).
- AI action: tra cứu 3 nguồn giá (ví dụ: chỗ ở rẻ nhất, 1 option ăn uống bình dân, chi phí di chuyển tiêu biểu), tổng hợp thành "Tổng chi phí dự kiến cho 1 ngày" và cho cả chuyến.
- Output: hiển thị tổng, trạng thái ngân sách (OK / Near limit / Over), và 2 gợi ý giảm chi phí (thay chỗ ở / thay nhà hàng / thay phương tiện) kèm ước lượng tiết kiệm.

Đánh giá theo 5 câu hỏi:

- User cụ thể chưa? Có — `sinh viên/khách du lịch tự túc` trong bối cảnh lên kế hoạch trước chuyến đi.
- Task đủ hẹp? Có — tính toán tổng chi phí + 2 gợi ý là demo được trong 3–5 phút.
- AI decision rõ chưa? Có — AI tính tổng và đề xuất thay thế rõ ràng.
- Failure path rõ chưa? Có — nguồn giá không khớp / dữ liệu thiếu dẫn tới ước lượng sai; test bằng case ngân sách quá thấp.
- Có evidence không? Có — self-use table, phỏng vấn, competitor analysis.

## 5. Quyết định: giữ scope / giảm scope / đổi hướng

- Quyết định: Giữ domain nhưng giảm scope — chỉ làm flow "Tổng chi phí 1 ngày + cảnh báo + 2 gợi ý thay thế".
- Rủi ro & mitigation: nếu dữ liệu giá không đáng tin, chọn mô hình augmentation — AI chỉ gợi ý và yêu cầu user xác nhận trước khi áp dụng thay đổi; hiển thị nguồn giá và giả định (ví dụ: "giá khách sạn lấy từ nguồn X, cập nhật ngày Y").

## 6. Câu chốt cuối

Dựa trên evidence từ `evidence-pack.md`, nhóm sẽ build `prototype slice` tính toán "Tổng chi phí dự kiến 1 ngày" và cảnh báo ngân sách, cho `sinh viên/khách du lịch tự túc`, để giải quyết vấn đề "bị vượt ngân sách giữa chuyến" bằng cách AI `augment` công việc tra cứu và tính toán tổ hợp chi phí, và sẽ test failure path bằng case "ngân sách quá thấp / nguồn giá không khớp".

## 7. Backlog (không build trong Day 06)

- Đồng bộ giá theo thời gian thực với nhiều nguồn API và caching.
- Tự động đặt chỗ / thanh toán (transactional flows).
- Tích hợp lịch trình chi tiết cho toàn bộ hành trình nhiều ngày (multi-day optimizer).
- UI/UX polish, nhiều lựa chọn tùy chỉnh preference người dùng.

---

Nếu bạn muốn, tôi sẽ commit thay đổi này vào nhánh `feature/lamnd` hoặc chỉnh sửa theo yêu cầu thêm.
