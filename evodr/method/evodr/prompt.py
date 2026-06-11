

from __future__ import annotations

import ast
from typing import List, Dict, Any

from evodr.base import Function


class EVODRPrompt:
    # Class-level prompt instances (set by EVODR during initialization)
    prompt_algo = None
    prompt_sche = None
    feature_mask = None  # set by EVODR.__init__, list of 9 bool

    @staticmethod
    def _get_arg_names(function: Function) -> List[str]:
        """Parse argument names from function.args string."""
        if not function.args:
            return []
        args = []
        for arg in function.args.split(','):
            arg = arg.strip()
            if ':' in arg:
                arg = arg.split(':')[0].strip()
            if '=' in arg:
                arg = arg.split('=')[0].strip()
            if arg:
                args.append(arg)
        return args
    
    @staticmethod
    def _get_output_names(function: Function) -> List[str]:
        """Get output names - default to ['result'] if not specified."""
        return ['result']

    @staticmethod
    def _get_filtered_input_names(function_to_evolve, feature_mask=None):
        """Return only input names where feature_mask[index] is True."""
        all_names = EVODRPrompt._get_arg_names(function_to_evolve)
        if feature_mask is None or all(feature_mask):
            return all_names
        filtered = [name for i, name in enumerate(all_names) if i < len(feature_mask) and feature_mask[i]]
        print(f"[ABL-DBG] prompt input filter: {len(all_names)}→{len(filtered)}, active={filtered}")
        return filtered

    @staticmethod
    def get_prompt_i1(task_description: str, function_to_evolve: Function) -> str:
        """Get prompt for initializing the first individual.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_content = task_description + "\n"
        prompt_content += "First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_e1(task_description: str, indivs: List[Function], function_to_evolve: Function) -> str:
        """Get prompt for crossover operator e1.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_indiv = ""
        for i, indiv in enumerate(indivs):
            prompt_indiv += f"No.{i + 1} algorithm and the corresponding code are: \n"
            prompt_indiv += f"{indiv.algorithm}\n{str(indiv)}\n"
            prompt_indiv += f"Its evaluation is: {indiv.opinion['evaluation'] if hasattr(indiv, 'opinion') and 'evaluation' in indiv.opinion else 'N/A'}\n"
        
        prompt_content = task_description + "\n"
        prompt_content += f"I have {len(indivs)} existing algorithms with their codes and evaluations as follows: \n"
        prompt_content += prompt_indiv
        prompt_content += "Please design a new algorithm by combining the advantages of the two algorithms provided. \n"
        prompt_content += "You must respond according to the following requirements: First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_e2(task_description: str, indivs: List[Function], function_to_evolve: Function) -> str:
        """Get prompt for crossover operator e2.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_indiv = ""
        for i, indiv in enumerate(indivs):
            prompt_indiv += f"No.{i + 1} algorithm and the corresponding code are: \n"
            prompt_indiv += f"{indiv.algorithm}\n{str(indiv)}\n"
        
        prompt_content = task_description + "\n"
        prompt_content += f"I have {len(indivs)} existing algorithms with their codes and evaluations as follows: \n"
        prompt_content += prompt_indiv
        prompt_content += "Please help me create a new algorithm that has a totally different form from the given ones. \n"
        prompt_content += "You must respond according to the following requirements: First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_m1(task_description: str, indiv: Function, function_to_evolve: Function) -> str:
        """Get prompt for mutation operator m1.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_content = task_description + "\n"
        prompt_content += "I have one algorithm with its code and suggestion for improvement as follows. "
        prompt_content += f"Algorithm description: {indiv.algorithm}\n"
        prompt_content += f"Code:\n{str(indiv)}\n"
        prompt_content += f"Its suggestion for improvement is {indiv.opinion['suggestion'] if hasattr(indiv, 'opinion') and 'suggestion' in indiv.opinion else 'N/A'}. "
        prompt_content += "Please improve the given algorithm according to the suggestions for improvement. \n"
        prompt_content += "You must respond according to the following requirements: First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_m2(task_description: str, indiv: Function, function_to_evolve: Function) -> str:
        """Get prompt for mutation operator m2.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_content = task_description + "\n"
        prompt_content += "I have one algorithm with its code and suggestion for improvement as follows. "
        prompt_content += f"Algorithm description: {indiv.algorithm}\n"
        prompt_content += f"Code:\n{str(indiv)}\n"
        prompt_content += "Please identify the main algorithm parameters， then create a new algorithm that has a different parameter settings of the score function provided. \n"
        prompt_content += "You must respond according to the following requirements: First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def _safe_score_display(score: float) -> str:
        """Safely display score, handle infinity and None values."""
        if score is None:
            return "unknown"
        try:
            if score == float('inf') or score == float('-inf'):
                return "N/A"
            return f"{round(score * -1)}"
        except:
            return "N/A"
    
    @staticmethod
    def get_prompt_f1(task_description: str, best_indiv: Function, worst_indiv: Function, now_indiv: Function) -> str:
        """Get prompt for evaluation operator f1.
        """
        prompt_content = EVODRPrompt.prompt_sche.get_introd() + "\n"
        prompt_content += EVODRPrompt.prompt_sche.get_task() + "\n"
        prompt_content += f"Under current working condition, the best heuristic rule is: {best_indiv.algorithm} "
        prompt_content += f"And it's delay is: {EVODRPrompt._safe_score_display(best_indiv.score)} minutes. "
        prompt_content += f"The worst heuristic rule is: {worst_indiv.algorithm} "
        prompt_content += f"And it's delay is: {EVODRPrompt._safe_score_display(worst_indiv.score)} minutes. "
        prompt_content += "You need to evaluate the following heuristic rules based on the above information. \n"
        prompt_content += f"There is an existing heuristic rule: {now_indiv.algorithm}\n"
        prompt_content += f"The corresponding code is as follows: \n{str(now_indiv)}\n"
        prompt_content += f"And its delay is {EVODRPrompt._safe_score_display(now_indiv.score)} minutes. "
        prompt_content += "You need to evaluate the heuristic rule from the perspective of minimizing the tardiness and suggest improvements. "
        prompt_content += "The evaluation needs to include the strengths and weaknesses of the rule, followed by suggestions for improvement. "
        prompt_content += "Evaluation and improvements need to be suggested in terms of the following characteristics: "
        prompt_content += "task characteristics such as the number of machines available for the task, "
        prompt_content += "the processing time of the task, the time available for the task to start, and the time for the task to be delivered; "
        prompt_content += "machine characteristics such as the time available for the machine, the machine utilization rate, and the types of tasks that can be handled by the machine; "
        prompt_content += "and machine-task relationship characteristics such as the processing time of the task on the machine. \n"
        prompt_content += "Please respond in the following format, outputting only the key points and not adding explanations: \n"
        prompt_content += EVODRPrompt.prompt_sche.get_format()
        return prompt_content

    @staticmethod
    def get_prompt_is1() -> str:
        prompt_content = EVODRPrompt.prompt_sche.get_introd() + "\n"
        prompt_content += "The following heuristic rule exists: the earlier the delivery date, the higher the production priority of the task.\n"
        prompt_content += EVODRPrompt.prompt_sche.get_task()
        prompt_content += "Please respond in the following format, outputting only the key points and not adding explanations: \n"
        prompt_content += EVODRPrompt.prompt_sche.get_format()
        return prompt_content

    @staticmethod
    def get_prompt_ia1(task_description: str, indiv: Function, function_to_evolve: Function) -> str:
        """Get prompt for improvement operator ia1.
        Improve algorithm based on improvement suggestions.
        """
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)
        
        prompt_content = task_description + "\n"
        prompt_content += "I have an algorithm and its code as follows: \n"
        prompt_content += f"{indiv.algorithm}\n{str(indiv)}\n"
        if hasattr(indiv, 'opinion') and 'suggestion' in indiv.opinion:
            prompt_content += f"Its suggestion for improvement is {indiv.opinion['suggestion']}\n"
        prompt_content += "Please improve the given algorithm according to the suggestions for improvement.\n"
        prompt_content += "First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. "
        prompt_content += "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. "
        prompt_content += "(For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"
        prompt_content += "\n" + "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_ia2(task_description: str, function_to_evolve: Function) -> str:
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)

        prompt_algo = EVODRPrompt.prompt_algo
        prompt_content = prompt_algo.get_task() + "\n"
        prompt_content += "First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += prompt_algo.get_inout_inf() + " "
        prompt_content += prompt_algo.get_other_inf() + "\n"
        prompt_content += "Do not give additional explanations."
        return prompt_content

    @staticmethod
    def get_prompt_ia3(task_description: str, indiv: Function, function_to_evolve: Function) -> str:
        feature_mask = EVODRPrompt.feature_mask
        input_names = EVODRPrompt._get_filtered_input_names(function_to_evolve, feature_mask)
        output_names = EVODRPrompt._get_output_names(function_to_evolve)

        prompt_algo = EVODRPrompt.prompt_algo
        prompt_content = prompt_algo.get_task() + "\n"
        prompt_content += "I have an algorithm and its code as follows: \n"
        prompt_content += f"{indiv.algorithm}\n{str(indiv)}\n"
        prompt_content += "Based on this algorithm, generate a new algorithm."
        prompt_content += "First, describe your new algorithm and main steps in one sentence. "
        prompt_content += "The description must be inside a brace. Next, implement it in Python as a function named "
        prompt_content += function_to_evolve.name + ". "
        prompt_content += "This function should accept " + str(len(input_names)) + " input(s): "
        prompt_content += ", ".join("'" + s + "'" for s in input_names) + ". "
        prompt_content += "The function should return " + str(len(output_names)) + " output(s): "
        prompt_content += ", ".join("'" + s + "'" for s in output_names) + ". "
        prompt_content += prompt_algo.get_inout_inf() + " "
        prompt_content += prompt_algo.get_other_inf() + "\n"
        prompt_content += "Do not give additional explanations."
        return prompt_content
