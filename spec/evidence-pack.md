# Template — Evidence Pack

Nộp kèm thin SPEC cuối Day 05.

## 1. Nhóm và track

**Tên nhóm:** Budget Travel AI
**Track:** Travel and Hospitality  
**Product/app đã chọn:**  Trợ lý thiết kế Tour phù hợp với ngân sách người dùng  
**Build slice đang nghĩ:** Tính toán tổ hợp chi phí và gợi ý lịch trình, xử lý cảnh báo vượt ngân sách.

## 2. Self-use evidence

Nhóm tự dùng app/workflow và ghi lại điểm gãy.

| Observation | Screenshot/link | Path liên quan | Điều học được |
|---|---|---|---|
| App được hỏi yêu cầu xao nhãng nhưng vẫn có thể hỏi lại người dùng để xác nhận các thông tin cần thiết | ![Ảnh minh họa](images/1.png) | Happy | Cần xác nhận lại các thông tin chuyến đi như địa điểm đến, thông tin địa điểm xuất phát... |
| Khi ngân sách quá thấp so với yêu cầu tối thiểu. | ![Ảnh minh họa](images/4.png) | Correction | Cần xác nhận lại ngân sách chuyến đi và gợi ý lại lộ trình. |
| App đã yêu cầu xác nhận lại thông tin đầu vào trước khi bắt đầu lên lịch trình | ![Ảnh minh họa](images/2.png) ![Ảnh minh họa](images/3.png)| Correction | Cần xác nhận lại các thông tin trên đầu vào trước khi thực hiện tạo lịch trình. |
## 3. User / review / social evidence

Nguồn có thể là review App Store/Play, group, comment, phỏng vấn nhanh, hoặc nguồn public khác.

| Quote / review / observation | Nguồn | User là ai? | Pain/failure mode |
|---|---|---|---|
| "Đi du lịch cầm đúng 1 triệu/ngày mà cứ vừa ăn vừa lo thâm hụt, đến nơi thấy giá vé tăng là phải nhịn ăn trưa để bù vào." | Phỏng vấn nhanh sinh viên trường Đại học | Sinh viên, người trẻ đi du lịch tự túc | Chi phí thực tế tăng gây "cháy túi" giữa chuyến đi. Buộc phải cắt giảm trải nghiệm thiết yếu một cách vô lý. |
| "Nhiều khi tìm được quán ngon trên TikTok nhưng đến nơi tính tiền mới thấy đắt, lại phải ngồi bấm máy tính cộng lại từ đầu xem tối còn bao nhiêu tiền." | Group du lịch tự túc | Khách du lịch có ngân sách giới hạn | Phải làm toán thủ công liên tục, mất đi sự an tâm và thoải mái khi trải nghiệm chuyến đi. |
| "Đi du lịch tự túc thường bị vượt ngân sách vì phát sinh chi phí ăn uống và di chuyển." | Phỏng vấn nhanh 1 bạn sinh viên trong lớp | Sinh viên, du lịch tự túc | Khó kiểm soát tổng chi tiêu trong ngày và toàn bộ chuyến đi. |
## 4. Competitor / analog evidence

| App / mô hình tham khảo | Họ xử lý task này thế nào? | Pattern học được | Có áp dụng trong 1 ngày không? |
|---|---|---|---|
| Google Maps / Tripadvisor | Gợi ý địa điểm theo bộ lọc mức giá ($, $$, $$$) nhưng không tổng hợp chi phí toàn bộ lịch trình. | Chỉ lọc bề nổi thông tin, không thực hiện tính toán tổ hợp chi phí. | Có (Học tập phần dữ liệu địa điểm nhưng cải tiến bằng cách cộng dồn toán học). |
| Ứng dụng Quản lý chi tiêu (Money Lover) | Cho người dùng nhập số tiền đã tiêu để trừ dần vào tổng ngân sách. | Là công cụ ghi nhận sau khi sự đã rồi (Reactive), người dùng cần một công cụ lên kế hoạch trước (Proactive). | Có (Áp dụng tư duy đặt "vạch kẻ đỏ" giới hạn ngân sách nghiêm ngặt). |
| App Layla | Người dùng nhập điểm đến, số ngày, sở thích du lịch và ngân sách. AI tự động đề xuất lịch trình, hoạt động và nơi lưu trú phù hợp. | Kết hợp AI hội thoại với hệ thống gợi ý lịch trình cá nhân hóa. Người dùng mô tả nhu cầu bằng ngôn ngữ tự nhiên thay vì điền form phức tạp. | Có (Xây dựng chatbot nhập ngân sách và sở thích để sinh lịch trình cơ bản). |

## 5. Evidence -> Insight

```text
Evidence nổi bật nhất:
Người trẻ đi du lịch phải mở đồng thời 3-4 ứng dụng để vừa tìm quán, vừa check giá, vừa tự cộng thủ công chi phí vì sợ bị "cháy túi" giữa chừng do giá phương tiện di chuyển hay giá vé tham quan tăng đột biến.

Insight:
User không chỉ gặp [surface problem: thiếu thông tin địa điểm hay giá cả].
Thật ra họ cần [deeper need / decision support / trust / recovery: Sự an tâm tuyệt đối về mặt tài chính. Họ cần một "vạch kẻ đỏ" an toàn để tự do trải nghiệm mà không lo bị thâm hụt túi tiền cuối ngày].

Opportunity:
AI có thể giúp bằng cách [augment/automate hành động hẹp: Tự động tra cứu, tính toán tổ hợp chi phí (vé cửa, món ăn, di chuyển) theo thời gian thực và tự động đưa ra các mẹo cắt giảm chi phí thông minh khi vượt ngưỡng].