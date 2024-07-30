import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # Cần thư viện Pillow để xử lý hình ảnh
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import threading

def show_help():
    help_text = (
        "Hướng dẫn sử dụng ứng dụng:\n\n"
        "1. **Chọn chế độ tải**: Chọn 'Tải hàng loạt' nếu bạn muốn tải ảnh từ nhiều chương.\n"
        "   Chọn 'Tải từng chap' nếu bạn muốn tải ảnh từ từng chương cụ thể.\n\n"
        "2. **Nhập URL truyện**: Nhập URL của trang web chứa truyện mà bạn muốn tải ảnh.\n\n"
        "3. **Chọn thư mục lưu trữ**: Chọn thư mục nơi bạn muốn lưu trữ các ảnh tải về.\n\n"
        "4. **Nếu bạn chọn 'Tải hàng loạt'**:\n"
        "   - Nhập số chương bắt đầu và số chương kết thúc để tải ảnh từ các chương đó.\n\n"
        "5. **Nếu bạn chọn 'Tải từng chap'**:\n"
        "   - Chỉ cần nhập URL truyện và thư mục lưu trữ, và ứng dụng sẽ tải ảnh từ chương đó.\n\n"
        "6. **Nhấn 'Bắt đầu tải'** để bắt đầu quá trình tải ảnh.\n\n"
        "7. **Nhấn 'Ngưng tải'** nếu bạn muốn dừng quá trình tải ảnh.\n\n"
        "Liên hệ gmail jstomvn99@gmail.com nếu bạn gặp lỗi hay câu hỏi trong quá trình sử dụng \n\n"
        "Chúc bạn tải truyện vui vẻ!"
    )
    messagebox.showinfo("Hướng Dẫn Sử Dụng", help_text)

def download_images_from_chapter(url, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Không thể truy cập trang web. Mã trạng thái: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    img_tags = soup.find_all('img')
    png_count = 0
    
    for idx, img in enumerate(img_tags):
        if stop_flag.is_set():
            print("Tải ảnh đã bị ngưng.")
            status_label.config(text="Đã ngưng tải.")
            return

        img_url = img.get('src')
        
        if not img_url:
            continue
        
        img_url = urljoin(url, img_url)
        
        img_filename = os.path.basename(urlparse(img_url).path)
        file_extension = img_filename.lower().split('.')[-1]

        if file_extension not in ['jpg', 'jpeg', 'png']:
            continue
        
        if file_extension == 'png':
            if png_count >= 5:
                continue
            png_count += 1
        
        img_path = os.path.join(download_folder, f"{idx+1:03d}_{img_filename}")

        retry_count = 0
        while True:
            try:
                img_data = requests.get(img_url).content
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                print(f"Đã tải {img_url} về {img_path} sau {retry_count} lần thử")
                break
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"Không thể tải {img_url}. Lỗi: {e}. Thử lại lần thứ {retry_count}...")
                
                if retry_count >= 50:
                    print("Đã thử 50 lần nhưng không tải được ảnh. Bỏ qua ảnh này.")
                    break

    status_label.config(text="Tải ảnh hoàn tất!")
    root.after(5000, lambda: status_label.config(text=""))  # Xóa thông báo sau 5 giây

