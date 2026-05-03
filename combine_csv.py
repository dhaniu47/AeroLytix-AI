import pandas as pd
import os

folder_path = r"C:\Users\dhane\Downloads\archive"

df_list = []

for root, dirs, files in os.walk(folder_path):
    for file in files:
        if file.endswith('.csv'):
            file_path = os.path.join(root, file)
            print("Reading:", file_path)
            try:
                data = pd.read_csv(file_path, encoding='latin1')
                df_list.append(data)
            except:
                print("Skipped:", file_path)

final_df = pd.concat(df_list, ignore_index=True)

final_df.to_csv("combined_data.csv", index=False)

print("✅ DONE - Combined file created!")