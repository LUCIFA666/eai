# SimpleVLA-RL 文件索引：reward-utils

覆盖 `reward-utils` 分组，共 `19` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/utils/reward_score/__init__.py` | 13 | 奖励打分工具；公共入口/工具 | - | - | - |
| `verl/utils/reward_score/countdown.py` | 122 | 奖励打分工具 | - | extract_solution, validate_equation, evaluate_equation, compute_score | ast, operator, random, re |
| `verl/utils/reward_score/evaluation_utils/code_util/__init__.py` | 80 | 奖励打分工具；公共入口/工具 | - | evaluate_code | json, os, re, traceback, utils |
| `verl/utils/reward_score/evaluation_utils/code_util/testing_util.py` | 822 | 奖励打分工具 | CODE_TYPE, TimeoutException, Capturing | truncatefn, timeout_handler, only_int_check, string_int_check, combined_int_check, clean_traceback, run_test, custom_compare_, stripped_string_compare, call_method | ast, datetime, enum, faulthandler, io, json, numpy, os |
| `verl/utils/reward_score/evaluation_utils/code_util/testing_util_org.py` | 755 | 奖励打分工具 | CODE_TYPE, TimeoutException, Capturing | truncatefn, timeout_handler, only_int_check, string_int_check, combined_int_check, clean_traceback, run_test, custom_compare_, stripped_string_compare, call_method | ast, datetime, enum, faulthandler, io, json, numpy, platform |
| `verl/utils/reward_score/evaluation_utils/code_util/testing_utils_org.py` | 755 | 奖励打分工具；公共入口/工具 | CODE_TYPE, TimeoutException, Capturing | truncatefn, timeout_handler, only_int_check, string_int_check, combined_int_check, clean_traceback, run_test, custom_compare_, stripped_string_compare, call_method | ast, datetime, enum, faulthandler, io, json, numpy, platform |
| `verl/utils/reward_score/evaluation_utils/code_util/utils.py` | 46 | 奖励打分工具；公共入口/工具 | - | _temp_run, check_correctness | datasets, multiprocessing, os, sys, testing_util, traceback, typing |
| `verl/utils/reward_score/evaluation_utils/libero_util/__init__.py` | 3 | 奖励打分工具；公共入口/工具 | - | evaluate_libero | - |
| `verl/utils/reward_score/evaluation_utils/math_util/__init__.py` | 949 | 奖励打分工具；公共入口/工具 | - | timeout, _sympy_parse, _parse_latex, _is_float, _is_int, _is_frac, _str_is_int, _str_to_int, _inject_implicit_mixed_number, _strip_properly_formatted_commas | grader, math, multiprocessing, os, pylatexenc, re, sympy |
| `verl/utils/reward_score/evaluation_utils/math_util/grader.py` | 384 | 奖励打分工具 | TimeoutException | is_digit, normalize, handle_base, handle_pi, math_equal, symbolic_equal, time_limit, format_intervals | contextlib, math, re, signal, sympy, typing |
| `verl/utils/reward_score/evaluation_utils/math_util/math_normalize.py` | 163 | 奖励打分工具 | - | normalize_answer, _fix_fracs, _fix_a_slash_b, _remove_right_units, _fix_sqrt, _strip_string | re, typing |
| `verl/utils/reward_score/evaluation_utils/test.py` | 154 | 奖励打分工具 | - | - | code_util, json, math_util |
| `verl/utils/reward_score/evaluation_utils/test2.py` | 139 | 奖励打分工具 | - | test_parallelism, test_prime_code, test_check_correctness, test_prime_math | asyncio, json, verl |
| `verl/utils/reward_score/gsm8k.py` | 63 | 奖励打分工具 | - | extract_solution, compute_score | re |
| `verl/utils/reward_score/logic.py` | 226 | 奖励打分工具 | - | extract_solution, parse_solution_text_format, parse_model_answer, validate_response_structure, compute_score | random, re, typing |
| `verl/utils/reward_score/math.py` | 227 | 奖励打分工具 | - | compute_score, is_equiv, remove_boxed, last_boxed_only_string, fix_fracs, fix_a_slash_b, remove_right_units, fix_sqrt, strip_string | - |
| `verl/utils/reward_score/multiply.py` | 64 | 奖励打分工具 | - | extract_solution, compute_score | random, re |
| `verl/utils/reward_score/prime.py` | 286 | 奖励打分工具 | - | process_completion, process_row_with_timeout, parallel_evaluate_continual_async, compute_score | asyncio, concurrent, evaluation_utils, functools, json, math, tqdm, traceback |
| `verl/utils/reward_score/test3.py` | 2 | 奖励打分工具 | - | - | - |