def download_images_from_website(url, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve the website. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    img_tags = soup.find_all('img')
    
    for idx, img in enumerate(img_tags):
        if stop_flag.is_set():
            print("Tải ảnh đã bị ngưng.")
            status_label.config(text="Đã ngưng tải.")
            return

        img_url = img.get('src')
        
        if not img_url:
            continue
        
        img_url = urljoin(url, img_url)
        
        img_filename = os.path.basename(urlparse(img_url).path)
        
        img_path = os.path.join(download_folder, f"{idx+1:03d}_{img_filename}")
        
        try:
            img_data = requests.get(img_url).content
            with open(img_path, 'wb') as img_file:
                img_file.write(img_data)
            print(f"Downloaded {img_url} to {img_path}")
        except Exception as e:
            print(f"Failed to download {img_url}. Error: {e}")

    status_label.config(text="Tải ảnh hoàn tất!")
    root.after(5000, lambda: status_label.config(text=""))  # Xóa thông báo sau 5 giây

def get_chapter_links(mother_url):
    response = requests.get(mother_url)
    if response.status_code != 200:
        print(f"Không thể truy cập trang web mẹ. Mã trạng thái: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    chapter_links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if 'chapter' in href:
            chapter_links.append(urljoin(mother_url, href))
    
    return chapter_links

def extract_chapter_number(url):
    match = re.search(r'chapter-(\d+)', url)
    if match:
        return int(match.group(1))
    return None

def start_download():
    stop_flag.clear()

    mother_url = url_entry.get()
    parent_download_folder = folder_entry.get()
    start_chapter = int(start_chapter_entry.get())
    end_chapter = int(end_chapter_entry.get())

    chapter_links = get_chapter_links(mother_url)
    chapter_links.reverse()

    selected_chapters = []
    for chapter_url in chapter_links:
        chapter_number = extract_chapter_number(chapter_url)
        if chapter_number and start_chapter <= chapter_number <= end_chapter:
            selected_chapters.append((chapter_number, chapter_url))

    for chapter_number, chapter_url in selected_chapters:
        if stop_flag.is_set():
            print("Tải ảnh đã bị ngưng.")
            status_label.config(text="Đã ngưng tải.")
            break
        chapter_folder = os.path.join(parent_download_folder, f"Chap {chapter_number}")
        print(f"Đang tải ảnh từ {chapter_url} vào thư mục {chapter_folder}")
        status_label.config(text=f"Đang tải chap {chapter_number}...")
        download_images_from_chapter(chapter_url, chapter_folder)
        print("-" * 50)

    if not stop_flag.is_set():
        status_label.config(text="Tải ảnh hoàn tất!")
        messagebox.showinfo("Hoàn thành", "Tải ảnh hoàn tất!")
        root.after(5000, lambda: status_label.config(text=""))
    else:
        messagebox.showinfo("Dừng", "Tải ảnh đã bị ngưng.")

def start_download_single():
    stop_flag.clear()

    website_url = url_entry.get()
    parent_download_folder = folder_entry.get()
    
    status_label.config(text="Đang tải ảnh...")
    download_images_from_website(website_url, parent_download_folder)

    if not stop_flag.is_set():
        status_label.config(text="Tải ảnh hoàn tất!")
        messagebox.showinfo("Hoàn thành", "Tải ảnh hoàn tất!")
        root.after(5000, lambda: status_label.config(text=""))
    else:
        messagebox.showinfo("Dừng", "Tải ảnh đã bị ngưng.")

def browse_folder():
    folder_selected = filedialog.askdirectory()
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, folder_selected)

def stop_download():
    stop_flag.set()
    status_label.config(text="Đã ngưng tải.")

def start_thread():
    if download_mode.get() == "batch":
        download_thread = threading.Thread(target=start_download)
    else:
        download_thread = threading.Thread(target=start_download_single)
    download_thread.start()

def update_ui(*args):
    if download_mode.get() == "batch":
        start_chapter_label.grid()
        start_chapter_entry.grid()
        end_chapter_label.grid()
        end_chapter_entry.grid()
    else:
        start_chapter_label.grid_remove()
        start_chapter_entry.grid_remove()
        end_chapter_label.grid_remove()
        end_chapter_entry.grid_remove()

root = tk.Tk()
root.title("Manga Downloaded")

# Thay đổi biểu tượng cửa sổ
icon_path = "D:\\Nam Trung\\Manga\\tyrannosaurus-rex.ico"  # Hoặc icon.ico
root.iconbitmap(icon_path)

download_mode = tk.StringVar(value="batch")
download_mode.trace_add("write", update_ui)

menu_frame = tk.Frame(root)
menu_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

tk.Radiobutton(menu_frame, text="Tải hàng loạt", variable=download_mode, value="batch").pack(side=tk.LEFT)
tk.Radiobutton(menu_frame, text="Tải từng chap", variable=download_mode, value="single").pack(side=tk.LEFT)

tk.Label(root, text="Url Truyện:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Thư mục lưu trữ:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Chọn thư mục", command=browse_folder).grid(row=2, column=2, padx=5, pady=5)

start_chapter_label = tk.Label(root, text="Chap bắt đầu:")
start_chapter_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
start_chapter_entry = tk.Entry(root, width=10)
start_chapter_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')

end_chapter_label = tk.Label(root, text="Chap kết thúc:")
end_chapter_label.grid(row=4, column=0, padx=10, pady=5, sticky='e')
end_chapter_entry = tk.Entry(root, width=10)
end_chapter_entry.grid(row=4, column=1, padx=5, pady=5, sticky='w')

# Tạo khung cho các nút chính
button_frame = tk.Frame(root)
button_frame.grid(row=5, column=0, columnspan=4, pady=10)

tk.Button(button_frame, text="Bắt đầu tải", command=start_thread).pack(side=tk.LEFT, padx=10)
tk.Button(button_frame, text="Ngưng tải", command=stop_download).pack(side=tk.LEFT, padx=10)

# Nút hướng dẫn xuống cuối màn hình
tk.Button(root, text="Hướng dẫn", command=show_help).grid(row=6, column=2, columnspan=4, pady=10)

status_label = tk.Label(root, text="")
status_label.grid(row=7, column=0, columnspan=4, padx=10, pady=5)

# Thêm label phiên bản
version_label = tk.Label(root, text="Ver1", anchor='w')
version_label.grid(row=8, column=0, padx=10, pady=5, sticky='w')



update_ui()

root.mainloop()
