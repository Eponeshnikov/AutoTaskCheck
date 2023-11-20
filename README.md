# Auto Checker

This is an automated checking system for grading student assignments and tests. It allows configuring checking rules, applying penalties, normalizing scores, and calculating totals.

## Features

- ✅ Check submissions against correct answers
- ⚙️ Configure checking rules like fuzziness, thresholds, etc.
- ⏰ Apply penalties for late submissions
- 📈 Normalize scores to a range
- 💯 Calculate weighted totals with question points
- 👥 Match student IDs to info from a separate match list
- 💻 Extract and check code submissions
- 🧪 Run tests against code submissions
- 📦 Install missing modules automatically
- 🔒 Restrict imports in code submissions
- 📊 Validate submitted data frames
- 📉 Check data columns with different metrics (MSE, MAE, etc.)
- 🧮 Combine errors with options like mean, min, max
- 🔢 Check numeric answers within tolerance
- 🔡 Check text answers with fuzziness thresholds

## Installation

Requires Python 3.10+. Install requirements:

```bash
pip install -r requirements.txt
```

## Usage

To run checker:

```bash
streamlit run 1_📈_AutoChecker.py
```

Go to:
```plaintext
http://localhost:8501
```

The checker requires a YAML config file and an Excel submissions file:

The config defines the questions, answers, checking logic, weights, etc. The submissions contain the answers to check. 

## Config parameters

The config file specifies the parameters for the checking system.

### YAML File Format (Tree Structure):

```plaintext
answers.yml
├── system_info
│   ├── non-questions_columns
│   │   ├── "ID"
│   │   ├── "Some_Column"
│   │   └── ... (other columns)
│   ├── name: "Some Quiz"  # or "Some Lab", "Another Quiz", etc.
│   ├── id: "ID_Column:"
│   ├── submission_folder: "submissions/some_path"  # or corresponding folder path
│   ├── time: "Creation Time"
│   ├── penalty_params
│   │   ├── penalty_formula: soft
│   │   ├── deadline_time: "2023-XX-XX XX:XX:XX"
│   │   └── ... (other penalty parameters)
│   ├── take_first_submission: True
│   ├── force_download: False
│   └── yatoken: "some_yatoken_value"
└── questions
    ├── q1
    │   ├── name: "Question 1"
    │   ├── answer: "Some abstract answer"
    │   ├── check_type: hard
    │   └── metadata
    │       └── ... (metadata details including code_names, code_types, etc.)
    ├── q2
    │   └── ... (details for q2)
    └── ... (other questions)
```

Note: The tree structure represents the hierarchical organization of the YAML file, with ellipses (`...`) indicating additional details within each section. The specific values used in the examples are abstract and can be replaced with actual values as per your requirements.

### YAML File Format:
```yaml
system_info:
  non-questions_columns:
    - "ID"
    - "Some_Column"
    # ... (other columns)
  name: "Some Quiz"  # or "Some Lab", "Another Quiz", etc.
  id: "ID_Column:"
  submission_folder: "submissions/some_path"  # or corresponding folder path
  time: "Creation Time"
  penalty_params:
    - penalty_formula: soft
    - deadline_time: "2023-XX-XX XX:XX:XX"
    # ... (other penalty parameters)
  take_first_submission: True
  force_download: False
  yatoken: "some_yatoken_value"
questions:
  q1:
    - name: "Question 1"
    - answer: "Some abstract answer"
    - check_type: hard
    - metadata:
        # ... (metadata details including code_names, code_types, etc.)
  q2:
    # ... (details for q2)
  # ... (other questions)
```

Note: Question Naming Convention

When configuring the questions in the YAML file, it's essential to adhere to the naming convention used internally within the code. The method `process_questions()` iterates through the list of questions, assigning them labels `q1`, `q2`, and so on, based on the order in which they are processed. These labels directly correspond to the keys used for questions in the YAML configuration file. Ensure consistency between the question keys in the YAML file and their respective metadata and configurations within the codebase to maintain accurate processing and configuration alignment.


### System Parameters 

System parameters define high-level settings for the checker.

