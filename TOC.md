- [Auto Checker](#auto-checker)
   * [Features](#features)
   * [Installation](#installation)
   * [Usage](#usage)
   * [Config parameters](#config-parameters)
      + [YAML File Format (Tree Structure):](#yaml-file-format-tree-structure)
      + [YAML File Format:](#yaml-file-format)
      + [System Parameters ](#system-parameters)
            * [`eval_formula`](#eval_formula)
            * [`penalty_params` and `penalty_formula`](#penalty_params-and-penalty_formula)
         - [Example: Penalty Parameters](#example-penalty-parameters)
      + [Question Parameters](#question-parameters)
      + [Metadata Parameters](#metadata-parameters)
   * [Parameter Insights and Practical Implementations](#parameter-insights-and-practical-implementations)
      + [`code_names` and `code_types`](#code_names-and-code_types)
         - [Example 1:](#example-1)
         - [Example 2:](#example-2)
         - [Example 3](#example-3)
      + [`check_type`](#check_type)
         - [Supported Options](#supported-options)
         - [Threshold Parameters](#threshold-parameters)
         - [Example: Data Frame Validation](#example-data-frame-validation)
         - [Table of parameters for `check_type`](#table-of-parameters-for-check_type)
      + [`import_libs`, `allowed_libs`, and `disallowed_libs`](#import_libs-allowed_libs-and-disallowed_libs)
         - [`import_libs`](#import_libs)
         - [`allowed_libs` and `disallowed_libs`](#allowed_libs-and-disallowed_libs)
         - [Example:](#example)
      + [`columns`, `error_funcs`, and `sum_points_method`](#columns-error_funcs-and-sum_points_method)
         - [`columns`](#columns)
         - [`error_funcs`](#error_funcs)
         - [`sum_points_method`](#sum_points_method)
            * [Logic Overview](#logic-overview)
            * [YAML Example:](#yaml-example)
            * [Example Tables:](#example-tables)
      + [Examples of configs](#examples-of-configs)
         - [`code` check_type:](#code-check_type)
         - [`data` check_type:](#data-check_type)
         - [`num` check_type:](#num-check_type)
   * [Submission formats](#submission-formats)
      + [Submission Header:](#submission-header)
      + [Initial Match List Headers:](#initial-match-list-headers)
      + [Match List with Results:](#match-list-with-results)