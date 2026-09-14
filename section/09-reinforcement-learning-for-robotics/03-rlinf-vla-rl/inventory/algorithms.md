# RLINF 文件索引：algorithms

覆盖 `algorithms` 分组，共 `26` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `rlinf/algorithms/__init__.py` | 14 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | - | - |
| `rlinf/algorithms/advantages.py` | 352 | 优势估计、loss、奖励和算法注册 | - | compute_gae_advantages_and_returns, compute_grpo_advantages, compute_grpo_dynamic_advantages, compute_reinpp_advantages, compute_raw_advantages | rlinf, torch, typing |
| `rlinf/algorithms/loss_scales.py` | 182 | 优势估计、loss、奖励和算法注册 | - | group_scale, agent_scale, turn_scale | rlinf, torch |
| `rlinf/algorithms/losses.py` | 461 | 优势估计、loss、奖励和算法注册 | - | compute_decoupled_ppo_actor_loss, compute_ppo_actor_loss, compute_ppo_critic_loss, compute_decoupled_ppo_actor_critic_loss, compute_ppo_actor_critic_loss, compute_grpo_actor_loss_fn | rlinf, torch, typing |
| `rlinf/algorithms/registry.py` | 159 | 优势估计、loss、奖励和算法注册 | - | register_advantage, get_adv_and_returns, register_policy_loss, get_policy_loss, policy_loss, calculate_adv_and_returns, register_loss_scale, get_loss_scales, register_toolcall_parser, get_toolcall_parser | functools, rlinf, torch, typing |
| `rlinf/algorithms/rewards/__init__.py` | 38 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | register_reward, get_rule_based_reward_class | rlinf |
| `rlinf/algorithms/rewards/code/__init__.py` | 33 | 优势估计、loss、奖励和算法注册；公共入口/工具 | CodeRewardOffline | - | code_verifier, omegaconf |
| `rlinf/algorithms/rewards/code/code_verifier/__init__.py` | 13 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | - | - |
| `rlinf/algorithms/rewards/code/code_verifier/verify.py` | 230 | 优势估计、loss、奖励和算法注册 | - | fim_llm_as_judge_verify_call, create_session_with_retry, _build_prompt, send_reward_request, process_single_request | concurrent, json, os, requests, typing, urllib3 |
| `rlinf/algorithms/rewards/math/__init__.py` | 42 | 优势估计、loss、奖励和算法注册；公共入口/工具 | MathReward | - | math_verifier, omegaconf |
| `rlinf/algorithms/rewards/math/math_verifier/__init__.py` | 13 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | - | - |
| `rlinf/algorithms/rewards/math/math_verifier/parser.py` | 441 | 优势估计、loss、奖励和算法注册 | - | _fix_fracs, _fix_a_slash_b, _fix_sqrt, convert_word_number, strip_string, choice_answer_clean, extract_answer | re, word2number |
| `rlinf/algorithms/rewards/math/math_verifier/verify.py` | 441 | 优势估计、loss、奖励和算法注册 | - | choice_answer_clean, str_to_pmatrix, parse_digits, is_digit, numeric_equal, symbolic_equal, symbolic_equal_process, math_equal, call_with_timeout, process_results | concurrent, latex2sympy2, multiprocessing, parser, re, regex, sympy, typing |
| `rlinf/algorithms/rewards/rstar2/__init__.py` | 182 | 优势估计、loss、奖励和算法注册；公共入口/工具 | Rstar2Reward | _compute_score_wrapper | multiprocessing, omegaconf, time |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/__init__.py` | 13 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | - | - |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/compute_score.py` | 37 | 优势估计、loss、奖励和算法注册 | - | compute_score | math_verify, prime_math |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/math_verify.py` | 43 | 优势估计、loss、奖励和算法注册 | - | compute_score | - |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/prime_math/__init__.py` | 440 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | _sympy_parse, _parse_latex, _is_float, _is_int, _is_frac, _str_is_int, _str_to_int, _inject_implicit_mixed_number, _strip_properly_formatted_commas, _normalize | contextlib, grader, math, re |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/prime_math/grader.py` | 545 | 优势估计、loss、奖励和算法注册 | - | is_digit, normalize, handle_base, handle_pi, math_equal, symbolic_equal, format_intervals, _mp_target_wrapper, timeout_limit | contextlib, functools, math, multiprocessing, os, queue, re, signal |
| `rlinf/algorithms/rewards/rstar2/fused_compute_score/prime_math/math_normalize.py` | 192 | 优势估计、loss、奖励和算法注册 | - | normalize_answer, _fix_fracs, _fix_a_slash_b, _remove_right_units, _fix_sqrt, _strip_string | re, typing |
| `rlinf/algorithms/rewards/searchr1/__init__.py` | 181 | 优势估计、loss、奖励和算法注册；公共入口/工具 | SearchR1Reward | normalize_answer, em_check, subem_check, extract_solution, count_answer_tags, compute_score, compute_score_subem | omegaconf, random, re, string |
| `rlinf/algorithms/rewards/vqa/__init__.py` | 60 | 优势估计、loss、奖励和算法注册；公共入口/工具 | VQAReward | - | format_rewards, omegaconf, qa_rewards, torch |
| `rlinf/algorithms/rewards/vqa/format_rewards.py` | 66 | 优势估计、loss、奖励和算法注册；奖励计算或奖励模型 | - | think_format_reward, answer_format_reward | re |
| `rlinf/algorithms/rewards/vqa/qa_rewards.py` | 109 | 优势估计、loss、奖励和算法注册；奖励计算或奖励模型 | - | qa_accuracy_reward, _compare_choice_content | re |
| `rlinf/algorithms/toolcall_parsers.py` | 297 | 优势估计、loss、奖励和算法注册 | Qwen25ToolCallParser, Searchr1QwenToolCallParser, Rstar2QwenToolCallParser, WideSeekQwenToolCallParser | - | json, logging, re, regex, rlinf |
| `rlinf/algorithms/utils.py` | 398 | 优势估计、loss、奖励和算法注册；公共入口/工具 | - | huber_loss, kl_penalty, preprocess_embodied_advantages_inputs, calculate_scores, postprocess_embodied_advantages_outputs, preprocess_reasoning_advantages_inputs, postprocess_reasoning_advantages_outputs, preprocess_loss_inputs, postprocess_loss_metric, expand_to_target_dim | torch, typing |
