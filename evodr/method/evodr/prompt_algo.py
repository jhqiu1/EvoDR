class Prompt_algo():
    def __init__(self, start_order_num, arrive_order_num, u):
        self.prompt_task = f'''In a dynamic shop scheduling problem, there are {start_order_num} orders available for production at moment 0 and the number of subsequent arrivals is {arrive_order_num}. \
The average arrival interval of the orders follows an exponential distribution whose mean is given by the formula: the average processing time of the orders divided by the shop load factor, which is currently {u}.'''\
            "Design a algorihtm to decide the priority of 'job-machine' arcs using specified features, with the optimization goal of minimizing tardiness. The output priority value should follow smaller-value-higher-priority convention."
        self.prompt_func_name = "cal_priority"
        self.prompt_func_inputs = [
            "status",
            "num_neighboring_machine",
            "processing_time",
            "start_time",
            "delivery_time",
            "available_time",
            "num_neighboring_operation",
            "utilization",
            "processing_tm"
        ]
        self.prompt_func_outputs = ["priority"]
        self.prompt_inout_inf = "The 'job' variable represents job-related information including status (0/1 indicating scheduling status), " \
                                "num_neighboring_machine (number of compatible machines), processing_time (actual/average processing time), start_time (actual/estimated start time), " \
                                "and delivery_time (actual delivery time). " \
                                "The 'machine' variable contains machine-related data such as available_time (machine's next available time), " \
                                "num_neighboring_operation (number of processable operations), and utilization (machine utilization rate [0-1]). " \
                                "The 'J-M Arc' variable reprensents the association of a job with a device, including processing_tm (actual processing time on machine). " \
                                "The output 'priority' stores numerical priority values where lower values indicate higher priority."
        self.prompt_other_inf = "All input variables may have a value of zero. Therefore, when division occurs, you need to determine whether the divisor is 0 or not. " \
                                "The generated code needs to be ensured that there are no syntax errors, invalid syntax and logic errors. (For example, the output variable 'priority' needs to be defined before it can be used as an output in the return of the code.)"

    def get_task(self):
        return self.prompt_task

    def get_func_name(self):
        return self.prompt_func_name

    def get_func_inputs(self):
        return self.prompt_func_inputs

    def get_func_outputs(self):
        return self.prompt_func_outputs

    def get_inout_inf(self):
        return self.prompt_inout_inf

    def get_other_inf(self):
        return self.prompt_other_inf
