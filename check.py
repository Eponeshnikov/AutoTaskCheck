import pandas as pd
from fuzzywuzzy import fuzz
import sys
import numpy as np
import random, string
from yadisk import YaDisk
import os
import ast
import subprocess
import validators
import re
from sklearn.base import BaseEstimator
import sklearn.metrics
from sklearn.preprocessing import MinMaxScaler
from dataclasses import dataclass


def number_of_dec(s):
    res = 2 if s == 0 else np.int_(np.abs(np.min([np.log10(np.abs(s)), -2])))
    return res


def isnumeric(s_):
    try:
        res = int(s_)
        return True
    except Exception:
        try:
            res = float(s_)
            return True
        except Exception:
            return False


@dataclass
class PackageName:
    module: str = None
    alias_name: str = None
    alias_as_name: str = None

    def get_as_string(self):
        name_string = ""
        for i in (self.module, self.alias_name):
            if i is not None:
                name_string += f'{i} '
        return name_string[:len(name_string) - 1]


class Check:
    """Performs checks on submitted answers and calculates scores."""

    def __init__(self, questions_data, submissions, user_params):
        """
        Initialize the Check class.

        Parameters:
            questions_data (dict): Question data.
            submissions (DataFrame): Submitted answers.
            user_params (dict): User-defined parameters.
        """
        self.questions_data = questions_data
        self.submissions = submissions
        self.user_params = user_params
        self.questions_results_params = {}
        self.result = pd.DataFrame()

    @staticmethod
    def convert_metadata(metadata):
        """Convert metadata from string to dictionaries."""
        return [ast.literal_eval(i) for i in metadata]

    def gen_kwargs(self, metadata):
        """Generate keyword arguments from metadata."""
        kwargs = self.user_params

        # Iterate through metadata and extract key-value pairs
        for item in metadata:
            for key, value in item.items():
                kwargs[key] = value
        return kwargs

    def gen_multiindex(self):
        new_col = pd.MultiIndex.from_product([[self.user_params['name']], self.result.columns])
        self.result.columns = new_col

    def check_row(self, submission, question_key, filename):
        """Check a submitted answer for a specific question."""
        metadata = self.convert_metadata(self.questions_data[question_key]['metadata'])
        kwargs = self.gen_kwargs(metadata)
        correct_answer = self.questions_data[question_key]['Answer']
        check_type = self.questions_data[question_key]['Check Type']
        check = CheckOne(submission, correct_answer, check_type, filename=filename, **kwargs)
        check.run()
        return check.result

    @staticmethod
    def clean_folder_name(name):
        """Clean a folder name by removing invalid characters."""
        # Remove invalid characters for all operating systems
        cleaned_name = re.sub(r'[\/:*?"<>|]', '_', name)

        # Remove invalid characters for Windows file systems
        if os.name == 'nt':
            cleaned_name = re.sub(r'[\\]', '_', cleaned_name)

        # Remove leading and trailing spaces and periods
        cleaned_name = cleaned_name.strip(' .')

        return cleaned_name

    def check_submissions(self):
        """Check all submissions for each question and calculate scores."""

        def process_row(row):
            filename = self.clean_folder_name(str(q) + '_' + row[self.user_params['id']])
            return self.check_row(row[question_str], q, filename)

        for q in self.questions_data.keys():
            if self.questions_data[q]['Check'] and self.questions_data[q]['Check Type'] != '':
                question_str = self.questions_data[q]['Questions']
                self.result[q] = self.submissions.apply(process_row, axis=1)
                metadata = self.convert_metadata(self.questions_data[q]['metadata'])
                kwargs = self.gen_kwargs(metadata)
                low_v = kwargs.get('normalize_low', 0)
                high_v = kwargs.get('normalize_high', 100)
                if kwargs.get('normalize', False):
                    self.result[q] = MinMaxScaler(feature_range=(low_v, high_v)
                                                  ).fit_transform(self.result[[q]].to_numpy())
                    self.result[q] = self.result[q].round(np.max([number_of_dec(i) for i in self.result[q]]))
        self.result.set_index(pd.Index(self.submissions[self.user_params['id']]), inplace=True)
        self.penalty()
        self.sum_points()
        self.gen_multiindex()

    @staticmethod
    def soft_time(submission_time, deadline_time, **kwargs):
        """Calculate a soft time penalty for late submissions."""
        if submission_time < deadline_time:
            return 1
        else:
            delta = (submission_time.timestamp() - deadline_time.timestamp()) / 60
            if delta < kwargs.get('duration', 30):
                pen = kwargs.get('start_val', 1) / np.exp(kwargs.get('power', 0.01) * delta)
                return np.round(pen, number_of_dec(pen))
            else:
                return 0

    @staticmethod
    def no_penalty(submission_time, deadline_time, **kwargs):
        """Calculate no penalty for submissions."""
        return 1

    @staticmethod
    def const_penalty(submission_time, deadline_time, **kwargs):
        if submission_time < deadline_time:
            return 1
        else:
            return kwargs.get('start_val', 1)

    @staticmethod
    def exact_time(submission_time, deadline_time, **kwargs):
        """Calculate an exact time penalty for submissions."""
        return int(submission_time < deadline_time)

    def penalty(self):
        """Apply penalties to submissions based on user-defined parameters."""
        mapping_methods = {
            'soft': self.soft_time,
            'exact': self.exact_time,
            'none': self.no_penalty,
            'const': self.const_penalty
        }
        date_format = "%Y-%m-%d %H:%M:%S"
        penalty_params = {list(k.keys())[0]: list(k.values())[0] for k in self.user_params['penalty_params']}
        penalty_params['deadline_time'] = (
            pd.to_datetime(penalty_params.get('deadline_time', '2050-01-01 00:00:00'), format=date_format))
        method = mapping_methods[penalty_params.get('penalty_formula', 'exact')]

        self.submissions['penalty_coefficient'] = (
            self.submissions[self.user_params['time']].apply(lambda x: method(x, **penalty_params)))
        self.result = self.result.merge(self.submissions[[self.user_params['id'], 'penalty_coefficient']],
                                        on=self.user_params['id'], how='left').set_index(self.user_params['id'])
        self.submissions.drop('penalty_coefficient', axis=1, inplace=True)

    def sum_points(self):
        """Calculate the total score for each submission based on question weights and penalties."""
        eval_formulas = self.user_params.get('eval_formula', [])
        for eval_formula in eval_formulas:
            for q, rules in eval_formula.items():
                if self._should_evaluate_question(q):
                    points_q = self.result[q]

                    rule_cond = rules[0]
                    rule_actions = rules[1:]
                    # print(q, rule_cond, rule_actions)
                    condition_actions = {
                        'pass': self._process_pass_condition,
                        'fail': self._process_fail_condition
                        # Add more conditions as needed
                    }

                    # Check if the condition is in the dictionary and call the corresponding function
                    condition_type = rule_cond.split('_')[0]
                    if condition_type in condition_actions and rule_cond.split('_')[1].isdigit():
                        condition_actions[condition_type](points_q, float(rule_cond.split('_')[1]), rule_actions, q)

        self._calculate_total_score()

    def _should_evaluate_question(self, q):
        """Check if the question should be evaluated."""
        return (q in self.questions_data and self.questions_data[q]['Check']
                and self.questions_data[q]['Check Type'] != '')

    def _apply_rule_actions(self, condition_mask, rule_actions, q):
        """Apply actions based on the rule condition."""
        for rule_action_ in rule_actions:
            rule_action = rule_action_.split('_')
            questions_for_process = []
            if rule_action[0] == 'all':
                questions_for_process = [i for i in self.questions_data.keys()]
            else:
                if rule_action[0].startswith('q'):
                    questions_for_process = [rule_action[0]]
            # Call the corresponding method based on the rule[1] value
            rule_action_type = rule_action[1] if len(rule_action) > 1 else None
            rule_actions_mapping = {
                'reweight': self._multiply_all_other_questions,
                'set': self._set_value_for_other_questions
                # Add more rule[1] values and corresponding methods as needed
            }

            if rule_action_type in rule_actions_mapping:
                rule_actions_mapping[rule_action_type](condition_mask, rule_action, q, questions_for_process)

    def _process_pass_condition(self, points_q, threshold, rule_actions, q):
        """Process 'pass' condition and perform corresponding action."""
        condition_mask = points_q >= threshold
        self._apply_rule_actions(condition_mask, rule_actions, q)

    def _process_fail_condition(self, points_q, threshold, rule_actions, q):
        """Process 'fail' condition and perform corresponding action."""
        condition_mask = points_q < threshold
        self._apply_rule_actions(condition_mask, rule_actions, q)

    def _multiply_all_other_questions(self, condition_mask, rule_action, q, qs_proc):
        """Multiply all other questions based on the rule action."""
        for other_q in qs_proc:
            if other_q != q and self._should_evaluate_question(other_q):
                tmp_column = f'{other_q}_tmp_multiply'
                self.result[tmp_column] = 1.0
                multiplier = float(rule_action[2]) \
                    if any([rule_action[2].isdigit(),
                            rule_action[2][1:].isdigit() and rule_action[2].startswith('-')]) \
                    else 1.0
                self.result[tmp_column] *= np.where(condition_mask, multiplier, 1.0)

    def _set_value_for_other_questions(self, condition_mask, rule_action, q, qs_proc):
        """Set a value for other questions based on the rule action."""
        for other_q in qs_proc:
            if other_q != q and self._should_evaluate_question(other_q):
                tmp_column = f'{other_q}_tmp_set'
                value_to_set = float(rule_action[2]) if isnumeric(rule_action[2]) else 0
                self.result[tmp_column] = np.where(condition_mask, value_to_set, self.result[other_q])

    def _calculate_total_score(self):
        """Calculate the total score and apply penalties."""
        self._initialize_result_columns()

        for q in self.questions_data.keys():
            if self._should_evaluate_question(q):
                self._apply_question_weights_and_max_values(q)

        self._finish_calculating_total_score()

    def _initialize_result_columns(self):
        """Initialize necessary result columns."""
        self.result['total'] = [0 for i in range(len(self.result))]
        self.result['max_val'] = [0 for i in range(len(self.result))]

    def _apply_question_weights_and_max_values(self, q):
        """Apply question weights and max values to the result."""
        self.result[q] *= self.questions_data[q]['Weight']
        self.result['max_val'] += self.questions_data[q]['Weight']

        tmp_column_name_pattern = re.compile(fr'{q}_tmp_(\w+)')
        matching_columns = [col for col in self.result.columns if tmp_column_name_pattern.match(col)]

        for matching_column in matching_columns:
            # Extract the operation name from the column using regular expression
            operation_match = tmp_column_name_pattern.match(matching_column)
            if operation_match:
                operation_name = operation_match.group(1)

                # Choose the operation based on the extracted operation name
                operation_mapping = {
                    'multiply': self._multiply_temporary_column_back,
                    'set': self._set_value_temporary_column_back
                    # Add more operations as needed
                }

                if operation_name in operation_mapping:
                    operation_mapping[operation_name](q)
        self.result['total'] += self.result[q]

    def _multiply_temporary_column_back(self, q):
        """Multiply the temporary column back to the result DataFrame."""
        tmp_column_name = f'{q}_tmp_multiply'
        self.result[q] *= self.result[tmp_column_name]
        self.result.drop(tmp_column_name, axis=1, inplace=True)

    def _set_value_temporary_column_back(self, q):
        """Set a value for the temporary column back to the result DataFrame."""
        tmp_column_name = f'{q}_tmp_set'
        self.result[q] = self.result[tmp_column_name]  # Assuming all values are the same
        self.result.drop(tmp_column_name, axis=1, inplace=True)

    def _finish_calculating_total_score(self):
        """Finish calculating the total score and round it."""
        self.result['total'] *= self.result['penalty_coefficient'] / self.result['max_val']
        self.result['total'] = np.int_(np.round(self.result['total']))
        self.result.drop('max_val', axis=1, inplace=True)