| Parameter | Description                                                                           | Required | Default | Possible Values |  
|-|---------------------------------------------------------------------------------------|-|-|-|
| `name` | The name of the assignment/test, displayed in results.                                | ✅ Required | - | Text string |
| `id` | The column in submissions containing student IDs.                                     | ✅ Required | - | Column name |
| `time` | The column with submission timestamps for penalties. Format **YYYY-MM-DD HH\:MM\:SS** | ⚙️ Optional | - | Column name |
| `penalty_params` | Parameters for applying late submission penalties:                                    | ⚙️ Optional | - | - |
| `penalty_formula` | The penalty calculation method.                                                       | ⚙️ Optional | "exact" | "soft", "exact", "none", "const" |
| `deadline_time` | Deadline timestamp for applying penalties.                                            | ⚙️ Optional | Distant future | Timestamp string |  
| `power` | Exponential power parameter for "soft" penalty formula.                               | ⚙️ Optional | 0.01 | Number |
| `start_val` | Starting penalty value for "soft" and "const" formulas.                               | ⚙️ Optional | 1 | Number |
| `duration` | Duration in minutes over which penalties decline for "soft" formula.                  | ⚙️ Optional | 30 mins | Number |
| `submission_folder` | Folder to save downloaded files.                                                      | ⚙️ Optional | "submissions" | Folder path |
| `take_first_submission` | Take first or last submission timestamp per student.                                  | ⚙️ Optional | false | true, false |
| `eval_formula` | Formulas for calculating total scores from questions.                                 | ⚙️ Optional | - | List of formulas |
| `yatoken` | Yandex Disk authorization token for downloading submissions.                          | ⚙️ Optional | - | Token string |

&nbsp;
#### `eval_formula`
The `eval_formula` allows defining conditional logic to calculate total scores based on question scores. It is a list of formulas with the following structure:

```yaml
eval_formula:
    - q*: 
      - condition
      - action1
      - action2
      ...
```

- `q*` refers to the question number, e.g. `q16`.
- `condition` is a pass or fail condition like `pass_100` or `fail_50`:
  - `pass_num` - Pass if the question score is >= num
  - `fail_num` - Fail if the question score is < num
- `action` defines what to do when the condition is met:
  - `all_reweight_num` - Multiply all question scores by num
  - `q*_reweight_num` - Multiply a specific question score by num
  - `all_set_num` - Set all question scores to num
  - `q*_set_num` - Set a specific question score to num

For example:

```yaml
- q16:
  - pass_100
  - all_reweight_2
```

This doubles all question scores if q16 >= 100.

The `eval_formula` allows conditional bonuses, limits, etc. based on specific question scores.

#### `penalty_params` and `penalty_formula`

The `penalty_params` and `penalty_formula` dictate how late submission penalties are applied by the auto checker (multiplying by generated coefficient). They configure the penalty behavior:

- **`deadline_time`**: Timestamp used to compare submissions against the deadline.
- **`penalty_formula`**: Options to calculate penalties:
  - `soft`: Exponentially decaying penalty over time.
  - `exact`: Binary 0/1 penalty for submissions before/after the deadline.
  - `none`: No penalty applied.
  - `const`: Fixed penalty applied after the deadline. Setting by **`start_val`** parameter.
  
For the `soft` penalty formula, additional parameters are utilized:

- **`start_val`**: Starting penalty value at the deadline, usually set to 1.
- **`power`**: Exponential decay power, typically ranging between 0.01 and 0.1. Determines the decay rate.
- **`duration`**: Time duration in minutes over which penalties decay and then becomes zero.

The **`soft` exponential penalty** is calculated as:

$$penalty =  start\_val * e^{-power * delta\_minutes}$$

Where:

- $start\_val$ represents the starting penalty value.
- $power$ controls the exponential decay rate.
- $delta\_minutes$ is the time after the deadline in minutes.

This results in a smooth exponential decay from the $start\_val$ over the specified $duration$. If $delta\_minutes$ exceeds $duration$ - result becomes $0$. The $power$ parameter regulates the decay speed.

Configuring `deadline_time` and `penalty_params` allows customizable late submission penalties by multiplying each score with the calculated penalty value.

#### Example: Penalty Parameters

Consider the following configuration:

