import numpy as np
from collections import defaultdict
import time
from numba import njit, prange

# @njit(parallel=True)
# def parallel_multiply(a, b):
#     result = np.empty_like(a)
#     for i in prange(a.size):  # 对多维数组也适用
#         result.flat[i] = a.flat[i] * b.flat[i]
#     return result


def m_j_match(data):  # 构建设备-任务对
    machine = data.allLineList
    machine_num = np.arange(len(machine))
    job_order = data.jobWOOrder
    all_job = job_order.keys()

    # 构建 设备-任务矩阵
    n_machines = len(machine)
    n_jobs = len(all_job)
    m_j_array = np.zeros((len(machine) * len(all_job), 2), int)
    for i in range(n_machines):
        start_row = i * n_jobs
        end_row = start_row + n_jobs
        m_j_array[start_row:end_row, 0] = machine_num[i]
        m_j_array[start_row:end_row, 1] = np.arange(n_jobs)

    # 执行机器资质校验
    machine_qualify = data.productSpeed
    task_material = data.taskWOMaterial
    temp_mask = np.zeros((len(machine) * len(all_job), 1))
    for i in range(m_j_array.shape[0]):
        m_n = m_j_array[i][0]
        j_n = m_j_array[i][1]
        m_n_orig = machine[m_n]
        m_canuse_j = machine_qualify[m_n_orig].keys()
        j_n_orig = list(all_job)[j_n]
        j_n_material = task_material[j_n_orig]
        if j_n_material in m_canuse_j:
            temp_mask[i] = 1
    # 根据机器资质剔除非法配对
    mask = temp_mask.astype(bool).flatten()
    m_j_array = m_j_array[mask]

    # 构建初始信息对应字典
    m_j_orig_dict = {}  # 键-矩阵行；值：设备-任务-对应物料
    for i in range(m_j_array.shape[0]):
        m_n = m_j_array[i][0]
        j_n = m_j_array[i][1]
        m_n_orig = machine[m_n]
        j_n_orig = list(all_job)[j_n]
        j_n_material = task_material[j_n_orig]
        matrix = np.array([m_n_orig, j_n_orig, j_n_material])
        m_j_orig_dict[i] = matrix

    return m_j_array, m_j_orig_dict


