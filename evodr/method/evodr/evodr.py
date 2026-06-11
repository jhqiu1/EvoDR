

from __future__ import annotations

import concurrent.futures
import math
import time
import traceback
from threading import Thread
from typing import Optional, Literal, List

from .population import Population
from .profiler import EVODRProfiler
from .prompt import EVODRPrompt
from .sampler import EVODRSampler
from ...base import (
    Evaluation, LLM, Function, Program, TextFunctionProgramConverter, SecureEvaluator
)
from ...tools.profiler import ProfilerBase


class EVODR:
    def __init__(self, 
                 llm: LLM, 
                 evaluation: Evaluation, 
                 profiler: ProfilerBase = None, 
                 max_generations: Optional[int] = 20, 
                 max_sample_nums: Optional[int] = 200, 
                 pop_size: Optional[int] = 6, 
                 selection_num=2, 
                 use_e1_operator: bool = True, 
                 use_e2_operator: bool = True, 
                 use_m1_operator: bool = True, 
                 use_m2_operator: bool = True, 
                 num_samplers: int = 2, 
                 num_evaluators: int = 10, 
                 *, 
                 resume_mode: bool = False, 
                 debug_mode: bool = False, 
                 multi_thread_or_process_eval: Literal['thread', 'process'] = 'process',
                 prompt_algo,
                 prompt_sche,
                 n_create=4,
                 num_concurrent=2,
                 gre_rand=0,
                 **kwargs):
        """Evolutionary of Heuristics with Dynamic Rules.
        Args:
            llm             : an instance of 'llm4.base.LLM', which provides the way to query LLM.
            evaluation      : an instance of 'llm4.base.Evaluator', which defines the way to calculate the score of a generated function.
            profiler        : an instance of 'llm4.method.evodr.EVODRProfiler'. If you do not want to use it, you can pass a 'None'.
            max_generations : terminate after evolving 'max_generations' generations or reach 'max_sample_nums',
                              pass 'None' to disable this termination condition.
            max_sample_nums : terminate after evaluating max_sample_nums functions (no matter the function is valid or not) or reach 'max_generations',
                              pass 'None' to disable this termination condition.
            pop_size        : population size, if set to 'None', EVODR will automatically adjust this parameter.
            selection_num   : number of selected individuals while crossover.
            use_e1_operator : if use e1 operator.
            use_e2_operator : if use e2 operator.
            use_m1_operator : if use m1 operator.
            use_m2_operator : if use m2 operator.
            resume_mode     : in resume_mode, randsample will not evaluate the template_program, and will skip the init process. TODO: More detailed usage.
            debug_mode      : if set to True, we will print detailed information.
            multi_thread_or_process_eval: use 'concurrent.futures.ThreadPoolExecutor' or 'concurrent.futures.ProcessPoolExecutor' for the usage of
                multi-core CPU while evaluation. Please note that both settings can leverage multi-core CPU. As a result on my personal computer (Mac OS, Intel chip),
                setting this parameter to 'process' will faster than 'thread'. However, I do not sure if this happens on all platform so I set the default to 'thread'.
                Please note that there is one case that cannot utilize multi-core CPU: if you set 'safe_evaluate' argument in 'evaluator' to 'False',
                and you set this argument to 'thread'.
            **kwargs                    : some args pass to 'llm4.base.SecureEvaluator'. Such as 'fork_proc'.
        """
        self._template_program_str = evaluation.template_program
        self._task_description_str = prompt_algo.get_task()
        self._max_generations = max_generations
        self._max_sample_nums = max_sample_nums
        self._pop_size = pop_size
        self._selection_num = selection_num
        self._use_e1_operator = use_e1_operator
        self._use_e2_operator = use_e2_operator
        self._use_m1_operator = use_m1_operator
        self._use_m2_operator = use_m2_operator
        self._n_create = n_create
        self._num_concurrent = num_concurrent
        self._gre_rand = gre_rand

        # Set EVODRPrompt's static prompt objects (so static methods can access them)
        from .prompt import EVODRPrompt
        EVODRPrompt.prompt_algo = prompt_algo
        EVODRPrompt.prompt_sche = prompt_sche
        EVODRPrompt.feature_mask = self._get_feature_mask()
        print(f"[ABL-DBG] {self.__class__.__name__}: feature_mask={EVODRPrompt.feature_mask}")

        # samplers and evaluators
        self._num_samplers = num_samplers
        self._num_evaluators = num_evaluators
        self._resume_mode = resume_mode
        self._debug_mode = debug_mode
        llm.debug_mode = debug_mode
        self._multi_thread_or_process_eval = multi_thread_or_process_eval

        # function to be evolved
        self._function_to_evolve: Function = TextFunctionProgramConverter.text_to_function(self._template_program_str)
        self._function_to_evolve_name: str = self._function_to_evolve.name
        self._template_program: Program = TextFunctionProgramConverter.text_to_program(self._template_program_str)

        # adjust population size
        self._adjust_pop_size()

        # population, sampler, and evaluator
        self._population = Population(pop_size=self._pop_size)
        self._sampler = EVODRSampler(llm, self._template_program_str)
        self._evaluator = SecureEvaluator(evaluation, debug_mode=debug_mode, **kwargs)
        self._profiler = profiler

        # statistics
        self._tot_sample_nums = 0
        self._error_num = 0
        self._llm_s_calls = 0
        self._llm_s_input_tokens = 0
        self._llm_s_output_tokens = 0
        self._llm_a_input_tokens = 0
        self._llm_a_output_tokens = 0
        self._use_tokens = 0

        # Result collector callback (set externally for ablation data collection)
        self._result_collector = None  # callable(gen, population)

        # reset _initial_sample_nums_max
        if self._max_sample_nums is not None:
            self._initial_sample_nums_max = min(
                self._max_sample_nums,
                self._pop_size + 1  # 1 EDD + pop_size ia1 individuals (align with 260319)
            )
        else:
            self._initial_sample_nums_max = self._pop_size + 1
        # self._initial_sample_nums_max = 4
        # Temperature parameters (as in reference code)
        self._min_u = 1.0  # Minimum temperature
        self._max_u = 1.0  # Maximum temperature (currently fixed to 1.0)
        self._best_temperature = 1.0  # Best temperature found during initialization
        self._temperature_results = []  # Store (objective, temperature) pairs for evaluation
        
        # Thread-safe counter lock (for multi-threaded initialization)
        import threading
        self._counter_lock = threading.Lock()

        # multi-thread executor for evaluation
        assert multi_thread_or_process_eval in ['thread', 'process']
        if multi_thread_or_process_eval == 'thread':
            self._evaluation_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=num_evaluators
            )
        else:
            self._evaluation_executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=num_evaluators
            )

        # pass parameters to profiler
        if profiler is not None:
            self._profiler.record_parameters(llm, evaluation, self)  # ZL: necessary

    def _adjust_pop_size(self):
        # adjust population size (skip in pure-iteration mode)
        if self._max_sample_nums is None:
            if self._pop_size is None:
                self._pop_size = 5
            return
        if self._max_sample_nums >= 10000:
            if self._pop_size is None:
                self._pop_size = 40
            elif abs(self._pop_size - 40) > 20:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 40.')
        elif self._max_sample_nums >= 1000:
            if self._pop_size is None:
                self._pop_size = 20
            elif abs(self._pop_size - 20) > 10:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 20.')
        elif self._max_sample_nums >= 200:
            if self._pop_size is None:
                self._pop_size = 10
            elif abs(self._pop_size - 10) > 5:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 10.')
        else:
            if self._pop_size is None:
                self._pop_size = 5
            elif abs(self._pop_size - 5) > 5:
                print(f'Warning: population size {self._pop_size} '
                      f'is not suitable, please reset it to 5.')

    def _get_op_list(self) -> list:
        """Operators to use in evolution. Override for EDR-C/EDR-M ablation."""
        return ['e1', 'e2', 'm1', 'm2']

    def _get_feature_mask(self) -> list:
        """9 bool values, True = feature active. Override for EDR-D ablation.
        Indices: 0:status 1:num_neighboring_machine 2:processing_time 3:start_time
                 4:delivery_time 5:available_time 6:num_neighboring_operation
                 7:utilization 8:processing_tm
        """
        return [True] * 9

    def _should_init_edd_baseline(self) -> bool:
        """Override for EDR-E ablation."""
        return True

    def _should_use_f1_evaluation(self) -> bool:
        """Override for EDR-S-none ablation."""
        return True

    def _get_f1_evaluation(self, indiv):
        """Override for EDR-S-fixed / EDR-S-random.
        Returns opinion dict with 'evaluation' and 'suggestion' keys.
        """
        best_indiv = self._population.get_best_individual()
        worst_indiv = self._population.get_worst_individual()
        if best_indiv is None or worst_indiv is None:
            return {"evaluation": "", "suggestion": ""}
        f1_prompt = EVODRPrompt.get_prompt_f1(
            self._task_description_str, best_indiv, worst_indiv, indiv
        )
        opinion, f1_usage = self._sampler.get_evaluation(f1_prompt)
        if f1_usage:
            self._use_tokens += f1_usage.get('total_tokens', 0)
            self._llm_s_calls += 1
            self._llm_s_input_tokens += f1_usage.get('prompt_tokens', 0)
            self._llm_s_output_tokens += f1_usage.get('completion_tokens', 0)
        return opinion or {"evaluation": "", "suggestion": ""}

    def _sample_evaluate_register(self, prompt, temperature=1.0):
        """Perform following steps:
        1. Sample an algorithm using the given prompt.
        2. Evaluate it by submitting to the process/thread pool, and get the results.
        3. Add the function to the population and register it to the profiler.
        """
        sample_start = time.time()
        thought, func, usage_info = self._sampler.get_thought_and_function(prompt, temperature)
        sample_time = time.time() - sample_start
        if thought is None or func is None:
            with self._counter_lock:
                self._error_num += 1
            return
        
        # update statistics (thread-safe)
        with self._counter_lock:
            if usage_info:
                self._use_tokens += usage_info.get('total_tokens', 0)
                self._llm_a_input_tokens += usage_info.get('prompt_tokens', 0)
                self._llm_a_output_tokens += usage_info.get('completion_tokens', 0)
            self._tot_sample_nums += 1
        
        # convert to Program instance
        program = TextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            with self._counter_lock:
                self._error_num += 1
            return
        
        # evaluate
        try:
            score, eval_time = self._evaluation_executor.submit(
                self._evaluator.evaluate_program_record_time,
                program
            ).result()
            
            # Check for invalid score values (NaN, inf)
            if score is None or math.isnan(score) or math.isinf(score):
                # print(f"Warning: Invalid score value detected: {score}")
                # print(f"This may indicate numerical instability in the generated code (e.g., division by zero, overflow)")
                with self._counter_lock:
                    self._error_num += 1
                return
        except Exception as e:
            if self._debug_mode:
                traceback.print_exc()
            with self._counter_lock:
                self._error_num += 1
            return
        
        # register to profiler
        func.score = score
        func.evaluate_time = eval_time
        func.algorithm = thought
        func.sample_time = sample_time
        if self._profiler is not None:
            self._profiler.register_function(func, program=str(program))
            if isinstance(self._profiler, EVODRProfiler):
                self._profiler.register_population(self._population)

        # register to the population
        self._population.register_function(func)
        
        # Record temperature result during initialization phase (thread-safe)
        # This ensures the temperature determination has enough data
        if hasattr(self, '_temperature_determined') and not self._temperature_determined:
            with self._counter_lock:
                if score is not None and not math.isnan(score) and not math.isinf(score):
                    self._temperature_results.append((score, temperature))

    def _continue_loop(self) -> bool:
        """Check termination condition. Supports pure-iteration mode when max_sample_nums is None."""
        if self._max_sample_nums is not None:
            # Both generation and sample limits apply
            return (self._population.generation < self._max_generations
                    and self._tot_sample_nums < self._max_sample_nums)
        else:
            # Pure iteration mode: only check generation
            return self._population.generation < self._max_generations

    def _iteratively_use_evodr_operator(self):
        """Evolutionary loop matching 260319: iterate operators in order,
        generate n_create offspring per operator using multi-threading,
        evaluate each with F1 immediately, and perform population survival per iteration.
        """
        op_list = self._get_op_list()
        print(f"[ABL-DBG] {self.__class__.__name__}: op_list={op_list}")

        while self._continue_loop():
            for op in op_list:
                if not self._continue_loop():
                    break

                temp_population = []

                with concurrent.futures.ThreadPoolExecutor(max_workers=self._num_concurrent) as executor:
                    futures = []
                    for _ in range(self._n_create):
                        future = executor.submit(
                            self._process_individual, op, self._best_temperature
                        )
                        futures.append(future)

                    for future in concurrent.futures.as_completed(futures):
                        try:
                            temp_ind = future.result()
                            if temp_ind is not None and temp_ind.score is not None:
                                if not math.isinf(temp_ind.score) and not math.isnan(temp_ind.score):
                                    temp_population.append(temp_ind)
                        except Exception:
                            if self._debug_mode:
                                traceback.print_exc()

                # Add new individuals to population
                for ind in temp_population:
                    self._population.register_function(ind)

                if not self._continue_loop():
                    break

            # Perform population survival once per iteration (after all 4 operators, matching 260319)
            self._population.select_population(self._pop_size)

            # Generation completed
            best = self._population.get_best_individual()
            best_score_str = f"{best.score:.4f}" if best and best.score is not None else "N/A"
            print(f"--- Generation {self._population.generation} completed. "
                  f"Best objective: {best_score_str}, "
                  f"Total samples: {self._tot_sample_nums}")

            # Call result collector after each generation
            if self._result_collector is not None:
                self._result_collector(
                    gen=self._population.generation,
                    population=self._population
                )

        # shutdown evaluation_executor
        try:
            self._evaluation_executor.shutdown(cancel_futures=True)
        except:
            pass

    def _iteratively_init_population(self):
        """Let a thread repeat {sample -> evaluate -> register to population}
        to initialize a population using IA operators
        
        Implements linear temperature variation as in reference code:
        current_temperature = min_u + (max_u - min_u) * (n - 1) / (N - 1)
        """
        # Initial evaluation of EDD baseline (only run once across all threads)
        with self._counter_lock:
            if self._tot_sample_nums == 1:  # EDD is already registered
                # Gate IS1 behind F1 evaluation hook (EDR-S-none should skip)
                edd_opinion = self._is1_operator() if self._should_use_f1_evaluation() else {"evaluation": "", "suggestion": ""}
                if edd_opinion and len(self._population) > 0:
                    # Get the first individual (should be EDD)
                    for indiv in self._population:
                        indiv.opinion = edd_opinion
                        # Record EDD's score with temperature = 1.0
                        if hasattr(indiv, 'score'):
                            self._temperature_results.append((indiv.score, 1.0))
                        break
        
        # Operator cycle for initialization - only use ia1 (as in reference code)
        operators = ['ia1']
        op_idx = 0
        
        # Number of individuals to create during initialization (excluding EDD)
        N = self._initial_sample_nums_max - 1  # -1 for EDD
        
        # Safety: max attempts per thread to prevent infinite loop
        max_attempts_per_thread = self._initial_sample_nums_max * 3
        thread_attempts = 0
        
        while thread_attempts < max_attempts_per_thread:
            # Check termination condition first (thread-safe)
            with self._counter_lock:
                if self._tot_sample_nums >= self._initial_sample_nums_max:
                    print(
                        f'Initialization complete: {self._tot_sample_nums}/{self._initial_sample_nums_max} samples collected.')
                    break
            
            try:
                current_op = operators[op_idx % len(operators)]
                func = None
                
                # Calculate current temperature (as in reference code)
                # n = current individual index (1-based)
                with self._counter_lock:
                    n = self._tot_sample_nums  # EDD is already counted as 1
                
                if N > 1:
                    current_temperature = self._min_u + (self._max_u - self._min_u) * (n - 1) / (N - 1)
                else:
                    current_temperature = self._min_u
                
                # Only use ia1 operator (as in reference code: evolu.ia1(edd_ind, temperature))
                if current_op == 'ia1' and len(self._population) > 0:
                    func = self._ia1_operator(current_temperature)
                else:
                    # Fallback: use ia1 directly once population has EDD rule
                    if len(self._population) > 0:
                        func = self._ia1_operator(current_temperature)
                    else:
                        # If no EDD yet, use original i1 prompt
                        prompt = EVODRPrompt.get_prompt_i1(self._task_description_str, self._function_to_evolve)
                        self._sample_evaluate_register(prompt, current_temperature)
                        op_idx += 1
                        thread_attempts += 1
                        continue
                
                if func:
                    # Thread-safe counter increment
                    with self._counter_lock:
                        self._tot_sample_nums += 1
                    # Evaluate and also record temperature results
                    score = self._evaluate_and_register_with_temperature(func, current_temperature)
                
                op_idx += 1
                thread_attempts += 1
                
            except Exception:
                thread_attempts += 1
                if self._debug_mode:
                    traceback.print_exc()
                    exit()
                continue
        
        # After initialization (only run once across all threads)
        with self._counter_lock:
            if not hasattr(self, '_temperature_determined'):
                self._determine_best_temperature()
                self._temperature_determined = True

        # Perform population survival after initialization (aligns with 260319)
        if hasattr(self, '_temperature_determined') and self._temperature_determined:
            self._population.select_population(self._pop_size)

    def _evaluate_and_register(self, func: Function, thought: Optional[str] = None, sample_time: float = 0.0):
        """Evaluate and register a function.
        Unified method for both single-threaded (initialization) and multi-threaded modes.
        """
        start = time.time()

        # convert to Program instance
        program = TextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            with self._counter_lock:
                self._error_num += 1
            return

        # evaluate - use direct call for better debugging
        try:
            # Direct call (better for debugging)
            score, eval_time = self._evaluator.evaluate_program_record_time(program)
        except Exception as e:
            print(f"[DEBUG] Evaluation failed: {e}")
            if self._debug_mode:
                import traceback; traceback.print_exc()
                exit()
            with self._counter_lock:
                self._error_num += 1
            return

        func.score = score
        func.evaluate_time = eval_time
        func.sample_time = sample_time if sample_time > 0 else time.time() - start

        if self._profiler is not None:
            self._profiler.register_function(func, program=str(program))

        # register the function to population
        self._population.register_function(func)
        
    def _evaluate_and_register_with_temperature(self, func: Function, temperature: float, thought: Optional[str] = None, sample_time: float = 0.0) -> Optional[float]:
        """Evaluate and register a function, also recording temperature results.
        Used during initialization for temperature evaluation.
        
        Returns:
            score if evaluation succeeded, None otherwise
        """
        start = time.time()

        # convert to Program instance
        program = TextFunctionProgramConverter.function_to_program(func, self._template_program)
        if program is None:
            with self._counter_lock:
                self._error_num += 1
            return None

        # evaluate - use direct call for better debugging
        try:
            # Direct call (better for debugging)
            score, eval_time = self._evaluator.evaluate_program_record_time(program)
        except Exception as e:
            print(f"[DEBUG] Evaluation failed: {e}")
            if self._debug_mode:
                import traceback; traceback.print_exc()
                exit()
            with self._counter_lock:
                self._error_num += 1
            return None

        func.score = score
        func.evaluate_time = eval_time
        func.sample_time = sample_time if sample_time > 0 else time.time() - start

        if self._profiler is not None:
            self._profiler.register_function(func, program=str(program))

        # register the function to population
        self._population.register_function(func)
        
        # Record temperature result (score, temperature) - lower score is better (thread-safe)
        # Only record if score is valid (not NaN, not inf)
        with self._counter_lock:
            if score is not None and not math.isnan(score) and not math.isinf(score):
                self._temperature_results.append((score, temperature))
            else:
                print(f"Warning: Invalid score {score} detected, not recorded in temperature results")
        
        return score
        
    def _determine_best_temperature(self):
        """Determine the best temperature based on initialization results.
        As in reference code: find temperature with minimum objective value.
        """
        if not self._temperature_results:
            print("Warning: No temperature results available for evaluation.")
            self._best_temperature = 1.0
            return
            
        # Find best temperature (minimum score = best performance)
        # temperature_results format: list of (objective_score, temperature)
        best_score, best_temp = min(self._temperature_results, key=lambda x: x[0])
        self._best_temperature = best_temp
        
        print(f"--- 初始化温度评估完成 ---")
        print(f"最佳温度: {best_temp:.4f} (对应最低目标值: {best_score:.4f})")

    def _multi_threaded_sampling(self, fn: callable, *args, **kwargs):
        """Execute `fn` using multithreading.
        In EVODR, `fn` can be `self._iteratively_init_population` or `self._iteratively_use_evodr_operator`.
        """
        # threads for sampling
        sampler_threads = [
            Thread(target=fn, args=args, kwargs=kwargs)
            for _ in range(self._num_samplers)
        ]
        for t in sampler_threads:
            t.start()
        for t in sampler_threads:
            t.join()

    def _get_edd_function(self) -> Function:
        """Get EDD (Earliest Due Date) heuristic rule as baseline."""
        # Parse function name from template
        import re
        func_name_match = re.search(r"def\s+(\w+)\s*\(", self._template_program_str)
        func_name = func_name_match.group(1) if func_name_match else 'cal_priority'
        
        # Parse function arguments
        from .sampler import EVODRSampler
        input_names = EVODRSampler._get_arg_names(self._function_to_evolve)
        args_str = ', '.join(input_names)
        
        edd_code = f'''def {func_name}({args_str}):
    """EDD (Earliest Due Date) heuristic rule.
    Prioritization by delivery time (smaller delivery_time = higher priority).
    """
    # Prioritization by delivery time
    priority = delivery_time

    # Return priority results
    return priority
'''
        
        func = TextFunctionProgramConverter.text_to_function(edd_code)
        if func:
            func.algorithm = "The earlier the delivery date, the higher the production priority of the task."
        return func

    def _init_edd_baseline(self):
        """Initialize population with EDD baseline rule."""
        print("--- 正在评估基准规则 (EDD) ---")
        try:
            # Get EDD function
            edd_func = self._get_edd_function()
            if not edd_func:
                print("EDD 函数创建失败")
                return
            
            # Convert to Program instance
            program = TextFunctionProgramConverter.function_to_program(edd_func, self._template_program)
            if program is None:
                print("EDD 程序转换失败")
                return
            
            # Evaluate EDD rule (direct call for single evaluation)
            score, eval_time = self._evaluator.evaluate_program_record_time(program)
            
            # Register function
            edd_func.score = score
            edd_func.evaluate_time = eval_time
            edd_func.sample_time = 0.0
            
            if self._profiler is not None:
                self._profiler.register_function(edd_func, program=str(program))
            
            self._population.register_function(edd_func)
            self._tot_sample_nums += 1
            
            # Record EDD's score in temperature results (temperature = 1.0)
            if score is not None:
                self._temperature_results.append((score, 1.0))
                print(f"EDD 评估完成. Score: {score:.4f}")
            else:
                print(f"EDD 评估完成. Score: None (evaluation failed)")
        except Exception as e:
            print(f"EDD 评估失败: {e}")
            if self._debug_mode:
                traceback.print_exc()

    @staticmethod
    def _is_valid_individual(indiv: Function) -> bool:
        """Check if an individual has a valid score (not inf, nan, or None)."""
        if indiv.score is None:
            return False
        try:
            return not (math.isinf(indiv.score) or math.isnan(indiv.score))
        except:
            return False
    
    def _get_valid_population(self) -> List[Function]:
        """Get list of valid individuals from population."""
        return [indiv for indiv in list(self._population) if self._is_valid_individual(indiv)]

    def _evaluate_individual(self, indiv: Function) -> bool:
        """Evaluate individual using f1 operator (LLM-S).
        Add opinion dict with 'evaluation' and 'suggestion' to the individual.
        """
        try:
            # Skip LLM-S for EDR-S-none ablation
            if not self._should_use_f1_evaluation():
                print(f"[ABL-DBG] {self.__class__.__name__}: _evaluate_individual — F1 DISABLED (EDR-S-none)")
                indiv.opinion = {"evaluation": "", "suggestion": ""}
                return True

            # Get best and worst individuals in population (only valid ones)
            population_list = self._get_valid_population()
            if not population_list:
                return False
                
            best_indiv = max(population_list, key=lambda x: x.score)
            worst_indiv = min(population_list, key=lambda x: x.score)
            
            # Use hook for EDR-S ablation support
            opinion = self._get_f1_evaluation(indiv)
            print(f"[ABL-DBG] {self.__class__.__name__}: _evaluate_individual via hook — suggestion={opinion.get('suggestion','')[:50] if opinion else 'None'}...")
            if opinion and (opinion.get('evaluation') or opinion.get('suggestion')):
                indiv.opinion = opinion
                return True
            return False
        except Exception as e:
            if self._debug_mode:
                print(f"Evaluation error: {e}")
                traceback.print_exc()
            return False

    def _evaluate_population(self):
        """Evaluate all individuals in population using f1 operator."""
        print("--- 正在评估种群中的所有个体 ---")
        population_list = list(self._population)
        for indiv in population_list:
            self._evaluate_individual(indiv)

    def _is1_operator(self) -> Optional[Dict[str, str]]:
        """Initial evaluation operator.
        Evaluate the EDD baseline rule using LLM-S.
        """
        try:
            prompt = EVODRPrompt.get_prompt_is1()
            opinion, usage_info = self._sampler.get_evaluation(prompt)
            if usage_info:
                self._use_tokens += usage_info.get('total_tokens', 0)
                self._llm_s_calls += 1
                self._llm_s_input_tokens += usage_info.get('prompt_tokens', 0)
                self._llm_s_output_tokens += usage_info.get('completion_tokens', 0)
            return opinion
        except Exception as e:
            if self._debug_mode:
                print(f"IS1 operator error: {e}")
                traceback.print_exc()
            return None

    def _ia1_operator(self, temperature=1.0) -> Optional[Function]:
        """Improvement operator ia1.
        Improve algorithm based on improvement suggestions.
        
        Args:
            temperature: Sampling temperature for LLM (as in reference code).
        """
        try:
            # Select individual from population
            if len(self._population) == 0:
                return None
            indiv = self._population.greedy_choose(1, self._gre_rand)
            if len(indiv) == 0:
                return None
            indiv = indiv[0]
            
            # Ensure individual has opinion
            if not hasattr(indiv, 'opinion'):
                self._evaluate_individual(indiv)
            
            prompt = EVODRPrompt.get_prompt_ia1(
                self._task_description_str,
                indiv,
                self._function_to_evolve
            )
            _, func, usage_info = self._sampler.get_thought_and_function(prompt, temperature)
            if usage_info:
                self._use_tokens += usage_info.get('total_tokens', 0)
                self._llm_a_input_tokens += usage_info.get('prompt_tokens', 0)
                self._llm_a_output_tokens += usage_info.get('completion_tokens', 0)
            return func
        except Exception as e:
            if self._debug_mode:
                print(f"IA1 operator error: {e}")
                traceback.print_exc()
            return None

    def _process_individual(self, op, temperature):
        """Generate and evaluate a single individual using the specified operator.
        Includes F1 immediate evaluation (aligns with 260319's process_individual).

        Args:
            op: Operator name ('e1', 'e2', 'm1', 'm2')
            temperature: LLM sampling temperature

        Returns:
            Function object with score and opinion set, or None on failure
        """
        max_retries = 3

        for retry in range(max_retries):
            try:
                # Check termination condition
                with self._counter_lock:
                    if self._max_sample_nums is not None and self._tot_sample_nums >= self._max_sample_nums:
                        return None

                # --- Select parent(s) and generate prompt ---
                if op == 'e1':
                    parents = self._population.greedy_choose(self._selection_num, self._gre_rand)
                    if len(parents) < self._selection_num:
                        continue
                    prompt = EVODRPrompt.get_prompt_e1(
                        self._task_description_str, parents, self._function_to_evolve
                    )
                elif op == 'e2':
                    parents = self._population.greedy_choose(self._selection_num, self._gre_rand)
                    if len(parents) < self._selection_num:
                        continue
                    prompt = EVODRPrompt.get_prompt_e2(
                        self._task_description_str, parents, self._function_to_evolve
                    )
                elif op == 'm1':
                    parents = self._population.greedy_choose(1, self._gre_rand)
                    if len(parents) < 1:
                        continue
                    prompt = EVODRPrompt.get_prompt_m1(
                        self._task_description_str, parents[0], self._function_to_evolve
                    )
                elif op == 'm2':
                    parents = self._population.greedy_choose(1, self._gre_rand)
                    if len(parents) < 1:
                        continue
                    prompt = EVODRPrompt.get_prompt_m2(
                        self._task_description_str, parents[0], self._function_to_evolve
                    )
                else:
                    return None

                if self._debug_mode:
                    print(f'{op.upper()} Prompt: {prompt[:200]}...')

                # --- LLM generation ---
                thought, func, usage_info = self._sampler.get_thought_and_function(prompt, temperature)
                if thought is None or func is None:
                    if retry < max_retries - 1:
                        continue
                    return None

                with self._counter_lock:
                    self._tot_sample_nums += 1
                    if usage_info:
                        self._use_tokens += usage_info.get('total_tokens', 0)
                        self._llm_a_input_tokens += usage_info.get('prompt_tokens', 0)
                        self._llm_a_output_tokens += usage_info.get('completion_tokens', 0)

                # --- Evaluate ---
                sample_time = 0.0  # Will be set by _evaluate_and_register
                self._evaluate_and_register(func, thought, sample_time)

                if func.score is None or math.isinf(func.score) or math.isnan(func.score):
                    with self._counter_lock:
                        self._error_num += 1
                    continue

                # -- F1 评估 (use hook) --
                if self._should_use_f1_evaluation():
                    opinion = self._get_f1_evaluation(func)
                    func.opinion = opinion
                    print(f"[ABL-DBG] {self.__class__.__name__}: F1 eval ENABLED, suggestion={opinion.get('suggestion','')[:50]}...")
                else:
                    func.opinion = {"evaluation": "", "suggestion": ""}
                    print(f"[ABL-DBG] {self.__class__.__name__}: F1 eval DISABLED (EDR-S-none)")

                return func

            except Exception:
                if self._debug_mode:
                    traceback.print_exc()
                if retry >= max_retries - 1:
                    return None
                continue

        return None

    def run(self):
        if not self._resume_mode:
            # Initialize with EDD baseline (skip for EDR-E ablation)
            if self._should_init_edd_baseline():
                print(f"[ABL-DBG] {self.__class__.__name__}: EDD baseline ENABLED")
                self._init_edd_baseline()
            else:
                print(f"[ABL-DBG] {self.__class__.__name__}: EDD baseline DISABLED — using ia2")
                # EDR-E: init without EDD — use ia2 zero-shot generation
                for _ in range(self._pop_size):
                    thought, func, usage = self._sampler.get_ia2_thought_and_function(
                        temperature=1.0
                    )
                    if func is not None:
                        self._evaluate_and_register(func, thought)
                        self._tot_sample_nums += 1
                        if usage:
                            self._use_tokens += usage.get('total_tokens', 0)
                            self._llm_a_input_tokens += usage.get('prompt_tokens', 0)
                            self._llm_a_output_tokens += usage.get('completion_tokens', 0)
                self._population.select_population(self._pop_size)

            # do initialization
            self._multi_threaded_sampling(self._iteratively_init_population)
            self._population.select_population(self._pop_size)

            # Evaluate all individuals in population
            self._evaluate_population()
            # terminate searching if
            if len(self._population) < self._selection_num:
                print(
                    f'The search is terminated since EVODR unable to obtain {self._selection_num} feasible algorithms during initialization. '
                    f'Please increase the `initial_sample_nums_max` argument (currently {self._initial_sample_nums_max}). '
                    f'Please also check your evaluation implementation and LLM implementation.')
                return

        # Reset generation counter before evolution loop (init phase already counted)
        self._population._generation = 0

        # evolutionary search
        self._multi_threaded_sampling(self._iteratively_use_evodr_operator)

        # finish
        if self._profiler is not None:
            self._profiler.finish()

        # print statistics
        success_rate = 1 - self._error_num / self._tot_sample_nums if self._tot_sample_nums > 0 else 0
        print(f"--- 运行完成。统计: 当前共生成代码 {self._tot_sample_nums} 次, "
              f"LLM-A tokens: {self._llm_a_input_tokens}入/{self._llm_a_output_tokens}出, "
              f"LLM-S tokens: {self._llm_s_input_tokens}入/{self._llm_s_output_tokens}出, "
              f"LLM-S 调用次数: {self._llm_s_calls}")

        self._sampler.llm.close()
