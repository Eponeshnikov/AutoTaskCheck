# Import necessary libraries
import ast
import streamlit as st
import warnings
import pandas as pd
from dataloader import DataLoader
from check import Check


# Ignore warnings to prevent clutter
warnings.filterwarnings("ignore")


# ===========================
# User Input Functions
# ===========================

# Function to display and collect optional parameters specified by the user
def display_optional_params():
    with st.expander('Optional parameters'):
        for param in dataloader.optional_params:
            user_input_param = dataloader.user_inputs[param]

            # Collect user input for optional parameters
            new_input_param = st.text_input(f'Enter the value for **{param}** (optional)', user_input_param)

            # Convert input to appropriate data types if needed
            if param in ('non-questions_columns', 'penalty_params', 'eval_formula'):
                new_input_param = ast.literal_eval(new_input_param)

            if param in ('force_download', 'take_first_submission') and isinstance(new_input_param, str):
                # Convert 'true' or 'false' strings to boolean values
                new_input_param = new_input_param.lower() == 'true'

            # Update user inputs with the new value
            dataloader.user_inputs[param] = new_input_param


# Function for changing columns name to prettier variant
def change_col_names():
    return dataloader.change_col_names()


# ===========================
# Checking Functions
# ===========================

# Function to perform checking on data (cached for performance)
@st.cache_data
def perform_checking(data, sub, usr):
    # Initialize the checker and perform checks
    checker = Check(data, sub, usr)
    checker.check_submissions()
    return checker.result


# ===========================
# Streamlit Configuration and Title
# ===========================

# Set Streamlit page configuration and title
st.set_page_config(layout="wide", page_title="AutoChecker", page_icon="📈")
st.title('Auto Checker')

# ===========================
# File Upload and Validation
# ===========================

# Load files - Config and Submissions
col1, col2 = st.columns(2)
with col1:
    config_file = st.file_uploader('Upload config file', type=['yaml', 'yml'])
with col2:
    submissions_file = st.file_uploader('Upload submissions file', type='xlsx')

# Check if both files are uploaded
if not config_file or not submissions_file:
    st.warning('Please upload both config and submissions files')
    st.stop()

# ===========================
# Data Loading
# ===========================

# Load data
dataloader = DataLoader(config_file, submissions_file)

# Get user inputs for 'name' and 'id' columns
col1, col2 = st.columns(2)
with col1:
    dataloader.user_inputs['name'] = st.text_input('Enter the **name** column (required)',
                                                   dataloader.system_info.get('name', ''))
with col2:
    dataloader.user_inputs['id'] = st.text_input('Enter the **id** column (required)',
                                                 dataloader.system_info.get('id', ''))
config = dataloader.config
submissions = dataloader.submissions

# ===========================
# Optional Parameters
# ===========================

# Set optional parameters
col1, col2 = st.columns(2)
with col1:
    # Collect and display optional parameters
    dataloader.collect_optional_params()
    display_optional_params()

with col2:
    is_matching_list = st.checkbox('Use matching list', value=True)

    with st.expander('Upload matching list file', expanded=True):
        list_id = st.file_uploader('Upload matching list file', type='xlsx', label_visibility='hidden')

    if list_id is not None and is_matching_list:
        dataloader.match_list_file = list_id
        dataloader.match_list = dataloader.load_match_list()

# ===========================
# Question Processing
# ===========================

# Process questions
dataloader.process_questions()
questions_data_df = dataloader.questions_data_df

# Display questions
questions_alias = questions_data_df.T
with st.expander('Questions for checking', expanded=True):
    # Allow the user to edit the questions
    questions_data_df = st.data_editor(
        questions_alias,
        column_config={
            "metadata": st.column_config.ListColumn(
                "metadata",
                help="metadata isn't editable, edit in config file and re-upload"
            )
        }
    )
questions_data_df = questions_data_df.T
dataloader.questions_data_df = questions_data_df
# ===========================
# Submissions and Results
# ===========================

# Check submissions
st.header('Submissions')
# Perform checking on submissions
st.dataframe(submissions)
result = perform_checking(questions_data_df, submissions, dataloader.user_inputs)
dataloader.results = result
result = change_col_names()
st.header('Results')
show_button = st.checkbox('Show as table')
if show_button:
    st.dataframe(result)
else:
    st.write(result.to_html(show_dimensions=True), unsafe_allow_html=True)
# Add a button to write results
cols = st.columns(8)
with cols[2]:
    save_checkbox = st.checkbox('Write without new results')

with cols[0]:
    st.button(label="Write results",
              on_click=lambda: dataloader.write_results(save_only_match=save_checkbox),
              disabled=list_id is None or not is_matching_list)

with cols[1]:
    st.button(label="Write short results",
              on_click=lambda: dataloader.write_results(short=True, save_only_match=save_checkbox),
              disabled=list_id is None or not is_matching_list)
