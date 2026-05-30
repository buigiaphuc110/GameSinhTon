Thành viên thực hiện
Sinh viên: Bùi Gia Phúc
Mã số sinh viên (MSV): 25112100
Môn học: Lập trình hướng đối tượng (OOP)
Trường: Đại học Việt Nhật - ĐHQGHN (VJU)
-Sơ đồ Lớp UML Hệ thống (Class Diagram):  
<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/f753ba02-b8f2-4d46-8872-e27b04766399" />
-Kiến trúc Phần mềm & Tư duy Hướng đối tượng (OOP):
1. Kiến trúc Phần mềm (Software Architecture)
Dự án của bạn đi theo Kiến trúc Vòng lặp Game (Game Loop Architecture) kết hợp với Kiến trúc dựa trên Mô-đun (Modular Architecture). Thay vì nhồi nhét mọi thứ vào một tệp duy nhất, hệ thống đã được chia tách logic khá rõ ràng:

Tính Mô-đun (Modularization): Mã nguồn được chia thành nhiều tệp (module) theo nguyên tắc Trách nhiệm Đơn lẻ (Single Responsibility Principle - SRP) ở mức cơ bản.

main.py: Đóng vai trò là tệp Entry Point (điểm khởi chạy). Nó quản lý vòng lặp sự kiện chính (Game Loop), tải tài nguyên (Assets) và điều hướng các trạng thái UI (Menu chính, Chọn Vũ khí, Chọn Màn, Bảng Điểm).

gameplay.py: Chứa lõi logic (Core Logic) của trò chơi như sinh quái, hệ thống va chạm, vòng lặp chiến đấu, và vẽ thanh máu.

player.py: Đóng gói toàn bộ các trạng thái và chỉ số thuộc về người chơi.

weapon.py & special.py: Xử lý riêng biệt hệ thống hạt (Particles), hiệu ứng nổ và các kỹ năng của vũ khí.

score.py: Quản lý việc lưu trữ và đọc/ghi dữ liệu điểm số ra file độc lập.

Quản lý Trạng thái (State Management): Kiến trúc của bạn ngầm định sử dụng State Machine (Máy trạng thái) thông qua các biến điều hướng hoặc vòng lặp while running cục bộ trong từng màn hình (như ở score_menu hoặc weapon_selection_menu). Các hàm hiệu ứng chuyển cảnh như transition_fade_in giúp cô lập việc chuyển đổi giữa UI Menu và Gameplay.

2. Tư duy Hướng đối tượng (OOP)
Code của bạn áp dụng tư duy Hướng đối tượng rất rõ nét, mô phỏng các thực thể trong game thành các Object (đối tượng) tương tác với nhau:

Tính Đóng gói (Encapsulation):

Bảo vệ dữ liệu thông minh: Lớp Player sử dụng hàm Decorator @property và @health.setter để tạo ra một "màng lọc bảo vệ máu thông minh". Thay vì để các module khác trừ máu trực tiếp (player.health -= damage), bạn đã đóng gói logic này lại: khi máu giảm (nhận sát thương > 4), hệ thống sẽ tự động kích hoạt khung thời gian bất tử (I-frames). Điều này giấu đi logic phức tạp bên trong đối tượng Player.

Đóng gói File IO: Lớp ScoreManager tự đóng gói biến high_score, top_scores cùng các hàm đọc/ghi save_high_score() và load_high_score(). Các phần khác của game chỉ cần gọi add_points(points) mà không cần biết điểm được ghi vào file text như thế nào.

Tính Đa hình (Polymorphism) thông qua Duck Typing:

Python không sử dụng Interfaces như Java, nhưng code của bạn có Tính đa hình rất tốt qua các hàm tiêu chuẩn. Các lớp như PoisonBullet, ChainProjectile, CannonballProjectile, DangerExplosion hay LavaPool đều được thiết kế để chia sẻ các phương thức cốt lõi như update() và draw().

Nhờ vậy, tại vòng lặp chính của gameplay, bạn chỉ cần duyệt qua danh sách các thực thể (entities) và gọi entity.update() hoặc entity.draw() mà không cần quan tâm thực thể đó là quả cầu độc, dung nham hay tên lửa.

Sự Trừu tượng hóa (Abstraction):

Class WeaponExplosion nhóm chung logic xử lý hạt (particles) cho nhiều loại vũ khí khác nhau (kiếm, rìu, súng, mỏ lết) vào chung một khung. Class ParticleManager trừu tượng hóa quá trình tạo khói, tạo vụ nổ, giúp việc tái sử dụng hiệu ứng hình ảnh ở các sự kiện khác nhau trở nên cực kỳ tinh gọn.
