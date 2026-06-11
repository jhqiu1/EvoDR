import copy

import numpy as np
from evodr.task.optimization.online_fafsp.get_instance import load_data

# from machine_job_match import m_j_match
import pandas as pd

# Datas = load_data_1()  # 数据获取
# data = Datas[0]
from evodr.task.optimization.online_fafsp.state import State, m_j_match
from evodr.task.optimization.online_fafsp.heuristic import Method
import time
import cProfile

# from joblib import Parallel, delayed
import os


class Sched:
    def __init__(self, data, rule):
        self.state_result = (
            {}
        )  # 键：设备号；值：调度记录（#订单编号-任务编号-设备编号-物料编号-开始时间-结束时间）
        self.task_arrive = data.taskWOArriveS  # dict
        self.task_finish = data.taskWOFinishS  # dict
        self.job_order = data.jobWOOrder
        self.order_num = data.taskWONumber
        self.m_j_array, self.m_j_orig_dict = m_j_match(data)
        self.m_j_orig = np.vstack(list(self.m_j_orig_dict.values()))
        self.state_done = np.zeros((self.m_j_array.shape[0], 1), int)  # 作业是否被安排
        self.state_now_time = 0
        self.state_mask = np.ones((self.m_j_array.shape[0], 1), int)  # 是否满足约束
        self.task_level = data.orderTaskData  # 键：总装任务；值：list部装任务
        job_order = data.jobWOOrder
        # all_job = np.array(list(job_order.keys())).reshape(-1, 1)
        all_job = np.unique(self.m_j_orig[:, 1])
        self.state_is_finish_task = np.zeros(
            (all_job.shape[0], 3), dtype=object
        )  # 记录作业是否完成，是否到达
        self.state_is_finish_task[:, 0] = all_job.flatten()
        self.job_arrive = np.zeros((all_job.shape[0], 2), dtype=object)
        self.job_arrive[:, 0] = all_job.flatten()
        for i in range(self.job_arrive.shape[0]):
            job = self.job_arrive[i, 0]
            arrive_time = self.task_arrive[job]
            self.job_arrive[i, 1] = arrive_time
            if arrive_time == 0:  # 初始时刻到达
                self.state_is_finish_task[i, 2] = 1

        self.state_is_done_task = np.zeros(
            (all_job.shape[0], 2), dtype=object
        )  # 记录作业是否完成
        self.state_is_done_task[:, 0] = all_job.flatten()
        self.state_can_use_machine = data.allLineList  # 开始可用设备集合
        for machine in data.allLineList:
            self.state_result[machine] = []
        self.speed_info = (
            data.lineDataF.to_numpy()
        )  # Unnameed-物料编码-生产线-速率类型-速率
        self.order_info = (
            data.orderlDataF.to_numpy()
        )  # Unnamed-装配件编码-工单数量-工单编号-最早开工时间-需求时间-订单编码
        self.top_change_time = data.topMatChangeTime
        self.sub_change_time = data.secondMatChangeTime
        self.top_level_job = data.assemblyOrderList
        self.prod_speed = data.productSpeed
        self.data = data
        self.state = State(data)
        self.method = Method(data)
        self.rule = rule

        self.state_feature = np.zeros((self.m_j_array.shape[0], 9))
        self.m_j_orig = np.vstack(list(self.m_j_orig_dict.values()))

        for i in range(self.m_j_orig.shape[0]):
            machine = self.m_j_orig[i, 0]
            job = self.m_j_orig[i, 1]
            material = self.m_j_orig[i, 2]
            order_num = self.order_num[job]
            speed = self.prod_speed[machine][int(material)]
            need_time = order_num * speed
            self.state_feature[i, [3, 4, 7, 8]] = [
                self.task_arrive[job],
                self.task_finish[job],
                1,
                need_time,
            ]
        a = 111

    def cal_process_time(self, index):
        info = self.m_j_orig_dict[index]
        machine = info[0]
        job = info[1]
        material = info[2]
        speed = self.prod_speed[machine][int(material)]
        order = self.job_order[job]
        idx1 = np.where(self.order_info[:, 6] == order)[0]
        order_num = self.order_num[job]
        need_time = order_num * speed
        m_schedule = self.state_result[
            machine
        ]  # 订单编号-任务编号-物料编号-开始时间-结束时间
        if not m_schedule:
            if job in self.top_level_job:
                change_time = self.top_change_time
            else:
                change_time = self.sub_change_time
        else:
            last_sche = m_schedule[-1]
            if last_sche[3] != material:
                # 判断作业层级
                if job in self.top_level_job:
                    change_time = self.top_change_time
                else:
                    change_time = self.sub_change_time
            else:
                change_time = 0

        deliv_time = self.state_now_time + need_time + change_time
        start_time = self.state_now_time + change_time

        return need_time, deliv_time, order, job, machine, material, start_time

    def cal_fitness(self):
        order_list = self.data.orderList
        order_delivery = self.data.orderPDeliveryTime
        all_lists = [
            s_list for s_lists in self.state_result.values() for s_list in s_lists
        ]
        sche_result = np.array(all_lists)
        delays = 0
        sche_result[:, 4] = sche_result[:, 4].astype(int)
        sche_result[:, 5] = sche_result[:, 5].astype(int)
        for order_no in order_list:
            s_index = sche_result[:, 0] == order_no
            o_sche = sche_result[s_index]
            end_time = np.max(o_sche[:, 5].astype(int))
            order_time = order_delivery[order_no]
            # delays = delays + abs(end_time - order_time)
            if end_time > order_time:
                delays = delays + (end_time - order_time)
        delay = delays / 60
        # print(f"当前总拖期为{delay}mintues")
        # generate_gantt_chart(sche_result)
        return delay

    def cal_cmax(self):
        all_lists = [
            s_list for s_lists in self.state_result.values() for s_list in s_lists
        ]
        sche_result = np.array(all_lists)
        cmax = max(sche_result[:, 5].astype(int))
        return cmax

    def schedule(self, code):
        start = time.time()
        order_delivery = self.data.orderPDeliveryTime
        count = 0
        count1 = {}
        sum = 0
        # feature = self.state.get_feature_1(self.state_result, self.state_done, self.state_mask, self.state_is_finish_task, self.state_can_use_machine, self.state_feature)

        assembly_mask = np.ones((self.state_mask.shape[0], 1), int)
        idx = np.isin(self.m_j_orig[:, 1], self.top_level_job)
        assembly_mask[idx] = 0  # 总装件的上下层约束
        # first_job = []
        # for key, values in self.data.orderTaskData.items():
        #     f_job = values[0]
        #     first_job.append(f_job)
        # idx = np.isin(self.m_j_orig[:, 1], first_job)
        # assembly_mask[idx] = 1  #总装件、紧前紧后工序的上下层约束

        while np.any(self.state_done == 0):
            count += 1
            # print(count)
            count1[count] = 0
            do_num = (self.state_is_done_task[:, 1] == 1).sum()

            while True:
                count1[count] += 1
                # print(count1[count])
                self.state_mask = self.state.constraints_check(
                    self.state_done,
                    self.state_mask,
                    self.state_is_finish_task,
                    self.state_can_use_machine,
                    self.state_now_time,
                    assembly_mask,
                )
                if np.sum(self.state_mask) == 0:
                    a = 111
                temp_done = copy.deepcopy(
                    self.state_done
                )  # 表示当前状态下M-J配对的处理情况
                # idx2 = np.where(self.state_mask == 0)[0]  # 违反约束配对
                idx2 = np.flatnonzero(self.state_mask == 0)
                temp_done[idx2] = 1  # 将违反约束的视为已处理
                if len(self.state_can_use_machine) == 0 or np.all(
                    temp_done == 1
                ):  # 无可用设备或无可处理配对
                    break
                count1[count] += 1
                # if not (self.state_can_use_machine.shape[0] > 0 and np.any(temp_done == 0)):  # 存在可用设备且未完成所有配对关系处理
                #     break

                min_ddl_index = -1

                # 根据不同规则选择加工任务
                if self.rule == "LLM":
                    self.state_feature = self.state.get_feature_1(
                        self.state_result,
                        self.state_done,
                        self.state_mask,
                        self.state_is_finish_task,
                        self.state_can_use_machine,
                        self.state_feature,
                    )
                    min_ddl_index = self.method.llm(
                        self.state_mask,
                        self.state_done,
                        self.state_result,
                        code,
                        self.state_now_time,
                        self.state_feature,
                    )
                    # print(count1[count], min_ddl_index, self.m_j_orig_dict[min_ddl_index]['machine'])
                elif self.rule == "EDD":
                    min_ddl_index = self.method.edd(self.state_mask, self.state_done)
                elif self.rule == "FIFO+SPT":
                    min_ddl_index = self.method.fifo_spt(
                        self.state_mask, self.state_done
                    )
                elif self.rule == "FIFO+EET":
                    min_ddl_index = self.method.fifo_eet(
                        self.state_mask, self.state_done, self.state_result
                    )
                elif self.rule == "MOPNR+SPT":
                    min_ddl_index = self.method.mopnr_spt(
                        self.state_mask, self.state_done, self.state_is_finish_task
                    )
                elif self.rule == "MOPNR+EET":
                    min_ddl_index = self.method.mopnr_eet(
                        self.state_mask,
                        self.state_done,
                        self.state_is_finish_task,
                        self.state_result,
                    )
                elif self.rule == "LWKR+SPT":
                    min_ddl_index = self.method.lwkr_spt(
                        self.state_mask,
                        self.state_done,
                        self.state_is_finish_task,
                        self.state_result,
                    )
                elif self.rule == "LWKR+EET":
                    min_ddl_index = self.method.lwkr_eet(
                        self.state_mask,
                        self.state_done,
                        self.state_is_finish_task,
                        self.state_result,
                    )
                elif self.rule == "MWKR+SPT":
                    min_ddl_index = self.method.mwkr_spt(
                        self.state_mask,
                        self.state_done,
                        self.state_is_finish_task,
                        self.state_result,
                    )
                elif self.rule == "MWKR+EET":
                    min_ddl_index = self.method.mwkr_eet(
                        self.state_mask,
                        self.state_done,
                        self.state_is_finish_task,
                        self.state_result,
                    )
                elif self.rule == "RAND":
                    min_ddl_index = self.method.random(self.state_mask, self.state_done)
                elif self.rule == "GP" or self.rule == "GEP":
                    min_ddl_index = self.method.gp(
                        self.state_mask,
                        self.state_done,
                        self.state_result,
                        code,
                        self.state_now_time,
                    )
                # 生产时间计算
                if min_ddl_index != -1:
                    (
                        process_time,
                        md_end_time,
                        md_order,
                        md_job,
                        md_machine,
                        md_material,
                        start_time,
                    ) = self.cal_process_time(min_ddl_index)

                    (
                        self.state_done,
                        self.state_mask,
                        self.state_result,
                        self.state_can_use_machine,
                        self.state_is_done_task,
                    ) = self.state.arrange_job(
                        min_ddl_index,
                        md_order,
                        md_job,
                        md_machine,
                        md_material,
                        md_end_time,
                        self.state_done,
                        self.state_mask,
                        self.state_result,
                        self.state_now_time,
                        self.state_can_use_machine,
                        self.state_is_done_task,
                        start_time,
                    )
                    temp_done[min_ddl_index] = 1
                    self.state_feature = self.state.get_feature_2(
                        self.state_result,
                        self.state_done,
                        self.state_mask,
                        self.state_is_finish_task,
                        self.state_can_use_machine,
                        self.state_feature,
                        min_ddl_index,
                    )
                    # feature = self.state.modify_feature(min_ddl_index, self.state_result, self.state_can_use_machine, feature)
                else:
                    # print("代码错误导致索引为-1")
                    delay = float("inf")
                    return delay
            # 状态更新
            (
                self.state_now_time,
                self.state_can_use_machine,
                self.state_mask,
                self.state_is_finish_task,
                assembly_mask,
            ) = self.state.push_state(
                self.state_result,
                self.state_is_finish_task,
                self.state_now_time,
                self.state_is_done_task,
                self.job_arrive,
                assembly_mask,
            )

        total = 0
        for value in count1.values():
            total += value
        delay = self.cal_fitness()
        # c_max = self.cal_cmax()
        end_time = time.time()
        elapsed_time = end_time - start
        print(f"耗时: {elapsed_time:.6f} 秒")
        print(self.data.xlsx_file, delay)
        return delay


