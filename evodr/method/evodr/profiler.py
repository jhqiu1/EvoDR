

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd

from evodr.base import LLM, Evaluation, Function
from evodr.tools.profiler import ProfilerBase


class EVODRProfiler(ProfilerBase):
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = log_dir
        self.start_time = time.time()
        self.sample_history: List[Dict[str, Any]] = []
        self.population_history: List[Dict[str, Any]] = []

        # create log directory if not exists
        os.makedirs(self.log_dir, exist_ok=True)

    def record_parameters(self, llm: LLM, evaluation: Evaluation, evodr: Any):
        """Record parameters of EVODR.
        """
        self.parameters = {
            "llm": llm.__class__.__name__,
            "evaluation": evaluation.__class__.__name__,
            "max_generations": evodr._max_generations,
            "max_sample_nums": evodr._max_sample_nums,
            "pop_size": evodr._pop_size,
            "selection_num": evodr._selection_num,
            "use_e1_operator": evodr._use_e1_operator,
            "use_e2_operator": evodr._use_e2_operator,
            "use_m1_operator": evodr._use_m1_operator,
            "use_m2_operator": evodr._use_m2_operator,
            "num_samplers": evodr._num_samplers,
            "num_evaluators": evodr._num_evaluators,
            "multi_thread_or_process_eval": evodr._multi_thread_or_process_eval,
        }

    def register_function(self, function: Function, program: str):
        """Register a function to the profiler.
        """
        sample_info = {
            "algorithm": function.algorithm,
            "code": program,
            "score": function.score,
            "sample_time": function.sample_time,
            "evaluate_time": function.evaluate_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.sample_history.append(sample_info)

    def register_population(self, population: Any):
        """Register a population to the profiler.
        """
        population_info = {
            "generation": population.generation,
            "population_size": len(population),
            "best_score": population.get_best_individual().score if population.get_best_individual() else None,
            "worst_score": population.get_worst_individual().score if population.get_worst_individual() else None,
            "average_score": sum(indiv.score for indiv in population) / len(population) if population else None,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.population_history.append(population_info)

    def finish(self):
        """Finish profiling and save results.
        """
        end_time = time.time()
        total_time = end_time - self.start_time

        # save sample history
        sample_history_df = pd.DataFrame(self.sample_history)
        sample_history_path = os.path.join(self.log_dir, f"sample_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        sample_history_df.to_csv(sample_history_path, index=False, encoding="utf-8")

        # save population history
        population_history_df = pd.DataFrame(self.population_history)
        population_history_path = os.path.join(self.log_dir, f"population_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        population_history_df.to_csv(population_history_path, index=False, encoding="utf-8")

        # save parameters
        parameters_df = pd.DataFrame([self.parameters])
        parameters_path = os.path.join(self.log_dir, f"parameters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        parameters_df.to_csv(parameters_path, index=False, encoding="utf-8")

        # print summary
        print(f"\n--- EVODR Profiler Summary ---")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Total samples: {len(self.sample_history)}")
        print(f"Best score: {max([s['score'] for s in self.sample_history]) if self.sample_history else 'N/A'}")
        print(f"Sample history saved to: {sample_history_path}")
        print(f"Population history saved to: {population_history_path}")
        print(f"Parameters saved to: {parameters_path}")
