import glob
import os
import pandas as pd
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog

def select_folder():
    root = tk.Tk()
    root.withdraw()  
    folder_path = filedialog.askdirectory(title="Chọn thư mục")
    return folder_path


selected_folder = select_folder()
if selected_folder:
    print(f"Đường dẫn thư mục đã chọn: {selected_folder}")
else:
    print("Không có thư mục nào được chọn.")

input_folder = selected_folder  
csv_files = glob.glob(f"{input_folder}/**/*.csv", recursive=True)

folders = {}
error_data = []                                                  
matching_files = []  # List of files contain NGVI10 or NGVI11
location_data = {}   
file_times = []  

for file in csv_files:
    folder = os.path.relpath(os.path.dirname(file), input_folder)
    filename = os.path.basename(file)

    if folder not in folders:
        folders[folder] = []
    
    folders[folder].append(filename)

for folder, files in folders.items():
    for file in files:
        file_path = os.path.join(input_folder, folder, file)  

        if "NG" in file:  
            try:
                if not os.path.exists(file_path):
                    print(f"❌ File không tồn tại: {file_path}")
                    continue

                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines='skip', index_col=False)
                
                
                contains_ngv = df.astype(str).apply(lambda x: x.str.contains("NGVI10|NGVI11", na=False)).any().any()

                if contains_ngv:
                    matching_files.append(file)  
                    
                    if "Location" in df.columns:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        file_hour = file_time.strftime("%H") #get hour
                        # split into two type of ngvi
                        ngvi10_count = df[df.astype(str).apply(lambda x: x.str.contains("NGVI10", na=False)).any(axis=1)]
                        ngvi11_count = df[df.astype(str).apply(lambda x: x.str.contains("NGVI11", na=False)).any(axis=1)]
                        
                        # save in to list
                        error_data.append({"Hour": int(file_hour), "NGVI10_Count": len(ngvi10_count), "NGVI11_Count": len(ngvi11_count)})
                    

                        locations = []  # Danh sách location kèm loại NGVI

                        if not ngvi10_count.empty:
                            locations.extend([f"{loc} (NGVI10)" for loc in ngvi10_count["Location"].dropna().unique()])

                        if not ngvi11_count.empty:
                            locations.extend([f"{loc} (NGVI11)" for loc in ngvi11_count["Location"].dropna().unique()])

                        location_data[file] = locations
                    

            except Exception as e:
                print(f"❌ Lỗi khi đọc {file_path}: {e}")

#convert to dataframe
error_df = pd.DataFrame(error_data)
hourly_errors = error_df.groupby("Hour").sum().reset_index()
# wide format to long format
hourly_errors_long = pd.melt(
    hourly_errors,
    id_vars=["Hour"],
    value_vars=["NGVI10_Count", "NGVI11_Count"],
    var_name="Error_Type",
    value_name="Count"
)

def get_time(file_path):
    """Trả về thời gian file được lưu lần cuối"""
    if not os.path.exists(file_path):
        return "❌ File không tồn tại"
    
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')



for folder, files in folders.items():
    for f in files:
        file_path = os.path.join(input_folder, folder, f)  # Đúng đường dẫn
        if f in matching_files:
            file_time = get_time(file_path)
            if file_time != "❌ File không tồn tại":
                file_times.append((f, file_time, file_path))


sorted_files = sorted(file_times, key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S"), reverse=True)
print("\n📂 Danh sách file chứa NGVI10 hoặc NGVI11 (sắp xếp theo thời gian giảm dần):")

for f, time, path in sorted_files:
    print(f"  ├── {f[:-18]} | 🕒 {time}")
    
    if f in location_data:
        print(f"      📍 Location: {', '.join(location_data[f])}")

# save output

output_directory = r"C:\Users\saran\ME_log"
output_file_path = os.path.join(output_directory, "ME_log.txt")

# Đảm bảo thư mục tồn tại, nếu không thì tạo mới
os.makedirs(output_directory, exist_ok=True)
with open(output_file_path, "w", encoding="utf-8") as file:
    file.write("📂 Danh sách file chứa NGVI10 hoặc NGVI11 (sắp xếp theo thời gian giảm dần):\n")

    for f, time, path in sorted_files:
        file.write(f"  ├── {f[:-18]} | 🕒 {time}\n")
        
        if f in location_data:
            file.write(f"      📍 Location: {', '.join(location_data[f])}\n")

print(f"✅ Dữ liệu đã được lưu vào file: {output_file_path}")


#plot diagram

sns.set(style="whitegrid")
plt.figure(figsize=(14, 7))

sns.barplot(data=hourly_errors_long, x="Hour", y="Count", hue="Error_Type", palette={"NGVI10_Count": "blue", "NGVI11_Count": "red"})


for p in plt.gca().patches:
    height = p.get_height()
    if height > 0:
        plt.gca().text(
            p.get_x() + p.get_width() / 2,  
            height + 0.5,  
            f"{int(height)}",  
            ha="center",  
            va="bottom",  
            fontsize=10
        )


plt.xlabel("Giờ trong ngày", fontsize=12)
plt.ylabel("Số lượng lỗi", fontsize=12)
plt.title("Biểu đồ số lượng NGVI10 & NGVI11 theo từng giờ", fontsize=14)
plt.xticks(range(0, 24)) 
plt.legend(title="Loại lỗi")
plt.show()