class CheckOne:
    """
    Class for performing a sequence of operations on an answer and a correct value.
    """

    def __init__(self, answer, correct, config, **kwargs):
        """
        Initialize the CheckOne object with answer, correct value, configuration, and optional keyword arguments.
        """
        self.filepath = None
        self.kwargs = kwargs
        self.method_list = []
        self.answer = answer
        self.correct = correct
        self.result = 0
        self.config = config
        self.build_chain()

    def soft(self):
        """
        Apply a soft comparison operation using fuzz.WRatio.
        """
        self.result = fuzz.WRatio(self.correct.lower(), str(self.answer).lower())
        return self

    def hard(self):
        """
        Apply a hard comparison operation.
        """
        self.result = int(self.correct.lower() == self.answer.lower()) * 100
        return self

    def threshlow(self, threshold=50):
        """
        Apply a threshold operation for values less than the threshold.
        """
        if self.result < threshold:
            self.result = self.kwargs.get('threshlow_val', 0)
        return self

    def threshhigh(self, threshold=50):
        """
        Apply a threshold operation for values greater than or equal to the threshold.
        """
        if self.result >= threshold:
            self.result = self.kwargs.get('threshhigh_val', 100)
        return self

    def normalize(self, coef=100):
        """
        Normalizes the result by dividing by a coef.
        """
        self.result /= coef
        return self

    def reweight(self, coef=1):
        """
        Reweight the result by multiplying on a coef.
        """
        self.result *= coef
        return self

    def num(self, tol=0.02):
        """
        Apply assertequal checking of numeric answer with relative tol
        """
        try:
            res = int(np.isclose(float(self.answer), float(self.correct), rtol=tol))
            self.result = res
        except:
            print('Unable perform num checking')

    def code(self):
        """
        Perform code-related operations.
        """
        tests_run, tests_passed = self.__parse_test_output()
        if tests_run > 0:
            self.result = tests_passed / tests_run * 100
            self.result = np.round(self.result, number_of_dec(self.result))
        return self

    def data(self):
        correct_df, answer_df = self.__read_file()
        columns_check = self.kwargs.get('columns', list(correct_df.columns))
        error_funcs = self.kwargs.get('error_funcs', ['neg_mean_squared_error' for i in correct_df.columns])
        errors = []
        for c, e in zip(columns_check, error_funcs):
            correct_column = correct_df[c]
            try:
                column_check = answer_df[c]
            except Exception:
                try:
                    column_check = answer_df[c.lower()]
                except Exception:
                    try:
                        print(self.kwargs.get('filename'), 'use first column')
                        column_check = answer_df[answer_df.columns[0]]
                    except Exception:
                        print('use zeros list')
                        column_check = [0 for i in correct_df[c]]
            try:
                scorer = sklearn.metrics.get_scorer(e)
                adjust_len = np.min([len(correct_column), len(column_check)])
                error = scorer(IdentityTransformer(), correct_column[:adjust_len], column_check[:adjust_len])
                errors.append(np.round(error, number_of_dec(error)))
            except Exception as e_:
                print(e_)
        sum_points_method = self.kwargs.get('sum_points_method', 'mean')
        try:
            self.result = eval(f'np.{sum_points_method}(errors)')
        except Exception:
            self.result = eval(f'np.mean(errors)')
        return self

    def build_chain(self):
        """
        Parse the configuration string and build the list of operations.
        """
        methods = self.config.split('_')
        self.method_list = []
        i = 0
        while i < len(methods):
            method_name = methods[i]
            method = getattr(self, method_name)
            if callable(method):
                param_index = i + 1
                param_list = []
                while param_index < len(methods) and isnumeric(methods[param_index]):
                    param_list.append(int(methods[param_index]))
                    param_index += 1
                self.method_list.append({"method": method, "params": param_list})
                i = param_index
            else:
                raise ValueError(f"Unknown method: {method_name}")

    def run(self):
        """
        Perform the specified operations on the result.
        """
        for method_dict in self.method_list:
            method = method_dict["method"]
            params = method_dict["params"]
            method(*params)

    def __read_file(self):
        extension = self.kwargs.get('extension', 'csv')
        self.answer = self.__download(extension)
        correct_df = pd.read_csv(self.correct)
        answer_df = pd.read_csv(self.answer)
        return correct_df, answer_df

    def __download(self, ext='py'):
        """
        Download a Python file from Yandex Disk.
        """
        # Initialize Yandex Disk client
        token = self.kwargs.get('yatoken', '')
        y = YaDisk(token=token)

        # Extract submission filename from URL
        def randomword(length):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(length))

        basename = os.path.basename(self.answer) if self.answer is not None else f'{randomword(10)}'
        filename = self.kwargs.get('filename', basename)
        folder = self.kwargs.get('submission_folder', 'submissions')
        if not os.path.exists(folder):
            os.makedirs(folder)
        filepath = f"{folder}/{filename}.{ext}"
        # Download submission file from Yandex Disk
        if validators.url(self.answer):
            if not os.path.exists(filepath) or self.kwargs.get('force_download', False):
                y.download(self.answer.split('https://disk.yandex.ru/client/disk/')[-1], filepath)
        return filepath

    def __extract_imports(self):
        """
        Extract and filter import statements from the downloaded Python file.
        """

        def gen_import_line(package: PackageName) -> str:
            if package.module is None:
                if package.alias_as_name is None:
                    return f'import {package.alias_name}'
                else: return f'import {package.alias_name} as {package.alias_as_name}'
            else:
                if package.alias_as_name is None:
                    return f'from {package.module} import {package.alias_name}'
                else:
                    return f'from {package.module} import {package.alias_name} as {package.alias_as_name}'

        def filter_imports(import_):
            # Filter and allow/disallow imports based on configuration.
            allowed_libs = self.kwargs.get('allowed_libs', 'any')
            disallowed_libs = self.kwargs.get('disallowed_libs', '')

            if allowed_libs == 'any' and len(disallowed_libs) == 0:
                return True  # All imports are allowed

            if disallowed_libs == 'any':
                return False  # All imports are disallowed

            disallowed_libs = disallowed_libs.split(',')
            allowed_libs = allowed_libs.split(',')
            allowed = False if allowed_libs[0] != 'any' else True
            disallowed = True
            # Check if the import is not in the disallowed list
            for lib_pattern in disallowed_libs:
                if re.search(lib_pattern, import_) and disallowed_libs[0] != '':
                    disallowed = False
            for lib_pattern in allowed_libs:
                if len(lib_pattern) > 0:
                    if re.search(lib_pattern, import_) and allowed_libs[0] != 'any':
                        allowed = True
            return bool(allowed * disallowed)  # If not explicitly allowed, it's disallowed

        self.answer = self.__download()
        # Parse the code into an AST
        try:
            with open(self.answer, "r", encoding='utf-8') as answer:
                answer_code = answer.read()
            parsed_code = ast.parse(answer_code)
        except Exception as e:
            print(e)
            return []

        # Find and extract imports
        extracted_modules = []
        for node in ast.walk(parsed_code):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    extracted_modules.append(PackageName(alias_name=alias.name, alias_as_name=alias.asname))
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for alias in node.names:
                    extracted_modules.append(PackageName(module, alias.name, alias.asname))
        all_extracted_imports = {k.get_as_string(): gen_import_line(k) for k in extracted_modules}
        filter_extracted_imports = {k: all_extracted_imports[k]
                                    for k in list(filter(filter_imports, all_extracted_imports))}
        return [filter_extracted_imports[i] for i in filter_extracted_imports]

    def __extract_code(self):
        """
        Extract code from the downloaded Python file and optionally insert it into another file.
        """
        extracted_imports = self.__extract_imports()

        try:
            # Read the content of the downloaded Python file
            with open(self.answer, "r", encoding='utf-8') as answer:
                answer_code = answer.read()
            # Parse the code into an AST
            parsed_code = ast.parse(answer_code)
        except Exception as e:
            print(e)
            with open(f'{self.correct}.py', "r", encoding='utf-8') as my_file:
                my_content = my_file.read()
            test_file = self.answer.split('.')[0] + '_test' + '.py'
            # Save the modified content as new_my.py
            with open(f"{test_file}", "w", encoding='utf-8') as new_my_file:
                new_my_file.write(my_content)
            return test_file

        ast_objects_ = {
            'function': ast.FunctionDef,
            'class': ast.ClassDef
        }
        code_names_to_extract = self.kwargs.get('code_names', ['foo'])
        code_types = self.kwargs.get('code_types', ['function'])

        # Find and extract the specified function or class definition
        extracted_code = ""
        for code_name_to_extract, code_type in zip(code_names_to_extract, code_types):
            for node in ast.walk(parsed_code):
                if isinstance(node, ast_objects_[code_type]) and node.name == code_name_to_extract:
                    extracted_code += ast.unparse(node)
                    extracted_code += '\n\n'
                    break

        with open(f'{self.correct}.py', "r", encoding='utf-8') as my_file:
            my_content = my_file.read()

        # Insert the extracted function or class at the beginning of my.py
        import_libs = self.kwargs.get('import_libs', False)
        extracted_imports_str = '\n'.join(extracted_imports) + "\n\n" if import_libs else ''
        modified_content = extracted_imports_str + extracted_code + "\n\n" + my_content
        test_file = self.answer.split('.')[0] + '_test' + '.py'
        # Save the modified content as new_my.py
        with open(f"{test_file}", "w", encoding='utf-8') as new_my_file:
            new_my_file.write(modified_content)

        # print(f"'{code_names_to_extract}' has been inserted at the beginning of {test_file}.")
        return test_file

    @staticmethod
    def __run_tests(test_file_path):
        """
        Run tests by executing the specified test file.
        """
        result = subprocess.run([sys.executable, f"{test_file_path}"], capture_output=True)
        return result

    @staticmethod
    def __install_package(package):
        """
        Install a Python package using pip.
        """
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(e)

    def __safety_run_tests(self):
        """
        Safely run tests, handling missing modules by attempting installation.
        """
        test_file = self.__extract_code()
        self.missing_module = None
        attempts = self.kwargs.get('import_attempts', 3)
        test_output = ""
        while True:
            if attempts == 0:
                break
            result = self.__run_tests(test_file)
            test_output = str(result.stdout) + str(result.stderr)
            error_message = re.search(r"ModuleNotFoundError: No module named \\'(.*?)\\'", test_output)
            if error_message:
                if error_message.group(1) == self.missing_module or self.missing_module is None:
                    attempts -= 1
                self.missing_module = error_message.group(1)
                self.__install_package(self.missing_module)
            else:
                break
        return test_output

    def __parse_test_output(self):
        """
        Parse the output of the test run and extract the number of tests run, passed, and failed.
        """
        test_output = self.__safety_run_tests()
        # Extract the number of tests run, passed, and failed
        match = re.search(r"Ran (\d+) test", test_output)
        if match:
            tests_run = int(match.group(1))
        else:
            tests_run = 0

        match_failures_errors = re.search(r"(?:FAILED \(errors=(\d+)\)|FAILURES=(\d+))", test_output)
        if match_failures_errors:
            tests_failed = int(match_failures_errors.group(1)) if match_failures_errors.group(1) else int(
                match_failures_errors.group(2))
        else:
            tests_failed = 0

        tests_passed = tests_run - tests_failed
        return tests_run, tests_passed


class IdentityTransformer(BaseEstimator):
    def fit(self, X, y=None):
        # This method does nothing, as we don't need to learn anything from the data
        return self

    def predict(self, X):
        # This method returns the input values as they are
        return X