if __name__ == "__main__":
    #     code = '''def cal_priority(status, num_neighboring_machine, processing_time, start_time, delivery_time, available_time, num_neighboring_operation, utilization, processing_tm):
    #     urgency_weight = 1.0 - utilization
    #     efficiency_weight = utilization
    #     result = urgency_weight * delivery_time + efficiency_weight * processing_tm
    #     return result
    # '''
    code = """
def cal_priority(status: int, num_neighboring_machine: int, processing_time: float, start_time: float, delivery_time: float, available_time: float, num_neighboring_operation: int, utilization: float, processing_tm: float) -> float:
    effective_start = max(start_time, available_time)
    slack = delivery_time - effective_start - processing_time

    # Base priority from due date
    priority = delivery_time

    # Exponential tardiness penalty: heavy exponential decrease for late jobs
    if slack < 0:
        # Exponential penalty: -C * exp(-slack/tau) with tau scaled to processing time
        tau = max(processing_tm, 1.0)
        priority -= 500.0 * (2.0 ** (-slack / tau) - 1.0)
    else:
        # Mild increase for early jobs
        priority += 0.1 * slack

    # Machine availability penalty
    priority += 0.05 * available_time

    # Processing time penalty
    priority += 0.2 * processing_tm

    # Nonlinear bottleneck utilization: quadratic penalty for high utilization
    priority += 30.0 * (utilization ** 2)

    # Flexibility penalties
    priority += 0.03 * num_neighboring_machine * processing_tm
    priority += 0.03 * num_neighboring_operation * processing_tm

    # Stronger status boost for in-progress jobs
    if status == 1:
        priority -= 10000.0

    return float(priority)
    
    """

    # file = r'./data_test_cmax/' + txt
    # Datas = load_data_1(file)
    # delay = []
    # # folder_path = 'D:/study_1/002maincode/data_test_cmax'
    # folder_path = 'D:/study_1/002maincode/data_test'
    # all_files = os.listdir(folder_path)
    # txt_files = [file for file in all_files if file.endswith('.txt')]  # 文件名获取
    #
    # def process_data(data_idx, Datas, rules, arrive_num, u):
    #     row = {}
    #     time_info = {}
    #     data = Datas[data_idx]
    #     for rule in rules:
    #         print(f'数据{data_idx}，当前规则为{rule}')
    #         start_time = time.time()
    #         sched = Sched(data, rule)
    #         delay = sched.schedule(code=code)
    #         end_time = time.time()
    #         elapsed_time = end_time - start_time
    #         row[rule] = delay
    #     return (data_idx, row)
    #
    # all_result = {}
    # rules = ['LLM']
    # for txt in txt_files:
    #     # file = r'./data_test_cmax/' + txt
    #     file = r'./data_test/' + txt
    #     Datas = load_data_1(file)
    #     arrive_num, machine_num, u = map(int, txt.replace('.txt', '').split('-'))
    #     results = Parallel(n_jobs=-1)(delayed(process_data)(data_idx, Datas, rules, arrive_num, u) for data_idx in range(20))
    #     results_df = pd.DataFrame(index=range(20), columns=rules)
    #     for data_idx, row in results:
    #         results_df.loc[data_idx] = row
    #     output_path = "scheduling_results_allLLM_cmax2.xlsx"  # 输出文件名
    #     data = Datas[0]
    #     sched = Sched(data, 'LLM')
    #     sched.schedule(code)
    #
    #     averages = results_df.mean(axis=0)  # 计算所有列的平均值
    #     results_df.loc['Average'] = averages
    #     all_result[txt] = results_df
    #     with pd.ExcelWriter(output_path) as writer:
    #         for sheet_name, df in all_result.items():
    #             df.to_excel(writer, sheet_name=sheet_name, index=True)

    # txt = 'm15-m212-f0.7-arrive50-u4.txt'
    txt = "m13-m26-f0.5-arrive20-u1.txt"
    # txt = '100-20-4.txt'
    # file = r"./data_test/" + txt
    Datas = load_data(txt)
    # data = Datas[0]
    results = []
    for key, data in Datas.items():
        sched = Sched(data, "LLM")
        result = sched.schedule(code)
        results.append(result)
    print(np.mean(results))

    a = 111
    # cProfile.run('my_function()')
