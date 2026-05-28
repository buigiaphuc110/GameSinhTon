import os
import sys

print("-" * 50)
print("ĐANG BẺ KHÓA VÀ ÉP HỆ THỐNG CÀI PYGAME...")
print("-" * 50)

# Thêm lệnh --break-system-packages để bỏ qua ổ khóa bảo vệ của uv
os.system(f'"{sys.executable}" -m pip install pygame --break-system-packages')

print("-" * 50)
print("NẾU THẤY CHỮ 'Successfully installed' THÌ OK RỒI ĐÓ!")
print("-" * 50)