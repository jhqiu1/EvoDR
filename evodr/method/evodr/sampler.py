

from __future__ import annotations

import re
from typing import Optional, Tuple, Dict, Any

from evodr.base import LLM, Function, TextFunctionProgramConverter


class EVODRSampler:
    # Role descriptions for different expert roles
    role_description_A = 'You are an algorithm expert who is well versed in programming and algorithms, you are required to design algorithms and provide the corresponding code according to the proposed requirements.'
    role_description_S = "You, as an expert in the field of dynamic shop floor scheduling, need to evaluate heuristic rules in terms of minimizing the tardiness in a scenario where orders arrive dynamically."
    
    def __init__(self, llm: LLM, template_program_str: str):
        self.llm = llm
        self.template_program_str = template_program_str
    
    def _call_llm(self, prompt: str, role: str = 'A', temperature: float = 1.0) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Unified LLM calling interface.
        Args:
            prompt: The prompt to send
            role: 'A' for Algorithm Expert, 'S' for Scheduling Expert
            temperature: Sampling temperature
        Returns:
            (response, usage_info)
        """
        role_description = self.role_description_A if role == 'A' else self.role_description_S
        
        # Check if llm has llm_A/llm_S methods
        method_name = f'llm_{role}'
        if hasattr(self.llm, method_name) and callable(getattr(self.llm, method_name)):
            # Use the dedicated method
            method = getattr(self.llm, method_name)
            return method(prompt, temperature)
        else:
            # Fallback to draw_sample with system prompt
            if isinstance(prompt, str):
                messages = [
                    {'role': 'system', 'content': role_description},
                    {'role': 'user', 'content': prompt.strip()}
                ]
            else:
                # Prepend system prompt to existing messages
                messages = [{'role': 'system', 'content': role_description}] + prompt
            
            result = self.llm.draw_sample(messages, temperature=temperature)
            if isinstance(result, tuple):
                response, usage_info = result
            else:
                response = result
                usage_info = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
            return response, usage_info
    
    @staticmethod
    def _clean_markdown_code_blocks(text: str) -> str:
        """Remove markdown code block markers (```python, ```, etc.) from text.
        
        Handles cases like:
        - ```python
        - ```
        - ```python code ```
        """
        import re
        
        # Pattern to match code block markers
        # Matches: ```language, ```, and closing ```
        pattern = r'^```(?:\w+)?\n?|```$'
        
        # Split into lines, process each line
        lines = text.split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            # Check for code block markers at the start/end of lines
            stripped_line = line.strip()
            
            # Detect code block start/end
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                # Skip the marker line
                continue
            elif stripped_line.endswith('```') and not stripped_line.startswith('```'):
                # Handle inline closing ```
                line = line.rsplit('```', 1)[0]
            
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # Fallback: if code blocks are inline, use regex to strip
        result = re.sub(r'```(?:\w+)?\n?(.*?)\n?```', r'\1', result, flags=re.DOTALL)
        
        return result
    
    @staticmethod
    def _get_arg_names(function: Function) -> list[str]:
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

    def get_thought_and_function(self, prompt: str, temperature: float = 1.0) -> Tuple[Optional[str], Optional[Function], Optional[Dict[str, Any]]]:
        """Get thought and function from LLM.
        """
        response, usage_info = self._call_llm(prompt, 'A', temperature)
        
        # extract algorithm description
        algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
        if len(algorithm) == 0:
            if 'python' in response:
                algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
            elif "import " in response:
                algorithm = re.findall(r'^.*?(?=import )', response, re.DOTALL)
            else:
                algorithm = re.findall(r'^.*?(?=def)', response, re.DOTALL)

        # First, clean any markdown code block markers (```python ... ```)
        cleaned_response = self._clean_markdown_code_blocks(response)
        
        # extract code - greedy match from first import/def to end
        code = re.findall(r"\b(?:import|def)\b[\s\S]*", cleaned_response)
        if len(code) == 0:
            # Fallback: match def until return with return value
            code = re.findall(r"\bdef\b[\s\S]*?return[^\n]*", cleaned_response)

        n_retry = 1
        max_retry = 3

        while (len(algorithm) == 0 or len(code) == 0) and n_retry <= max_retry:
            response, usage_info = self._call_llm(prompt, 'A', temperature)

            algorithm = re.findall(r"\{(.*)\}", response, re.DOTALL)
            if len(algorithm) == 0:
                if 'python' in response:
                    algorithm = re.findall(r'^.*?(?=python)', response, re.DOTALL)
                elif 'import ' in response:
                    algorithm = re.findall(r'^.*?(?=import )', response, re.DOTALL)
                else:
                    algorithm = re.findall(r'^.*?(?=def )', response, re.DOTALL)

            # Clean markdown code blocks before extracting code
            cleaned_response = self._clean_markdown_code_blocks(response)
            code = re.findall(r"\b(?:import|def)\b[\s\S]*", cleaned_response)
            if len(code) == 0:
                code = re.findall(r"\bdef\b[\s\S]*?return[^\n]*", cleaned_response)

            n_retry += 1

        if len(algorithm) == 0 or len(code) == 0:
            return None, None, usage_info

        algorithm = algorithm[0]
        code = code[0]

        # extract function name from template
        func_name_match = re.search(r"def\s+(\w+)\s*\(", self.template_program_str)
        if not func_name_match:
            return None, None, usage_info
        func_name = func_name_match.group(1)

        # extract return value from template
        return_match = re.search(r"return\s+(.*)\s*$", self.template_program_str, re.MULTILINE)
        if not return_match:
            return None, None, usage_info
        return_value = return_match.group(1)

        # Check if return statement exists and matches expected value
        # Pattern: match "return" followed by the return value (allowing whitespace/comments)
        code_stripped = code.strip()
        return_pattern = rf"\breturn\s+{re.escape(return_value)}\s*(?:#.*)?$"
        
        # Check if code already has a proper return statement
        has_proper_return = re.search(return_pattern, code_stripped, re.MULTILINE) is not None
        
        # Also check if there's any return statement (even if incomplete)
        has_any_return = "return" in code_stripped
        
        # Append return value only if missing or incomplete
        if not has_proper_return:
            if has_any_return:
                # There's a return but it's incomplete - replace it
                code_lines = code.rstrip().split('\n')
                for i in range(len(code_lines) - 1, -1, -1):
                    if 'return' in code_lines[i]:
                        code_lines[i] = f"    return {return_value}"
                        break
                code = '\n'.join(code_lines)
            else:
                # No return at all - add it
                code += f"\n    return {return_value}"

        # convert code to function
        try:
            func = TextFunctionProgramConverter.text_to_function(code)
            if func is None:
                return None, None, usage_info
            # add algorithm description to function
            func.algorithm = algorithm
            return algorithm, func, usage_info
        except Exception:
            return None, None, usage_info

    def get_ia2_thought_and_function(self, temperature=1.0):
        """Generate a new algorithm from scratch (ia2 operator).
        Corresponds to 260319's evolu.ia2(temperature).
        """
        from .prompt import EVODRPrompt
        func = TextFunctionProgramConverter.text_to_function(self.template_program_str)
        prompt = EVODRPrompt.get_prompt_ia2("", func)
        return self.get_thought_and_function(prompt, temperature)

    def get_ia3_thought_and_function(self, indiv, temperature=1.0):
        """Generate a new algorithm based on a single parent (ia3 operator).
        Corresponds to 260319's evolu.ia3(indiv, temperature).
        """
        from .prompt import EVODRPrompt
        func = TextFunctionProgramConverter.text_to_function(self.template_program_str)
        prompt = EVODRPrompt.get_prompt_ia3("", indiv, func)
        return self.get_thought_and_function(prompt, temperature)

    def get_evaluation(self, prompt: str, temperature: float = 1.0) -> tuple[Optional[Dict[str, str]], Optional[Dict[str, Any]]]:
        """Get evaluation and suggestion from LLM-S (Scheduling Expert).
        Returns:
            - opinion dict with 'evaluation' and 'suggestion' keys
            - usage info
        """
        response, usage_info = self._call_llm(prompt, 'S', temperature)
        
        # Parse evaluation and suggestion from response
        evaluation = self._extract_field(response, 'evaluation')
        suggestion = self._extract_field(response, 'suggestion')
        
        if evaluation or suggestion:
            return {
                'evaluation': evaluation or '',
                'suggestion': suggestion or ''
            }, usage_info
        return None, usage_info

    @staticmethod
    def _extract_field(text: str, field_name: str) -> Optional[str]:
        """Extract field value from response text.
        Supports formats like:
        - "field_name: [value]"
        - "field_name: value"
        """
        import re
        # Try patterns like "evalution: [...]" or "suggestion: [...]"
        patterns = [
            rf'{field_name}\s*:\s*\[(.*?)\](?=\n|$)',
            rf'{field_name}\s*:\s*(.*?)(?=\n\w+:|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no structured format found, try to extract content after field name
        lines = text.split('\n')
        for line in lines:
            if field_name.lower() in line.lower():
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None
