import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from evodr.method.evodr import EVODR
import re

from evodr.method.evodr.prompt_algo import Prompt_algo
from evodr.method.evodr.prompt_sche import Prompt_sche
from evodr.task.optimization.online_fafsp.evaluation import Online_fafsp_Evaluation
from evodr.method.evodr.profiler import EVODRProfiler
from evodr.tools.llm.llm_api_openai import OpenAIAPI


def main():
    llm = OpenAIAPI(
        base_url=os.getenv("LLM_BASE_URL", ""),
        api_key=os.getenv("LLM_API_KEY", ""),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        timeout=120,
    )

    evaluation = Online_fafsp_Evaluation(
        timeout_seconds=None,
        n_instance=16,
        n_jobs=50,
        n_machines=10,
        safe_evaluate=False,
        daemon_eval_process=False
    )

    profiler = EVODRProfiler(log_dir="./logs")

    txt = evaluation._txt
    m = re.search(r"arrive(\d+).*u(\d+)", txt)
    _arrive = int(m.group(1)) if m else 20
    _u = int(m.group(2)) if m else 1

    prompt_algo = Prompt_algo(start_order_num=10, arrive_order_num=_arrive, u=_u)
    prompt_sche = Prompt_sche(start_order_num=10, arrive_order_num=_arrive, u=_u)

    evodr = EVODR(
        llm=llm,
        evaluation=evaluation,
        profiler=profiler,
        prompt_algo=prompt_algo,
        prompt_sche=prompt_sche,
        max_generations=10,
        max_sample_nums=100,
        pop_size=4,
        selection_num=2,
        n_create=4,
        gre_rand=0,
        use_e1_operator=True,
        use_e2_operator=True,
        use_m1_operator=True,
        use_m2_operator=True,
        num_samplers=1,
        num_evaluators=10,
        resume_mode=False,
        debug_mode=True,
        multi_thread_or_process_eval='thread'
    )

    print("Starting EVODR for Online FAFSP...")
    evodr.run()
    print("EVODR run completed!")


if __name__ == "__main__":
    main()
