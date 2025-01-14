import os
import pandas as pd
import streamlit as st
from io import BytesIO

# Streamlit title and description
st.title("Folder Structure to Excel")
st.write("Generate an Excel table listing each folder's name and either the folder path or the path to a file inside the folder.")

# User input to select the main directory
main_dir = st.text_input("Enter the path to the main directory:", "")

# User input for custom column names
folder_column_name = st.text_input("Enter the name for the 'Folder Name' column:", "name of folder")
path_column_name = st.text_input("Enter the name for the 'Path' column:", "path")

# Checkbox to choose whether to write the path to a file inside the folder
write_file_path = st.checkbox("Write path to file inside the folder (instead of folder path)")


# Function to get folder info and paths to files or folder
def get_folder_info(main_directory, write_file_path):
    folder_data = []
    for root, dirs, _ in os.walk(main_directory):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            
            if write_file_path:
                # Find files in the folder
                files_in_folder = os.listdir(folder_path)
                if files_in_folder:  # Check if there are any files
                    # Get the first file in the folder (or any desired logic)
                    first_file_path = os.path.join(folder_path, files_in_folder[0])
                    folder_data.append({
                        folder_column_name: '_'.join(folder.split('_')[0:2]),
                        path_column_name: first_file_path  # Path to the first file
                    })
                else:
                    folder_data.append({
                        folder_column_name: '_'.join(folder.split('_')[0:2]),
                        path_column_name: "No files in folder"
                    })
            else:
                folder_data.append({
                    folder_column_name: '_'.join(folder.split('_')[0:2]),
                    path_column_name: folder_path  # Path to the folder
                })
    return folder_data

# Button to generate Excel file
if st.button("Generate Excel"):
    if os.path.isdir(main_dir):
        # Collect folder information
        folder_info = get_folder_info(main_dir, write_file_path)
        
        # Convert to DataFrame
        df = pd.DataFrame(folder_info)
        
        # Export to Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Folders")
        
        # Provide download button
        st.download_button(
            label="Download Excel file",
            data=output.getvalue(),
            file_name="folders_info.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Please enter a valid directory path.")
