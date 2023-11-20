import yaml
import os
import pandas as pd
import re


class DataLoader:
    def __init__(self, config_file, submissions_file):
        """
        Initialize a DataLoader instance with configuration and submissions files.

        Args: config_file (str or file-like object): The path to the configuration file in YAML format or a file-like
        object. submissions_file (str or file-like object): The path to the submissions file in Excel format or a
        file-like object.
        """
        self.questions_data_df = None
        self.results = None
        self.match_list = None
        self.match_list_file = None
        self.config_file = config_file
        self.submissions_file = submissions_file
        self.submissions = self.load_submissions()
        self.config = self.load_config()
        self.system_info = self.config.get('system_info', {})
        self.optional_params = [param for param in self.system_info.keys() if param not in ['id', 'name']]
        self.user_inputs = None
        self.collect_optional_params()
        self.filter_submissions()

    def change_col_names(self):
        ren_col = {i: f"{i} ({int(self.questions_data_df[i]['Weight'] * 100)})" for i in
                   self.questions_data_df.columns}
        ren_col['total'] = 'Total (%)'
        ren_col['penalty_coefficient'] = 'Penalty coefficient'
        self.results = self.results.rename(columns=ren_col)
        return self.results

    def merge_match_res(self, write_mode='outer'):
        if self.match_list is not None and self.results is not None:
            if isinstance(self.match_list.columns[0], str):
                new_col_match_list = pd.MultiIndex.from_product([['Info'], self.match_list.columns])
                match_list = self.match_list.copy()
                match_list.columns = new_col_match_list
            elif isinstance(self.match_list.columns[0], tuple):
                match_list = self.match_list.copy()
            else:
                raise Exception(f"Unknown format of columns {type(self.match_list.columns)}")
            merged_df = match_list.merge(
                self.results, left_index=True, right_index=True, how=write_mode)
            return merged_df

    def write_results(self, short=False, save_only_match=False, filename=None, write_mode='outer'):
        if save_only_match:
            merged_df = self.match_list
        else:
            merged_df = self.merge_match_res(write_mode)
        if isinstance(self.match_list_file, str):
            match_list_file_name = self.match_list_file
        else:
            match_list_file_name = self.match_list_file.name
        file_name, file_ext = os.path.splitext(match_list_file_name)
        file_name = file_name if filename is None else filename
        if short:
            info_columns = merged_df[['Info']]
            total_columns = merged_df.filter(like='Total (%)')
            merged_df = pd.concat([info_columns, total_columns], axis=1)
            merged_df.columns = pd.MultiIndex.from_tuples(merged_df.columns)
            if '_short' not in file_name:
                file_name += '_short'
        merged_df.to_excel(f'{file_name}{file_ext}')

    def load_config(self):
        """
        Load the configuration from the provided YAML file.

        Returns:
            dict: A dictionary containing the configuration data.
        """
        if isinstance(self.config_file, str):
            config_file_name = self.config_file
        else:
            config_file_name = self.config_file.name
        file_name, file_ext = os.path.splitext(config_file_name)
        config = None
        if file_ext == '.yml':
            config = yaml.safe_load(self.config_file)
        return config

    def load_submissions(self):
        """
        Load the submissions data from the provided Excel file.

        Returns:
            pandas.DataFrame: A DataFrame containing the submissions' data.
        """
        if isinstance(self.submissions_file, str):
            submissions_file_name = self.submissions_file
        else:
            submissions_file_name = self.submissions_file.name
        file_name, file_ext = os.path.splitext(submissions_file_name)
        file = None
        if file_ext == '.xlsx':
            file = pd.read_excel(self.submissions_file, dtype=str, keep_default_na=False)
        return file

    def load_match_list(self):
        """
        Load the match_list data from the provided Excel file.

        Returns:
            pandas.DataFrame: A DataFrame containing the match_list' data.
        """
        if isinstance(self.match_list_file, str):
            match_list_file_name = self.match_list_file
        else:
            match_list_file_name = self.match_list_file.name
        file_name, file_ext = os.path.splitext(match_list_file_name)
        file = None
        if file_ext == '.xlsx':
            file = pd.read_excel(self.match_list_file, dtype=str, keep_default_na=False)
            if not self.user_inputs['id'] in file.columns:
                file = pd.read_excel(self.match_list_file, dtype=str,
                                     keep_default_na=False, header=[0, 1], index_col=[0])
                file.index = file.index.str.lower().str.strip()
            else:
                file[self.user_inputs['id']] = file[self.user_inputs['id']].str.lower().replace(' ', '')
                file.set_index(self.user_inputs['id'], inplace=True)
        return file

    @staticmethod
    def clean_id(df, id_col):
        df[[id_col]].apply(lambda col: col.str.lower())
        return df

    def filter_submissions(self):
        id_ = self.user_inputs.get('id', None)
        time_ = self.user_inputs.get('time')
        date_format = "%Y-%m-%d %H:%M:%S"
        self.submissions[id_] = self.submissions[id_].str.lower().str.strip()

        # Convert the string to a Pandas datetime object
        if time_:
            self.submissions[time_] = pd.to_datetime(self.submissions[time_], format=date_format)
            self.submissions['time_column'] = self.submissions[time_].dt.time
            if self.user_inputs.get('take_first_submission', False):
                self.submissions = self.submissions.loc[self.submissions.groupby(id_)['time_column'].idxmin()]
            else:
                self.submissions = self.submissions.loc[self.submissions.groupby(id_)['time_column'].idxmax()]
            self.submissions = self.submissions.drop('time_column', axis=1)
            self.submissions = self.submissions.sort_index().reset_index(drop=True)

    def process_questions(self):
        """
        Process and configure the list of questions to be checked.
        """
        columns_drop = self.user_inputs.get('non-questions_columns', [])
        columns_to_drop = []
        for col in self.submissions.columns:
            for pattern in columns_drop:
                if re.search(pattern.replace('*', '.*'), col):
                    columns_to_drop.append(col)
        questions = pd.DataFrame(
            {'Questions': self.submissions.drop(columns_to_drop, axis=1).keys()})
        questions_data_df = {}
        for i, question in enumerate(questions['Questions'].values, start=1):
            q_info = self.config.get('questions', {}).get(f'q{i}', {})
            # Create a dictionary with question information, including check status, answer, check type, and weight
            metadata = q_info.get('metadata', []) if q_info.get('metadata', []) is not None else []
            metadata = [str(i) for i in metadata]
            questions_data_df[f'q{i}'] = [question,
                                          q_info.get('check', False),
                                          q_info.get('answer', ''),
                                          q_info.get('check_type', ''),
                                          q_info.get('weight', 0),
                                          metadata]

        self.questions_data_df = pd.DataFrame(
            questions_data_df,
            index=['Questions', 'Check', 'Answer', 'Check Type', 'Weight', 'metadata']
        )

    def collect_optional_params(self):
        """
        Collect optional parameters from the system information and store them in user inputs.
        """
        self.user_inputs = {'id': self.system_info.get('id', ''), 'name': self.system_info.get('name', '')}
        for param in self.optional_params:
            param_value = self.system_info.get(param, None)
            self.user_inputs[param] = param_value
