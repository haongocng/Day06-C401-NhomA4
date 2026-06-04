# Template — Thin SPEC Cuối Day 05

Thin SPEC không phải PRD đầy đủ. Đây là bản cam kết đủ rõ để sáng Day 06 nhóm build ngay.

## 1. Track, product/app và user

**Track:** Travel & Hospitality
**Product/app thật:** Budget Travel Planner AI (Trợ lý thiết kế Tour phù hợp với ngân sách người dùng)
**User cụ thể:** Sinh viên, người trẻ đi du lịch tự túc với ngân sách giới hạn, muốn tối ưu chi phí nhưng vẫn có trải nghiệm đầy đủ.
**Nhóm có phải user thật không? Nếu không, khác ở đâu?**
Có. Nhóm phát triển cũng thuộc đối tượng sinh viên/người trẻ thường xuyên đi du lịch tự túc và gặp khó khăn trong việc cân đối ngân sách giữa ăn uống, tham quan và di chuyển.

## 2. Evidence summary

| Evidence                                                                         | Nguồn                              | User/pain nói lên điều gì?                              | SPEC phải đổi gì?                             |
| -------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| Người dùng mở đồng thời Google Maps, TikTok, Grab, blog review để lên lịch trình | Quan sát hành vi                   | Thông tin bị phân mảnh, phải tự tổng hợp thủ công       | AI cần gom dữ liệu và tính toán tự động       |
| Người dùng thường cộng tiền bằng tay để kiểm tra có vượt ngân sách không         | Phỏng vấn nhanh sinh viên          | Việc lập kế hoạch tài chính mất thời gian và dễ sai     | AI cần tự động tính tổng chi phí              |
| Chi phí thực tế có thể thay đổi do giá vé hoặc giá di chuyển                     | Trải nghiệm thực tế của người dùng | Người dùng thiếu khả năng dự đoán rủi ro vượt ngân sách | AI cần cảnh báo và đề xuất phương án thay thế |


## 3. Pain statement

```text
User là sinh viên hoặc người trẻ đi du lịch tự túc đang gặp khó khăn
ở bước lập lịch trình và phân bổ ngân sách trong ngày,
vì phải tự thu thập thông tin từ nhiều nguồn và tự tính toán chi phí,
dẫn tới nguy cơ vượt ngân sách hoặc phải cắt giảm trải nghiệm vào phút cuối.

Bằng chứng chính là việc người dùng thường mở nhiều ứng dụng cùng lúc
để vừa tìm địa điểm vừa tự cộng chi phí thủ công trước chuyến đi.
```

## 4. Build slice

```text
Cho sinh viên, nhóm bạn trẻ đi du lịch tự túc muốn thiết kế một ngày trải nghiệm
trọn vẹn với một hạn mức ngân sách cố định,

prototype sẽ dùng AI để tra cứu chi phí trung bình của các địa điểm
(ăn uống, tham quan, di chuyển) và tính toán tổ hợp chi phí nhằm đảm bảo
tổng chi tiêu không vượt quá ngân sách người dùng,

tạo ra bản phân bổ chi tiêu chi tiết theo từng hạng mục cùng các đề xuất
địa điểm phù hợp,

và xử lý failure mode bằng cách giữ nguyên các địa điểm bắt buộc,
hiển thị cảnh báo vượt ngân sách và đề xuất các phương án tiết kiệm chi phí
thay thế để bù trừ.
```

## 5. Auto/Aug decision

* [x] **Augmentation:** AI gợi ý/draft/phân loại, user quyết cuối.
* [ ] Conditional automation
* [ ] Automation

**Lý do chọn:**

Lịch trình du lịch mang tính cá nhân cao. AI chỉ nên đóng vai trò tư vấn và tính toán ngân sách, còn người dùng là người quyết định giữ hay thay đổi địa điểm.

**Human role:** Decider


## 6. Four paths

| Path           | Prototype phải thể hiện gì?                                                    |
| -------------- | ------------------------------------------------------------------------------ |
| Happy          | Tổng chi phí nằm trong ngân sách, AI tạo lịch trình hoàn chỉnh                 |
| Low-confidence | Thiếu dữ liệu giá một số địa điểm, AI hiển thị giá ước lượng và mức độ tin cậy |
| Failure        | Tổng chi phí vượt ngân sách do địa điểm bắt buộc quá đắt                       |
| Correction     | AI đề xuất phương án tiết kiệm để đưa tổng chi phí về gần ngân sách mục tiêu   |


## 7. Failure mode nguy hiểm nhất

```text
Nếu user chọn nhiều địa điểm bắt buộc có chi phí cao,
AI có thể tạo ra lịch trình vượt ngân sách đáng kể.

Hậu quả là người dùng hiểu nhầm rằng kế hoạch đó khả thi
và gặp khó khăn tài chính trong chuyến đi.

Prototype sẽ xử lý bằng cách:
- Không tự động xóa địa điểm.
- Hiển thị cảnh báo vượt ngân sách rõ ràng.
- Tính toán số tiền vượt mức.
- Đề xuất các lựa chọn tiết kiệm chi phí thay thế.
- Yêu cầu người dùng xác nhận trước khi tiếp tục.

Owner kiểm thử path này là: Thành viên phụ trách Testing.
```

## 8. Owner plan cho sáng Day 06

| Thành viên | Việc phụ trách      | Bằng chứng cần có trong repo               |
| ---------- | ------------------- | ------------------------------------------ |
| Pham Thanh Hang + Ngo Duc Lam + Nguyen Ngoc Hao   | Research / Evidence | File tổng hợp pain point và khảo sát các app hiện tại |
| Nguyen Ngoc Hao   | SPEC                | Thin SPEC hoàn chỉnh                       |
| Nguyen Ngoc Hao + Pham Thanh Hang + Ngo Duc Lam   | Prototype           | Source code AI Planner                     |
| Pham Thanh Hang   | Test / Failure Path | Test cases và ảnh chụp kết quả             |
| Ngo Duc Lam   | Demo Script / Repo  | Kịch bản demo và README                    |