class State:  # 该类用于更新状态变量
    def __init__(self, data):
        job_order = data.jobWOOrder
        self.m_j_array, self.m_j_orig_dict = m_j_match(data)
        self.task_arrive = data.taskWOArriveS
        self.task_level = data.orderTaskData
        self.order_num = data.taskWONumber
        # self.sched = Sched()
        self.top_change_time = data.topMatChangeTime
        self.sub_change_time = data.secondMatChangeTime
        self.top_level_job = data.assemblyOrderList
        self.speed_info = (
            data.lineDataF.to_numpy()
        )  # Unnameed-物料编码-生产线-速率类型-速率
        self.order_info = (
            data.orderlDataF.to_numpy()
        )  # Unnamed-装配件编码-工单数量-工单编号-最早开工时间-需求时间-订单编码
        self.prod_speed = data.productSpeed
        self.job_order = data.jobWOOrder
        self.job_deliveay = data.taskWOFinishS
        self.m_j_orig = np.vstack(list(self.m_j_orig_dict.values()))
        new_array = np.zeros((self.m_j_orig.shape[0], 1), int)
        for key, values in self.task_arrive.items():
            idx = self.m_j_orig[:, 1] == key
            new_array[idx] = int(values)
        self.m_j_orig = np.hstack((self.m_j_orig, new_array))
        # 构建任务设备矩阵，行索引为任务，列索引为设备
        self.all_jobs = np.unique(self.m_j_orig[:, 1])
        self.all_machines = np.unique(self.m_j_orig[:, 0])
        speed_array = np.zeros(
            (self.all_jobs.shape[0], self.all_machines.shape[0]), int
        )
        quality_array = np.zeros(
            (self.all_jobs.shape[0], self.all_machines.shape[0]), int
        )
        speed_array_all = np.zeros(
            (self.m_j_array.shape[0], self.all_machines.shape[0]), int
        )
        quailty_array_all = np.zeros(
            (self.m_j_array.shape[0], self.all_machines.shape[0]), int
        )
        oper_array_all = np.zeros(
            (self.m_j_array.shape[0], self.all_jobs.shape[0]), int
        )
        job_to_mat = {
            job: self.m_j_orig[self.m_j_orig[:, 1] == job, 2][0]  # 取第一个material
            for job in self.all_jobs
        }
        # for job in self.all_jobs:
        #     job_mat = job_to_mat[job]
        #     for machine, speeds in self.prod_speed.items():
        #         for mat, speed in speeds.items():
        #             if mat == int(job_mat):
        #                 speed_array[self.all_jobs == job, self.all_machines == machine] = speed
        #                 quality_array[self.all_jobs == job, self.all_machines == machine] = 1
        # self.speed_array = speed_array
        # self.quality_array = quality_array
        for i in range(self.m_j_orig.shape[0]):
            machine = self.m_j_orig[i, 0]
            job = self.m_j_orig[i, 1]
            material = self.m_j_orig[i, 2].astype(int)
            arrive_time = self.m_j_orig[i, 3].astype(int)
            for mac, speeds in self.prod_speed.items():
                for mat, speed in speeds.items():
                    if mat == material:
                        speed_array_all[i, self.all_machines == mac] = speed
                        quailty_array_all[i, self.all_machines == mac] = 1
            idx = self.m_j_orig[:, 0] == machine
            can_job = self.m_j_orig[idx, 1]
            oper_array_all[i, np.isin(self.all_jobs, can_job)] = 1

        self.speed_array_all = speed_array_all
        self.quailty_array_all = quailty_array_all
        self.oper_array_all = oper_array_all

        self.assembly_job = data.assemblyOrderList  # 所有总装工件集合
        self.sub_job = data.subassemblyOrderList
        # 构建部装，总装对应关系矩阵
        sub_assembly_array = np.zeros((len(self.sub_job), len(self.assembly_job)), int)
        for job_idx in range(len(self.assembly_job)):
            assembly_job = self.assembly_job[job_idx]
            sub_job = self.task_level[assembly_job]
            indices = [self.sub_job.index(x) for x in sub_job if x in self.sub_job]
            sub_assembly_array[indices, job_idx] = 1
        self.sub_assembly_array = sub_assembly_array

        a = 111

    def push_state(
        self,
        result,
        is_finish_task,
        input_time,
        is_done_task,
        job_arrive,
        assembly_mask,
    ):  # 状态数据更新
        machine_endtime = float("inf")
        m_1 = 0
        for key, value in result.items():
            if not value:  # 初始时刻未调度的设备排除
                continue
            end_sche = value[-1]
            end_time = int(end_sche[5])
            if end_time > input_time:  # 确保时间钟推进
                m_1 = 1
                machine_endtime = min(machine_endtime, end_time)
        # job_at = 999999999
        # if m_1 == 0: #此时跳转到下个未被调度任务的到达时间
        #     no_done_job = is_done_task[np.where(is_done_task[:, 1] == 0)[0], 0]
        #     for job_ in no_done_job:
        #         arrive_time = int(self.task_arrive[job_])
        #         if arrive_time > input_time:
        #             job_at = min(arrive_time, job_at)

        job_at = float("inf")
        no_done_job = is_done_task[np.where(is_done_task[:, 1] == 0)[0], 0]
        for job_ in no_done_job:
            arrive_time = int(self.task_arrive[job_])
            if arrive_time > input_time:
                job_at = min(arrive_time, job_at)

        output_now = min(machine_endtime, job_at)
        # 更新状态变量信息
        mask = np.ones((self.m_j_array.shape[0], 1), int)  # 掩码矩阵更新
        # output_now = machine_endtime  # 当前时间更新
        self.now = output_now
        can_use_machine = []
        for key, value in result.items():
            if not value:  # 初始时刻未调度的设备排除
                # self.can_use_machine.append(key)
                can_use_machine = np.append(can_use_machine, key)
                continue
            end_sche = value[-1]
            end_time = int(end_sche[5])
            if end_time <= output_now:  # 任务完工状态更新
                temp_job = end_sche[1]
                idx = np.where(is_finish_task[:, 0] == temp_job)
                is_finish_task[idx, 1] = 1
                can_use_machine = np.append(can_use_machine, key)
                if temp_job in self.sub_job:
                    idx1 = self.sub_job.index(temp_job)
                    assembly_row = self.sub_assembly_array[idx1]
                    assembly_job = self.assembly_job
                    a_job = np.array(assembly_job)[assembly_row == 1][0]
                    sub_jobs = self.task_level[a_job]
                    is_finish = is_finish_task[
                        np.isin(is_finish_task[:, 0], sub_jobs), 1
                    ]
                    # index = sub_jobs.index(temp_job)
                    # if index + 1 < len(sub_jobs):  #紧后工序释放
                    #     next_job = sub_jobs[index + 1]
                    #     idx_n_job = self.m_j_orig[:, 1] == next_job
                    #     assembly_mask[idx_n_job] = 1
                    if np.all(is_finish.astype(int) == 1):  # 此时所有下层工序完成
                        idx_a_job = self.m_j_orig[:, 1] == a_job
                        assembly_mask[idx_a_job] = 1

        # 找出已到达的所有工件
        arrive_mask = job_arrive[:, 1] <= output_now
        is_finish_task[arrive_mask, 2] = 1
        return output_now, can_use_machine, mask, is_finish_task, assembly_mask

    def arrange_job(
        self,
        index,
        order,
        job,
        machine,
        material,
        end_time,
        done,
        mask,
        result,
        now_time,
        can_use_machine,
        is_done_task,
        start_time,
    ):  # 将任务记录到相应的设备上
        sched = result[machine]
        new_row = [order, job, machine, material, start_time, end_time]
        sched.append(new_row)
        result[machine] = sched
        # self.can_use_machine.remove(machine)   #可用设备更新
        can_use_machine = can_use_machine[can_use_machine != machine]
        done[index] = 1
        j_no = np.where(self.m_j_array[:, 1] == self.m_j_array[index, 1])[0]
        done[j_no] = 1  # 将同任务在其余设备的边剔除
        mask[j_no] = 1
        is_done_task[np.where(is_done_task[:, 0] == job)[0], 1] = 1

        return done, mask, result, can_use_machine, is_done_task

    def constraints_check(
        self, done, mask, is_finish_task, can_use_machine, now_time, assembly_mask
    ):  # 进行当前状态时刻的约束校验
        time_array = np.ones((self.m_j_orig.shape[0], 1), int)
        machine_array = np.ones((self.m_j_orig.shape[0], 1), int)
        idx = self.m_j_orig[:, 3].astype(int) > now_time
        time_array[idx] = 0  # 到达时间不符合
        idx1 = ~np.isin(self.m_j_orig[:, 0], can_use_machine)
        machine_array[idx1] = 0
        # 加工阶段判断任务前后关系
        mask = (1 - done) * machine_array * time_array * assembly_mask

        # 判断下层工件是否完工
        # 找出所有未完成的上层工件集合
        no_finish_top_job_mask = np.isin(is_finish_task[:, 0], self.assembly_job) & (
            is_finish_task[:, 1] == 0
        )
        no_finish_top_job = is_finish_task[no_finish_top_job_mask, 0]

        # for i in range(self.m_j_array.shape[0]):
        #     if done[i] == 1:
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #
        #     # 判断当前时刻设备是否可用
        #     if machine not in can_use_machine:
        #         mask[i] = 0
        #         continue
        #
        #     job = info[1]
        #     material = info[2]
        #     arrive_time = self.task_arrive[job]
        #
        #     # 任务到达时间判断
        #     if arrive_time > now_time:
        #         mask[i] = 0
        #         continue

        # 判断下层任务是否完工
        # flag = 0
        # if job in self.task_level.keys():
        #     sub_job = self.task_level[job]
        #     for ind in sub_job:
        #         idx = np.where(is_finish_task[:, 0] == ind)[0]
        #         if is_finish_task[idx, 1] == 0:  # 下层任务未完工
        #             mask[i] = 0
        #             flag = 1
        #             break
        #     if flag == 1:
        #         continue

        return mask

    def cal_process_time(self, index, result, now_time):
        info = self.m_j_orig_dict[index]
        machine = info[0]
        job = info[1]
        material = info[2]
        speed = self.prod_speed[machine][int(material)]
        order = self.job_order[job]
        idx1 = np.where(self.order_info[:, 6] == order)[0]
        order_num = self.order_num[job]
        need_time = order_num * speed
        m_schedule = result[machine]  # 订单编号-任务编号-物料编号-开始时间-结束时间
        if not m_schedule:
            change_time = 0
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

        deliv_time = now_time + need_time + change_time

        return need_time, deliv_time, order, job, machine, material

    # def get_feature(self, result, done, mask, now_time):  # 更新配对特征
    #     # 任务：状态-相邻机器数量-处理时间-开始时间-交付时间[作业中未调度的操作数量-作业完成时间]
    #     # 设备：可用时间-相邻操作数量-利用率-
    #     # 边：处理时间
    #     self.j_feature = []
    #     self.m_feature = []
    #     self.e_feature = []
    #     m_j_array = self.m_j_array
    #     all_lists = [s_list for s_lists in result.values() for s_list in s_lists]  # 订单编号-任务编号-设备编号-物料编号-开始时间-结束时间
    #     sche_result = np.array(all_lists)
    #     temp_done = 1 - done
    #     new_mask = mask * temp_done
    #
    #     # 循环外计算：任务平均处理时间，任务相邻机器数量，设备利用率，设备最早可用时间，设备的相邻操作数量
    #
    #     for i in range(m_j_array.shape[0]):
    #         if new_mask[i] == 0:
    #             self.j_feature.append([-1, -1, -1, -1, -1])
    #             self.m_feature.append([-1, -1, -1])
    #             self.e_feature.append([-1])
    #             continue
    #         info = self.m_j_orig_dict[i]
    #         machine = info[0][0]
    #         job = info[0][1]
    #         material = info[0][2]
    #         # 特征获取
    #         j_dt = self.job_deliveay[job]
    #         if not all_lists:
    #             j_status = 0
    #         else:
    #             # s_list = [sublist for sublist in all_lists if sublist[1] == job]
    #             # all_lists_array = np.array(all_lists)
    #             job_mask = sche_result[:, 1] == job
    #             s_list = sche_result[job_mask]
    #             if not s_list:
    #                 j_status = 0
    #             else:
    #                 j_status = 1
    #         j_num_machine = np.sum(new_mask[np.where(m_j_array[:, 1] == m_j_array[i, 1])[0]])
    #         m_scheme = result[machine]
    #         if j_status == 1:
    #             # s_list = [sublist for sublist in all_lists if sublist[1] == job]
    #             # all_lists_array = np.array(all_lists)
    #             job_mask = sche_result[:, 1] == job
    #             s_list = sche_result[job_mask]
    #             j_pt = int(s_list[0][5]) - int(s_list[0][4])
    #             j_st = int(s_list[0][4])
    #         else:
    #             j_pt_t = 0
    #             for inx in np.where(m_j_array[:, 1] == m_j_array[i, 1])[0]:
    #                 pt = self.cal_process_time(inx, result, now_time)[0]
    #                 j_pt_t = j_pt_t + pt
    #             j_pt = j_pt_t / np.where(m_j_array[:, 1] == m_j_array[i, 1])[0].shape[0]
    #             if not m_scheme:
    #                 j_st = 0
    #             else:
    #                 last_scheme = m_scheme[-1]
    #                 if material != last_scheme[3]:
    #                     if job in self.top_level_job:
    #                         change_time = self.top_change_time
    #                     else:
    #                         change_time = self.sub_change_time
    #                     j_st = last_scheme[5] + change_time
    #                 else:
    #                     j_st = last_scheme[5]
    #         if not m_scheme:
    #             m_util = 0
    #             m_at = 0
    #         else:
    #             pt = 0
    #             last_scheme = m_scheme[-1]
    #             m_at = last_scheme[-1]
    #             m_array = np.array(m_scheme)
    #             # for s_ in m_scheme:
    #             #     pt = pt + s_[-1] - s_[-2]
    #             pt = np.sum(m_array[:, -1].astype(int) - m_array[:, -2].astype(int))
    #             m_util = pt / m_at
    #
    #         m_op_num = np.sum(new_mask[np.where(m_j_array[:, 0] == m_j_array[i, 0])[0]])
    #
    #         e_pt = self.cal_process_time(i, result, now_time)[0]
    #
    #         self.j_feature.append([j_status, j_num_machine, j_pt, j_st, j_dt])
    #         self.m_feature.append([m_at, m_op_num, m_util])
    #         self.e_feature.append([e_pt])
    #
    #         j_feature = np.array(self.j_feature)
    #         m_feature = np.array(self.m_feature)
    #         e_feature = np.array(self.e_feature)
    #
    #     return self.j_feature, self.m_feature, self.e_feature

    def get_feature(self, result, done, mask):  # 更新配对特征
        # 任务：状态-相邻机器数量-处理时间-开始时间-交付时间[作业中未调度的操作数量-作业完成时间]
        # 设备：可用时间-相邻操作数量-利用率-
        # 边：处理时间

        ## **********************####
        m_j_orig = self.m_j_orig
        m_j_array = self.m_j_array
        j_feature = np.zeros((m_j_array.shape[0], 5))
        m_feature = np.zeros((m_j_array.shape[0], 3))
        e_feature = np.zeros((m_j_array.shape[0], 1))
        all_machine = np.unique(m_j_orig[:, 0])
        all_job = np.unique(m_j_orig[:, 1])
        all_material = np.unique(m_j_orig[:, 2]).astype(int)
        all_lists = [
            s_list for s_lists in result.values() for s_list in s_lists
        ]  # 订单编号-任务编号-设备编号-物料编号-开始时间-结束时间
        sche_result = np.array(all_lists)
        temp_done = 1 - done
        new_mask = mask * temp_done

        # 循环外计算：任务平均处理时间，任务相邻机器数量，设备利用率，设备最早可用时间，设备的相邻操作数量
        j_avg_pt_dict = {}
        j_machine_num_dict = {}
        m_util_dict = {}
        m_st_dict = {}
        m_j_num_dict = {}
        m_j_orig = self.m_j_orig
        for j in all_job:
            j_idx = np.where(m_j_orig[:, 1] == j)[0]
            j_no = m_j_array[j_idx[0], 1]
            j_num_machine = np.sum(new_mask[np.where(m_j_array[:, 1] == j_no)[0]])
            j_machine_num_dict[j] = j_num_machine  # 任务相邻机器数量
            machine_list = m_j_orig[j_idx, 0]
            material = m_j_orig[j_idx[0], 2]
            # pt = 0
            # for m in machine_list:
            #     speed = self.prod_speed[m][int(material)]
            #     order_num = self.order_num[j]
            #     pt += speed * order_num
            # pt_avg = pt / machine_list.shape[0]
            speeds = np.array([self.prod_speed[m][int(material)] for m in machine_list])
            pt_avg = np.mean(speeds) * self.order_num[j]
            j_avg_pt_dict[j] = pt_avg

        for m in all_machine:
            m_scheme = result[m]
            if not m_scheme:
                m_at = 0
                m_util = 0
            else:
                last_scheme = m_scheme[-1]
                m_at = last_scheme[-1]
                m_array = np.array(m_scheme)
                pt = np.sum(m_array[:, -1].astype(int) - m_array[:, -2].astype(int))
                m_util = pt / m_at
            m_st_dict[m] = m_at
            m_util_dict[m] = m_util

            m_idx = np.where(m_j_orig[:, 0] == m)[0]
            m_no = m_j_array[m_idx[0], 0]
            m_num_job = np.sum(new_mask[np.where(m_j_array[:, 0] == m_no)[0]])
            m_j_num_dict[m] = m_num_job

        for i in range(m_j_array.shape[0]):
            if new_mask[i] == 0:
                j_feature[i, :] = -1
                m_feature[i, :] = -1
                e_feature[i, :] = -1
                # j_feature.append([-1, -1, -1, -1, -1])
                # m_feature.append([-1, -1, -1])
                # e_feature.append([-1])
                continue
            info = self.m_j_orig_dict[i]
            machine = info[0]
            job = info[1]
            material = info[2]
            # 特征获取
            j_dt = self.job_deliveay[job]
            if not all_lists:
                j_status = 0
            else:
                # s_list = [sublist for sublist in all_lists if sublist[1] == job]
                # all_lists_array = np.array(all_lists)
                job_mask = sche_result[:, 1] == job
                s_list = sche_result[job_mask]
                if not s_list:
                    j_status = 0
                else:
                    j_status = 1
            j_num_machine = j_machine_num_dict[job]
            # j_num_machine = np.sum(new_mask[np.where(m_j_array[:, 1] == m_j_array[i, 1])[0]])
            m_scheme = result[machine]
            if j_status == 1:
                # s_list = [sublist for sublist in all_lists if sublist[1] == job]
                # all_lists_array = np.array(all_lists)
                job_mask = sche_result[:, 1] == job
                s_list = sche_result[job_mask]
                j_pt = int(s_list[0][5]) - int(s_list[0][4])
                # j_st = int(s_list[0][4])
            else:
                j_pt = j_avg_pt_dict[job]
                # if not m_scheme:
                #     j_st = 0
                # else:
                #     last_scheme = m_scheme[-1]
                #     if material != last_scheme[3]:
                #         if job in self.top_level_job:
                #             change_time = self.top_change_time
                #         else:
                #             change_time = self.sub_change_time
                #         j_st = last_scheme[5] + change_time
                #     else:
                #         j_st = last_scheme[5]
            j_st = self.task_arrive[job]
            if not m_scheme:
                m_util = 0
                m_at = 0
            else:
                m_util = m_util_dict[machine]
                m_at = m_st_dict[machine]

            m_util = 1

            # m_op_num = np.sum(new_mask[np.where(m_j_array[:, 0] == m_j_array[i, 0])[0]])
            m_op_num = m_j_num_dict[machine]
            order_num = self.order_num[job]
            speed = self.prod_speed[machine][int(material)]
            need_time = order_num * speed
            e_pt = speed * need_time

            j_feature[i] = [j_status, j_num_machine, j_pt, j_st, j_dt]
            m_feature[i] = [m_at, m_op_num, m_util]
            e_feature[i] = e_pt
            # j_feature.append([j_status, j_num_machine, j_pt, j_st, j_dt])
            # m_feature.append([m_at, m_op_num, m_util])
            # e_feature.append([e_pt])
        combined_matrix = np.hstack((j_feature, m_feature, e_feature))

        return combined_matrix
        # return j_feature, m_feature, e_feature

    def get_feature_1(
        self, result, done, mask, is_finish_task, can_use_machine, feature, feature_mask=None
    ):
        # 特征的3，4，7，8列已固定

        m_j_orig = self.m_j_orig
        m_j_array = self.m_j_array

        all_machine = np.unique(m_j_orig[:, 0])
        all_lists = [
            s_list for s_lists in result.values() for s_list in s_lists
        ]  # 订单编号-任务编号-设备编号-物料编号-开始时间-结束时间
        sche_result = np.array(all_lists)
        temp_done = 1 - done

        speed_array_all = self.speed_array_all
        quailty_array_all = self.quailty_array_all
        oper_array_all = self.oper_array_all

        # 计算相邻机器数量
        j_mchine_num = np.sum(
            quailty_array_all[:, np.isin(all_machine, can_use_machine)], axis=1
        )
        # 计算处理时间
        j_pt = np.zeros((m_j_orig.shape[0], 1))
        # 已排产任务
        if all_lists:
            # have_done_pt = sche_result[:, 5].astype(int) - sche_result[:, 4].astype(int)
            # a_dict = dict(zip(sche_result[:, 1], have_done_pt))
            mask = np.isin(m_j_orig[:, 1], sche_result[:, 1])
            # for key,values in a_dict.items():
            #     idx = m_j_orig[:, 1] == key
            #     j_pt[idx] = values
            # 未排产的任务
            j_pt[~mask] = np.mean(
                speed_array_all[~mask][:, np.isin(all_machine, can_use_machine)],
                axis=1,
                keepdims=True,
            )
        else:
            j_pt = np.mean(
                speed_array_all[:, np.isin(all_machine, can_use_machine)],
                axis=1,
                keepdims=True,
            )

        # 计算可用时间

        # 计算相邻操作数量
        arrive_mask = is_finish_task[:, 2].astype(int)
        oper_arr = oper_array_all * arrive_mask
        # oper_arr = parallel_multiply(oper_array_all, arrive_mask.astype(int))
        m_op = np.sum(oper_arr, axis=1)

        feature[:, 0] = done.flatten()
        feature[:, 1] = j_mchine_num
        feature[:, 2] = j_pt.flatten()

        feature[:, 6] = m_op

        # Apply feature mask for ablation (zero out disabled features)
        if feature_mask is not None:
            for i, active in enumerate(feature_mask):
                if not active:
                    feature[:, i] = 0

        return feature

    def get_feature_2(
        self, result, done, mask, is_finish_task, can_use_machine, feature, index, feature_mask=None
    ):
        # 这个方法对（任务：处理时间，第2列）（设备：可用时间，第5列）进行计算
        m_j_orig = self.m_j_orig
        use_job = m_j_orig[index, 1]
        use_machine = m_j_orig[index, 0]
        mscheme = np.array(result[use_machine])
        mscheme_last = result[use_machine][-1]
        j_pt = mscheme_last[5] - mscheme_last[4]  # 任务的处理时间
        m_ct = mscheme_last[5]  # 设备的可用时间
        j_mask = m_j_orig[:, 1] == use_job
        m_mask = m_j_orig[:, 0] == use_machine
        feature[j_mask, 2] = j_pt
        feature[m_mask, 5] = m_ct
        utilize = sum(mscheme[:, 5].astype(int) - mscheme[:, 4].astype(int)) / m_ct
        # 计算该设设备的利用率
        feature[m_mask, 7] = utilize

        # Apply feature mask for ablation (zero out disabled features)
        if feature_mask is not None:
            for i, active in enumerate(feature_mask):
                if not active:
                    feature[:, i] = 0

        return feature