```yaml
penalty_params:
  - penalty_formula: soft
  - deadline_time: "2023-11-30 23:59:59"
  - start_val: 1
  - power: 0.05
  - duration: 1440
```

In this scenario:

- `penalty_formula` is set to `soft`, implying an exponential decay of penalties over time.
- `deadline_time` is specified as "2023-11-30 23:59:59", which is the deadline timestamp.
- `start_val` is defined as 1, indicating the initial penalty value.
- `power` is set to 0.05, determining the rate of exponential decay.
- `duration` is 1440 minutes (24 hours), configuring the duration over which penalties decay to zero.

These parameters collaboratively create an exponential decay penalty function that starts at a value of 1 and decreases exponentially over a 24-hour duration after the defined deadline.


---

### Question Parameters

Question parameters configure the details of each individual question. 

Specified under `questions` in the config file.

| Parameter                   | Description | Required | Default | Possible Values                                                                               |
|-----------------------------|-|-|-|-----------------------------------------------------------------------------------------------|
| `answer`                    | The correct answer string. | ✅ Required | - | Text string  |
| `check`                     | Whether to check/grade the question. | ⚙️ Optional | true | true, false                                                                                   |
| [`check_type`](#check-type) | The checking logic. | ✅ Required | - | "hard", "soft", "code", "data", etc                                                           |
| `weight`                    | Number of points the question is worth. | ⚙️ Optional | 0 | Number                                                                                        |

###
The `answer` parameter defines the submitted data for evaluation, provided either as a text string or a path referring to `.py` test files (without extension) or correct dataframe files (with extension).

---

### Metadata Parameters

Metadata parameters allow customizing the checking logic and scoring.

Specified in `metadata` list for each question.

| Parameter | Description | Required | Default | Possible Values                                                                                                |
|-|-|-|-|----------------------------------------------------------------------------------------------------------------|
| `normalize` | Whether to normalize scores. | ⚙️ Optional | false | true, false                                                                                                    |
| `normalize_low` | Lower bound for normalized score range. | ⚙️ Optional | 0 | Number                                                                                                         |
| `normalize_high` | Upper bound for normalized score range. | ⚙️ Optional | 100 | Number                                                                                                         |
| `threshlow_val` | Value applied when a submitted value falls below `threshlow`. | ⚙️ Optional | - | Number                                                                                                         |
| `threshhigh_val` | Value applied when a submitted value exceeds `threshhigh`. | ⚙️ Optional | - | Number                                                                                                         |
| `code_names` | Names of functions/classes to extract from code. | ⚙️ Optional | - | List of strings                                                                                                |
| `code_types` | Type for extracted code - "function" or "class". | ⚙️ Optional | - | "function", "class"                                                                                            |
| `import_libs` | Whether to allow imports in extracted code. | ⚙️ Optional | false | true, false                                                                                                    | 
| `allowed_libs` | List of allowed import library patterns. | ⚙️ Optional | "any" | List of strings                                                                                                |
| `disallowed_libs` | List of disallowed import library patterns. | ⚙️ Optional | "" | List of strings                                                                                                |
| `columns` | Columns to check for "data" questions. | ⚙️ Optional | - | List of column names                                                                                           |
| `error_funcs` | Error functions to use for "data" questions. | ⚙️ Optional | "neg_mean_squared_error" | [List of errors](https://scikit-learn.org/stable/modules/model_evaluation.html#common-cases-predefined-values) |
| `sum_points_method` | How to combine errors for "data". | ⚙️ Optional | "mean" | "mean", "min", "max" etc                                                                                       |
| `extension` | File format extension | ⚙️ Optional | `'py'` | File format extensions (e.g., `'csv'`, `'xlsx'`, `'json'`, etc.)                                               |

&nbsp;
## Parameter Insights and Practical Implementations

### `code_names` and `code_types`

In the examples provided, the `code_names` and `code_types` metadata parameters are used to specify the expected names and types of functions or classes within the submitted code. Here's how you can structure these parameters:

#### Example 1:

```yaml
metadata:
  - code_names:
      - function_name_1
      - function_name_2
  - code_types:
      - function
      - function
  - import_libs: True
```

In this example, the metadata specifies that the submitted code is expected to contain two functions, named `function_name_1` and `function_name_2`. Both of these functions are expected to be of type `function`. The `import_libs` parameter is set to `True`, indicating that the submitted code is allowed to include imports.

#### Example 2:

```yaml
metadata:
  - code_names:
      - class_name
  - code_types:
      - class
  - import_libs: False
```

In this example, the metadata specifies that the submitted code should include a class named `class_name`, and it should be of type `class`. The `import_libs` parameter is set to `False`, suggesting that the submitted code should not include any imports.

#### Example 3

```yaml
metadata:
  - code_names:
      - function_name_1
      - function_name_2
      - class_name_1
      - class_name_2
  - code_types:
      - function
      - function
      - class
      - class
  - import_libs: True
```

In this example, the metadata details specify the expectations for the submitted code, outlining that it should contain multiple functions and classes for validation. The provided code snippet declares a set of function names (`function_name_1` and `function_name_2`) and class names (`class_name_1` and `class_name_2`), categorizing them accordingly as functions and classes, respectively. Additionally, the `import_libs` parameter set to `True` implies that the submission should include relevant libraries or dependencies for proper execution and validation of the functions and classes listed.

### `check_type`

The `check_type` parameter in the configuration file enables the customization of grading strategies for individual questions. It dictates the sequence of operations in the grading pipeline by combining methods and, when necessary, numerical parameters connected by underscores ('_').

#### Supported Options

- `hard`: Requires an exact match between the submitted answer and the expected answer.
- `soft`: Executes a fuzzy string match with customized high and low thresholds to accommodate variations in the answer.
- `code`: Evaluates submitted code by running specific tests against the extracted code snippets. The "answer" in the configuration should be the path to the unit test (using the **unittest** library) to test the provided functions or classes.
- `data`: Validates submitted data frames or structured data.
- `num`: Checks numeric answers, allowing a specified relative tolerance (**rtol**) range for comparison. Formula for calculating tolerance for two numbers $a - answer, b - correct\_answer$:  $absolute(a - b) <= 1e-8 + rtol * absolute(b)$. If this condition is met, then the answer is counted as correct.
- `normalize`:  Normalizes the result by dividing by a specified coefficient
- `reweight`: Reweights the result by multiplying it by a specified coefficient

#### Threshold Parameters

The `check_type` parameter supports threshold parameters, `threshlow` and `threshhigh`, which are used to define boundaries for evaluating submitted values against predefined limits. These parameters play a crucial role in defining ranges within which submitted values retain their default grading, while values outside this range receive alternative default results. 

- `threshlow`: Establishes the lower limit or boundary for submitted values. Any submitted value below this threshold is assigned a default grading or result.
- `threshhigh`: Sets the upper limit or boundary for submitted values. Values exceeding this threshold receive a different default result.
- `threshlow_val`: Defines the specific value used when a submitted value falls below the `threshlow` threshold.
- `threshhigh_val`: Specifies the value applied when a submitted value exceeds the `threshhigh` threshold.


For example, consider the configuration:

```yaml
check_type: soft_threshhigh_70_threshlow_30
metadata:
  - threshlow_val: 20
  - threshhigh_val: 80
```


In this scenario, the `soft` check type specifies a fuzzy string match with customized thresholds. The `threshlow_val` and `threshhigh_val` parameters in the metadata section further refine the boundaries for grading. Any submitted value below 30 receives a `threshlow_val` grading, while values exceeding 70 receive an `threshhigh_val` result, ensuring precise evaluation within the specified range.

#### Example: Data Frame Validation

```yaml
check_type: data_threshlow_-100_threshhigh_-10
```

The `data` method is applied here, specifying the validation of submitted data frames within the defined lower and upper bounds (-100 to -10). This configuration ensures precise validation of structured data submissions.

#### Table of parameters for `check_type`

| Parameter         | Description                                                                                                | Default | Possible Values                          |
|-------------------|------------------------------------------------------------------------------------------------------------|---------|------------------------------------------|
| `hard`            | Requires an exact match between the submitted answer and the expected answer.                              | -       | -                                        |
| `soft`            | Executes a fuzzy string match with customized high and low thresholds to accommodate variations in the answer. | -       | -                                        |
| `code`            | Evaluates submitted code by running specific tests against the extracted code snippets.                    | -       | -                                        |
| `data`            | Validates submitted data frames or structured data.                                                        | -       | -                                        |
| `num`             | Checks numeric answers, allowing a specified relative tolerance (**rtol**) range for comparison.         | 0.02    | numeric                                        |
| `threshlow`       | Establishes the lower limit or boundary for submitted values.                                                | 50      | numeric                                         |
| `threshhigh`      | Sets the upper limit or boundary for submitted values.                                                       | 50      | numeric                                         |
| `normalize`       | Normalizes the result by dividing by a specified coefficient.                                       | 100     | numeric                                  |
| `reweight`        | Reweights the result by multiplying it by a specified coefficient.                                  | 1       | numeric                                 |

&nbsp;
### `import_libs`, `allowed_libs`, and `disallowed_libs`

The metadata parameters `import_libs`, `allowed_libs`, and `disallowed_libs` for `code` `check_type` offer granular control over import permissions within extracted code snippets.

#### `import_libs`

When set to `true`, this parameter allows imports within the extracted code. Setting it to `false` restricts all imports.

#### `allowed_libs` and `disallowed_libs`

These parameters accept lists of import library patterns and utilize Regular Expressions (RegEx) to define import inclusion or exclusion rules:

- **`allowed_libs`**: Includes libraries specified in the pattern. For example, `"pandas,numpy,matplotlib"` permits imports for any libraries matching these terms. Allows all libraries if set to **'any'**.
- **`disallowed_libs`**: Prevents inclusion of libraries specified in the pattern. For instance, `"os,sys"` restricts any import statement containing 'os' or 'sys'. Disallows all libraries if set to **'any'**

#### Example:

```yaml
metadata:
  - import_libs: True
  - allowed_libs: "pandas,numpy,matplotlib"
  - disallowed_libs: "os,sys"
```
This example allows imports for `pandas`, `numpy`, and `matplotlib` libraries while disallowing imports for `os` and `sys`. Adjust the `allowed_libs` and `disallowed_libs` patterns to suit specific import rules or needs within your code extraction settings.

### `columns`, `error_funcs`, and `sum_points_method`

The parameters `columns`, `error_funcs`, and `sum_points_method` aid in validating and scoring "data" type questions within the extracted code snippets.

#### `columns`

This parameter specifies the columns to check for "data" type questions. By default, it utilizes all columns in the correct data frame.

#### `error_funcs`

Defines the error functions to use for assessing discrepancies in "data" type questions. If unspecified, it defaults to using the negative mean squared error (`'neg_mean_squared_error'`) for each column.

#### `sum_points_method`

Determines how errors for multiple columns are combined to generate an overall score. The default method is to calculate the mean (`'mean'`) of the errors.

##### Logic Overview

- **Column Selection**: Uses the `columns` parameter to identify specific columns within the correct data frame for comparison.
- **Error Functions**: Retrieves the specified or default error functions to evaluate discrepancies between the correct and answer data frames. Error functions are applied to their corresponding columns.
- **Error Calculation**: For each specified column, it calculates the error ([list of errors](https://scikit-learn.org/stable/modules/model_evaluation.html#common-cases-predefined-values) (*not all errors works!*)) using the appropriate function (`sklearn.metrics.get_scorer`). If unspecified columns or errors occur during comparison, it falls back to default handling methods or prints a relevant message.
- **Combining Errors**: Utilizes the `sum_points_method` to aggregate the errors from different columns. It calculates the `np.*` function of errors (default: `np.mean`).

##### YAML Example:

```yaml
metadata:
  columns:
    - "column1"
    - "column2"
    - "column3"
  error_funcs:
    - "neg_mean_squared_error"
    - "neg_mean_absolute_error"
    - "r2_score"
  sum_points_method: "mean"
```

##### Example Tables:

**Correct Table:**
| column1 | column2 | column3 |
|---------|---------|---------|
| 10      | 8       | 15      |
| 12      | 7       | 14      |
| 9       | 9       | 16      |
##
**Answer Table:**
| column1 | column2 | column3 |
|---------|---------|---------|
| 9       | 7       | 14      |
| 11      | 8       | 13      |
| 8       | 10      | 15      |
##
In this example, the `columns` parameter specifies the columns to check for "data" questions (`column1`, `column2`, `column3`). The corresponding `error_funcs` parameter defines the error functions to apply to each column (`neg_mean_squared_error` for `column1`, `neg_mean_absolute_error` for `column2`, and `r2_score` for `column3`). The `sum_points_method` is set to calculate the mean of the errors. Adjust these settings based on the specific requirements of your data validation within code extraction settings.

### Examples of configs

#### `code` check_type:
```yaml
questions:
  q1:
    answer: "tasks/lab_task/task1"
    check_type: code
    metadata:
      - code_names:
          - function_name
      - code_type:
          - function
      - import_libs: True
    check: True
    weight: 1

  q2:
    answer: "tasks/lab_task/task2"
    check_type: code
    metadata:
      - code_names:
          - another_function
      - code_type:
          - function
      - import_libs: True
    check: True
    weight: 1
```

#### `data` check_type:
```yaml
questions:
  q1:
    answer: "tasks/data_analysis/data1.csv"
    check_type: data_threshlow_0_threshhigh_100
    metadata:
      - threshlow_val: 0
      - threshhigh_val: 100
      - normalize: True
      - normalize_low: 10
      - columns:
        - "Column1"
        - "Column2"
      - error_funcs:
        - neg_mean_squared_error
      - sum_points_method: mean
      - extension: csv
    check: True
    weight: 1

  q2:
    answer: "tasks/data_analysis/data2.csv"
    check_type: data_threshlow_-10_threshhigh_10
    metadata:
      - threshlow_val: -10
      - threshhigh_val: 10
      - normalize: False
      - columns:
        - "Feature_A"
        - "Feature_B"
      - error_funcs:
        - neg_mean_absolute_error
        - neg_root_mean_squared_error
      - sum_points_method: max
      - extension: csv
    check: True
    weight: 1
```

#### `num` check_type:
```yaml
questions:
  q1:
    answer: 42
    check_type: num_threshlow_40_threshhigh_50
    metadata:
      - threshlow_val: 40
      - threshhigh_val: 50
    check: True
    weight: 1

  q2:
    answer: 3.14
    check_type: num_threshlow_3.1_threshhigh_3.2
    metadata:
      - threshlow_val: 3.1
      - threshhigh_val: 3.2
    check: True
    weight: 1
```

## Submission formats

### Submission Header:
This table represents the initial details of submissions in an Excel (.xlsx) format.

If there is a link to the file in submission, then downloading only from Yandex disk is supported.

<table>
  <tr>
    <th>ID</th>
    <th>Created At</th>
    <th>Name</th>
    <th>Question 1</th>
    <th>Question 2</th>
    <th>Question 3</th>
  </tr>
</table>

&nbsp;

### Initial Match List Headers:

**Variant 1:**
A table layout displaying the essential details for initial matching in an Excel (.xlsx) format.

<table>
  <tr>
    <th>Name</th>
    <th>Group Number</th>
    <th>ID</th>
  </tr>
</table>

&nbsp;

**Variant 2:**
An alternate layout providing necessary information for matching purposes in an Excel (.xlsx) format. `Info` column is required.

<table>
  <tr>
    <th></th>
    <th colspan="2">Info</th>
  </tr>
  <tr>
    <th></th>
    <th>Some info</th>
    <th>Some info 2</th>
  </tr>
  <tr>
    <th>ID</th>
    <th></th>
    <th></th>
  </tr>
</table>

&nbsp;

### Match List with Results:
A comprehensive table capturing match details and quiz results in an Excel (.xlsx) format. `Info` column is required.

<table>
  <tr>
    <th></th>
    <th colspan="2">Info</th>
    <th colspan="7">Quiz Results</th>
  </tr>
  <tr>
    <th></th>
    <th>Some info</th>
    <th>Some info 2</th>
    <th>q1 (100)</th>
    <th>q2 (100)</th>
    <th>q3 (100)</th>
    <th>q4 (100)</th>
    <th>q5 (200)</th>
    <th>Penalty coefficient</th>
    <th>Total (%)</th>
  </tr>
  <tr>
    <th>ID</th>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
</table>

