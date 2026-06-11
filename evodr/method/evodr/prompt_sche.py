class Prompt_sche():
    def __init__(self, start_order_num, arrive_order_num, u):
        self.prompt_introd = " "
        self.prompt_task = "You need to evaluate the heuristic rule from the perspective of minimizing the tardiness and suggest improvements. \
The evaluation needs to include the strengths and weaknesses of the rule, followed by suggestions for improvement. " \
"Evaluation and improvements need to be suggested in terms of the following characteristics: task characteristics such as the number of machines available for the task, " \
"the processing time of the task, the time available for the task to start, and the time for the task to be delivered; " \
"machine characteristics such as the time available for the machine, the machine utilization rate, and the types of tasks that can be handled by the machine; "\
   "and machine-task relationship characteristics such as the processing time of the task on the machine. \n"
        self.prompt_format = "evalution: [The strengths is (Based on the characteristics provided, describe the core strengths in one sentence); The weaknesses is (Based on the characteristics provided, identify major weaknesses in 1 sentence)]\n" \
 "suggestion: [Make no more than 3 suggestions for improvement based on the characteristics provided, each described in one sentence or less]"
        self.start_order_num = start_order_num
        self.arrive_order_num = arrive_order_num
        self.u = u

    def get_introd(self):
        self.prompt_introd = f'''In a dynamic shop scheduling problem, there are {self.start_order_num} orders available for production at moment 0 and the number of subsequent arrivals is {self.arrive_order_num}. \
The average arrival interval of the orders follows an exponential distribution whose mean is given by the formula: the average processing time of the orders divided by the shop load factor, which is currently {self.u}.'''
        return self.prompt_introd

    def get_task(self):
        return self.prompt_task

    def get_format(self):
        return self.prompt_format
