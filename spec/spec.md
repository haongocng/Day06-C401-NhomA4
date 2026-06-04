# Spec sản phẩm

Hãy hình dung SPEC như một lập luận, chứ không phải một danh sách tính năng. Nó cần trả lời rõ bốn câu hỏi: sản phẩm giải vấn đề gì và cho ai, AI tham gia quyết định điều gì, chuyện gì xảy ra khi AI trả lời sai, và những nhận định của nhóm dựa trên bằng chứng nào.

## 1. Bằng chứng

| Evidence                                                                         | Nguồn                              | User/pain nói lên điều gì?                              | SPEC phải đổi gì?                             |
| -------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| Người dùng mở đồng thời Google Maps, TikTok, Grab, blog review để lên lịch trình | Quan sát hành vi                   | Thông tin bị phân mảnh, phải tự tổng hợp thủ công       | AI cần gom dữ liệu và tính toán tự động       |
| Người dùng thường cộng tiền bằng tay để kiểm tra có vượt ngân sách không         | Phỏng vấn nhanh sinh viên          | Việc lập kế hoạch tài chính mất thời gian và dễ sai     | AI cần tự động tính tổng chi phí              |
| Chi phí thực tế có thể thay đổi do giá vé hoặc giá di chuyển                     | Trải nghiệm thực tế của người dùng | Người dùng thiếu khả năng dự đoán rủi ro vượt ngân sách | AI cần cảnh báo và đề xuất phương án thay thế |

## 2. Lát cắt để build

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

# 3. AI Product Canvas

| Ô                              | Nội dung                                                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Value — Giá trị**            | Dành cho sinh viên và người trẻ du lịch tự túc. AI giúp tạo lịch trình phù hợp với ngân sách, phân bổ chi phí và đề xuất phương án tối ưu khi có nguy cơ vượt ngân sách.       |
| **Trust — Niềm tin**           | Người dùng có thể kiểm tra chi phí dự kiến, chỉnh sửa yêu cầu và xem so sánh Before/After. AI không tự động xóa địa điểm bắt buộc mà luôn hiển thị cảnh báo và gợi ý thay thế. |
| **Feasibility — Tính khả thi** | MVP chỉ cần 1–2 lượt gọi Gemini API để tạo lịch trình. Dữ liệu gồm giá vé, chi phí ăn uống và di chuyển. Rủi ro lớn nhất là dữ liệu giá lỗi thời.                              |
| **Tín hiệu học**               | Hệ thống ghi nhận các chỉnh sửa của người dùng (thêm/xóa địa điểm, tăng giảm ngân sách) để cải thiện chất lượng gợi ý và tối ưu hóa lịch trình trong tương lai.                |

# 4. Tăng năng lực hay tự động hóa

**Lựa chọn:** Tăng năng lực (Augment)

AI hỗ trợ lập lịch trình, ước tính chi phí và đề xuất phương án tối ưu ngân sách. Người dùng là người quyết định cuối cùng.

**Con người giữ quyền quyết định**

* Chọn hoặc từ chối lịch trình.
* Chỉnh sửa ngân sách và địa điểm.
* Chấp nhận hoặc bỏ qua các gợi ý của AI.

**Lý do**
Chi phí du lịch liên quan trực tiếp đến tiền bạc. Nếu AI tính toán sai, người dùng vẫn có thể dễ dàng kiểm tra, chỉnh sửa hoặc hoàn tác trước khi thực hiện kế hoạch.

# 5. Bốn đường đi của trải nghiệm

| Đường đi                               | Cách xử lý                                                                                                      |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Đường thuận (Happy Path)**           | AI tạo lịch trình phù hợp ngân sách và hiển thị phân bổ chi phí chi tiết. Người dùng có thể sử dụng ngay.       |
| **Khi AI không chắc (Low Confidence)** | AI yêu cầu bổ sung thông tin như ngân sách, địa điểm hoặc sở thích trước khi tạo lịch trình.                    |
| **Khi AI sai (Failure)**               | AI cảnh báo khi lịch trình vượt ngân sách, hiển thị số tiền vượt và đề xuất các phương án tiết kiệm.            |
| **Khi người dùng sửa (Correction)**    | Người dùng chỉnh sửa ngân sách hoặc địa điểm. AI tính toán lại và hiển thị sự khác biệt trước/sau khi thay đổi. |


## 6. Những kiểu lỗi đáng lo nhất

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

## 7. Kế hoạch kiểm thử và bằng chứng demo
 - file excel Test plan
 - file pdf demo-slides

## 8. Phân công

### Ngô Đắc Lãm (Mã học viên: 2A202600655)

**Phụ trách kiểm thử Sản phẩm & Báo cáo**

* Viết document, update các file readme
* Tạo các test-case kiểm thử và kiểm thử trải nghiệm người dùng 
* Đánh giá chất lượng câu trả lời của AI và đề xuất cải tiến.
* Trình bày cách hoạt động của AI và chiến lược prompt trong buổi demo.
* Viết báo cáo nhóm và chuẩn bị kịch bản thuyết trình.

### Phạm Thanh Hằng (Mã học viên: 2A202600593)

**Phụ trách Giao diện người dùng**

* Xác định ý tưởng bài toán và phạm vi dự án.
* Tạo data mockup ban đầu
* Vẽ workflow của dự án
* Thiết kế, xây dựng và chỉnh sửa giao diện sản phẩm 

### Nguyễn Ngọc Hảo (Mã học viên: 2A202600903)

**Phụ trách Backend, Quản lý mã nguồn & Báo cáo**

* Xây dựng luồng xử lý nghiệp vụ và tích hợp AI.
* Quản lý repository GitHub, phân chia và hợp nhất mã nguồn.
* Thiết kế, thử nghiệm và tối ưu các prompt.
* Trình bày kiến trúc hệ thống và quá trình phát triển sản phẩm.
* Thực hiện phần demo luồng sử dụng của người dùng.