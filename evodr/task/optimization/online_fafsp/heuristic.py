import numpy as np
from evodr.task.optimization.online_fafsp.state import State, m_j_match
import traceback
import time


class Method:  # 该类用于选择优先级方法
    def __init__(self, data):
        a = 111
        self.m_j_array, self.m_j_orig_dict = m_j_match(data)
        self.top_change_time = data.topMatChangeTime
        self.sub_change_time = data.secondMatChangeTime
        self.top_level_job = data.assemblyOrderList
        self.prod_speed = data.productSpeed
        self.job_order = data.jobWOOrder  # 键：任务；值：数量
        self.order_info = data.taskWONumber
        self.order_delivery = data.orderPDeliveryTime
        self.order_arrive = data.taskWOArriveS
        self.order_data = (
            data.orderlDataF
        )  # umnamed-装配件编码-工单数量-最早开工时间-需求时间-订单编码
        self.order_level = data.orderTaskData
        self.job_material = data.taskWOMaterial  # 键：任务；值：物料
        self.line_info = data.lineDataF  # unnamed-物料编码-生产线-速率类型-速率
        self.state = State(data)
        self.all_machine = data.allLineList
        self.all_job = list(data.jobWOOrder.keys())
        self.m_j_orig = np.vstack(list(self.m_j_orig_dict.values()))
        order_array = np.zeros((self.m_j_orig.shape[0], 1))  # 到达时间
        at_array = np.zeros((self.m_j_orig.shape[0], 1), int)
        for key, values in self.order_arrive.items():
            idx = self.m_j_orig[:, 1] == key
            at_array[idx] = values
        self.m_j_orig = np.hstack((self.m_j_orig, at_array))
        pt_array = np.zeros((self.m_j_orig.shape[0], 1), int)
        for key, values in self.prod_speed.items():
            for s_key, s_value in values.items():
                idx = (self.m_j_orig[:, 0] == key) & (
                    self.m_j_orig[:, 2].astype(int) == s_key
                )
                pt_array[idx] = s_value
        self.m_j_orig = np.hstack((self.m_j_orig, pt_array))

    def edd(self, mask, done):  # edd规则
        ddl = float("inf")
        min_ddl_index = -1
        for i in range(self.m_j_array.shape[0]):
            if mask[i] == 0 or done[i] == 1:
                continue
            info = self.m_j_orig_dict[i]
            job = info[1]
            order = self.job_order[job]
            if self.order_delivery[order] < ddl:
                ddl = self.order_delivery[order]
                min_ddl_index = i

        return min_ddl_index

    def random(self, mask, done):  # 随机选择
        random_index = []
        temp_done = 1 - done
        new_mask = mask * temp_done
        indices = np.where(new_mask == 1)[0]
        if len(indices) > 0:
            random_index = np.random.choice(indices)
        else:
            print("没有为1的行")

        return random_index

    """
    作业排序
    FIFO（First In First Out，先进先出）​
    按作业到达顺序调度，优先处理先到达的作业。
    MOPNR（Most Operation Number Remaining，剩余最多操作数）​
    优先选择剩余未完成操作数最多的作业。
    LWKR（Least Work Remaining，剩余最少工作）​
    优先选择剩余总处理时间最短的作业。
    MWKR（Most Work Remaining，剩余最多工作）​
    优先选择剩余总处理时间最长的作业

    机器分配
    SPT（Shortest Processing Time，最短处理时间）​
    将作业分配到处理时间最短的可用机器上。
    EET（Earliest End Time，最早结束时间）​
    选择能够使作业最早完成的机器。

    FIFO+SPT
    FIFO+EET
    MOPNR+SPT
    MOPNR+EET
    LWKR+SPT
    LWKR+EET
    MWKR+SPT
    MWKR+EET
    """

    def fifo_spt(self, mask, done):
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        selected_rows = self.m_j_orig[idx_list]  # 选择 1804 行
        sort[idx_list, :] = selected_rows[:, [3, 4]].astype(int)
        # for i in idx_list:
        #     sort[i, 0] = self.m_j_orig[i, 3].astype(int)
        #     sort[i, 1] = self.m_j_orig[i, 4].astype(int)

        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     arrive_time = self.order_arrive[job]
        #     pt = self.prod_speed[machine][material]
        #     sort.append([arrive_time, pt])
        # sort = np.array(sort)
        # indices = np.arange(len(sort), dtype=int).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2]), 0] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def fifo_eet(self, mask, done, result):
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        end_time_dict = {}
        for key, values in result.items():
            if not values:
                end_time_dict[key] = 0
            else:
                end_time_dict[key] = values[-1][-1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            sort[i, 0] = self.m_j_orig[i, 3].astype(int)
            sort[i, 1] = end_time_dict[self.m_j_orig[i, 0]] + self.m_j_orig[
                i, 4
            ].astype(int)

        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break
        # sort = []
        # temp_done = 1 - done
        # new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     arrive_time = self.order_arrive[job]
        #     ps = self.prod_speed[machine][material]
        #     order_num = self.order_info[job]
        #     m_scheme = result[machine]
        #     if not m_scheme:
        #         change_time = 0
        #         end_time = 0
        #     else:
        #         last_scheme = m_scheme[-1]
        #         end_time = last_scheme[-1]
        #         change_time = 0
        #         if material != last_scheme[3]:
        #             if job in self.top_level_job:
        #                 change_time = self.top_change_time
        #             else:
        #                 change_time = self.sub_change_time
        #     pt = ps * order_num
        #     new_end_time = end_time + pt + change_time
        #     sort.append([arrive_time, new_end_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def mopnr_spt(self, mask, done, is_finish):
        # 先汇总出工单下的未完工任务数量
        order_no_finish_dict = {}
        all_order = self.order_data["订单编码"].drop_duplicates()
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            no_finish_num = 0
            for j in order_job:  # 找出相同工单下未完成的装配件数
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    no_finish_num += 1
            order_no_finish_dict[order] = no_finish_num
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_no_finish_dict[order_i]
            sort[i, 1] = self.m_j_orig[i, 4].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     pt = self.prod_speed[machine][material]
        #     order = self.job_order[job]
        #     order_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_num = 0
        #     for j in order_job:  # 找出相同工单下未完成的装配件数
        #         if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
        #             no_finish_num += 1
        #     sort.append([no_finish_num, pt])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def mopnr_eet(self, mask, done, is_finish, result):
        # MOPNR规则以订单为基准，计算订单下装配件的剩余数量
        end_time_dict = {}
        for key, values in result.items():
            if not values:
                end_time_dict[key] = 0
            else:
                end_time_dict[key] = values[-1][-1]

        order_no_finish_dict = {}
        all_order = self.order_data["订单编码"].drop_duplicates()
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            no_finish_num = 0
            for j in order_job:  # 找出相同工单下未完成的装配件数
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    no_finish_num += 1
            order_no_finish_dict[order] = no_finish_num
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_no_finish_dict[order_i]
            sort[i, 1] = end_time_dict[self.m_j_orig[i, 0]] + self.m_j_orig[
                i, 4
            ].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break
        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     order = self.job_order[job]
        #     order_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_num = 0
        #     for j in order_job:  # 找出相同工单下未完成的装配件数
        #         if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
        #             no_finish_num += 1
        #     ps = self.prod_speed[machine][material]
        #     order_num = self.order_info[job]
        #     m_scheme = result[machine]
        #     if not m_scheme:
        #         change_time = 0
        #         end_time = 0
        #     else:
        #         last_scheme = m_scheme[-1]
        #         end_time = last_scheme[-1]
        #         change_time = 0
        #         if material != last_scheme[3]:
        #             if job in self.top_level_job:
        #                 change_time = self.top_change_time
        #             else:
        #                 change_time = self.sub_change_time
        #     pt = ps * order_num
        #     new_end_time = end_time + pt + change_time
        #     sort.append([no_finish_num, new_end_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    # LWKR（Least Work Remaining，剩余最少工作）​
    # 优先选择剩余总处理时间最短的作业。
    def lwkr_spt(self, mask, done, is_finish, result):
        # LWKR规则以订单为基准，计算部装+总装的时间之和为处理时间，并取所有装配件处理时间最大值作为订单的总处理时间
        all_order = self.order_data["订单编码"].drop_duplicates()
        order_remain_time = {}
        m_j_orig = self.m_j_orig
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            flag = 0
            temp = []
            for j in order_job:
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    flag = 1
                    # 计算工件的平均加工时间
                    j_idx = np.where(m_j_orig[:, 1] == j)[0]
                    machine_list = m_j_orig[j_idx, 0]
                    material = m_j_orig[j_idx[0], 2]
                    speeds = np.array(
                        [self.prod_speed[m][int(material)] for m in machine_list]
                    )
                    pt_avg = np.mean(speeds)
                    temp.append(pt_avg)
            if not temp:
                order_remain_time[order] = 0
            else:
                order_remain_time[order] = sum(temp) / len(temp)
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_remain_time[order_i]
            sort[i, 1] = self.m_j_orig[i, 4].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        #
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     order = self.job_order[job]
        #     order_num = self.order_info[job]
        #     speed = self.prod_speed[machine][material]
        #     process_time = order_num * speed
        #     # 找出该订单下对应的未完成的总装任务
        #     order_final_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_final_job = []
        #     for j_ in order_final_job:
        #         if is_finish[np.where(is_finish[:, 0] == j_)[0], 1] == 0:
        #             no_finish_final_job.append(j_)
        #     all_pt = []  # 记录该订单下所有装配件的处理时间
        #     for j_1 in no_finish_final_job:  # 遍历每一个未完成的总装件
        #         no_finish_sub_job = []
        #         j_1_num = self.order_info[j_1]
        #         f_mat = self.job_material[j_1]
        #         # 计算总装件的加工时间
        #         f_can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == f_mat, '速率'].tolist()
        #         f_pt = sum(f_can_use_machine_speed) / len(f_can_use_machine_speed)
        #         sub_job = self.order_level[j_1]  # 所有部装件
        #         for s_j in sub_job:  # 遍历每一个未完成的部装件
        #             if is_finish[np.where(is_finish[:, 0] == s_j)[0], 1] == 0:
        #                 no_finish_sub_job.append(s_j)
        #         if not no_finish_sub_job:  # 该装配件下所有部件均已加工完成
        #             s_pt = 0
        #         else:
        #             pt_l = []  # 所有部件的加工时间记录
        #             for s_j_1 in no_finish_sub_job:
        #                 s_mat = self.job_material[s_j_1]  # 计算物料在所有设备上的平均加工时间
        #                 can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == s_mat, '速率'].tolist()
        #                 ps = sum(can_use_machine_speed) / len(can_use_machine_speed)
        #                 pt = j_1_num * ps
        #                 pt_l.append(pt)
        #             s_pt = max(pt_l)  # 取出所有部装工件加工时间最大值
        #         all_pt.append(f_pt + s_pt)
        #     max_pt = max(all_pt)  # 该任务对应订单的剩余总时间
        #     sort.append([max_pt, process_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def lwkr_eet(self, mask, done, is_finish, result):
        end_time_dict = {}
        for key, values in result.items():
            if not values:
                end_time_dict[key] = 0
            else:
                end_time_dict[key] = values[-1][-1]

        all_order = self.order_data["订单编码"].drop_duplicates()
        order_remain_time = {}
        m_j_orig = self.m_j_orig
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            flag = 0
            temp = []
            for j in order_job:
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    flag = 1
                    # 计算工件的平均加工时间
                    j_idx = np.where(m_j_orig[:, 1] == j)[0]
                    machine_list = m_j_orig[j_idx, 0]
                    material = m_j_orig[j_idx[0], 2]
                    speeds = np.array(
                        [self.prod_speed[m][int(material)] for m in machine_list]
                    )
                    pt_avg = np.mean(speeds)
                    temp.append(pt_avg)
            if not temp:
                order_remain_time[order] = 0
            else:
                order_remain_time[order] = sum(temp) / len(temp)
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_remain_time[order_i]
            sort[i, 1] = end_time_dict[self.m_j_orig[i, 0]] + self.m_j_orig[
                i, 4
            ].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     order = self.job_order[job]
        #     order_num = self.order_info[job]
        #     speed = self.prod_speed[machine][material]
        #     process_time = order_num * speed
        #     # 找出该订单下对应的未完成的总装任务
        #     order_final_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_final_job = []
        #     for j_ in order_final_job:
        #         if is_finish[np.where(is_finish[:, 0] == j_)[0], 1] == 0:
        #             no_finish_final_job.append(j_)
        #     all_pt = []  # 记录该订单下所有装配件的处理时间
        #     for j_1 in no_finish_final_job:  # 遍历每一个未完成的总装件
        #         no_finish_sub_job = []
        #         j_1_num = self.order_info[j_1]
        #         f_mat = self.job_material[j_1]
        #         # 计算总装件的加工时间
        #         f_can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == f_mat, '速率'].tolist()
        #         f_pt = sum(f_can_use_machine_speed) / len(f_can_use_machine_speed)
        #         sub_job = self.order_level[j_1]  # 所有部装件
        #         for s_j in sub_job:  # 遍历每一个未完成的部装件
        #             if is_finish[np.where(is_finish[:, 0] == s_j)[0], 1] == 0:
        #                 no_finish_sub_job.append(s_j)
        #         if not no_finish_sub_job:  # 该装配件下所有部件均已加工完成
        #             s_pt = 0
        #         else:
        #             pt_l = []  # 所有部件的加工时间记录
        #             for s_j_1 in no_finish_sub_job:
        #                 s_mat = self.job_material[s_j_1]  # 计算物料在所有设备上的平均加工时间
        #                 can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == s_mat, '速率'].tolist()
        #                 ps = sum(can_use_machine_speed) / len(can_use_machine_speed)
        #                 pt = j_1_num * ps
        #                 pt_l.append(pt)
        #             s_pt = max(pt_l)  # 取出所有部装工件加工时间最大值
        #         all_pt.append(f_pt + s_pt)
        #     max_pt = max(all_pt)  # 该任务对应订单的剩余总时间
        #     m_scheme = result[machine]
        #     if not m_scheme:
        #         change_time = 0
        #         end_time = 0
        #     else:
        #         last_scheme = m_scheme[-1]
        #         end_time = last_scheme[-1]
        #         change_time = 0
        #         if material != last_scheme[3]:
        #             if job in self.top_level_job:
        #                 change_time = self.top_change_time
        #             else:
        #                 change_time = self.sub_change_time
        #     new_end_time = end_time + process_time + change_time
        #     sort.append([max_pt, new_end_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def mwkr_spt(self, mask, done, is_finish, result):
        all_order = self.order_data["订单编码"].drop_duplicates()
        order_remain_time = {}
        m_j_orig = self.m_j_orig
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            flag = 0
            temp = []
            for j in order_job:
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    flag = 1
                    # 计算工件的平均加工时间
                    j_idx = np.where(m_j_orig[:, 1] == j)[0]
                    machine_list = m_j_orig[j_idx, 0]
                    material = m_j_orig[j_idx[0], 2]
                    speeds = np.array(
                        [self.prod_speed[m][int(material)] for m in machine_list]
                    )
                    pt_avg = np.mean(speeds)
                    temp.append(pt_avg)
            if not temp:
                order_remain_time[order] = 0
            else:
                order_remain_time[order] = sum(temp) / len(temp)
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_remain_time[order_i]
            sort[i, 1] = self.m_j_orig[i, 4].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     order = self.job_order[job]
        #     order_num = self.order_info[job]
        #     speed = self.prod_speed[machine][material]
        #     process_time = order_num * speed
        #     # 找出该订单下对应的未完成的总装任务
        #     order_final_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_final_job = []
        #     for j_ in order_final_job:
        #         if is_finish[np.where(is_finish[:, 0] == j_)[0], 1] == 0:
        #             no_finish_final_job.append(j_)
        #     all_pt = []  # 记录该订单下所有装配件的处理时间
        #     for j_1 in no_finish_final_job:  # 遍历每一个未完成的总装件
        #         no_finish_sub_job = []
        #         j_1_num = self.order_info[j_1]
        #         f_mat = self.job_material[j_1]
        #         # 计算总装件的加工时间
        #         f_can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == f_mat, '速率'].tolist()
        #         f_pt = sum(f_can_use_machine_speed) / len(f_can_use_machine_speed)
        #         sub_job = self.order_level[j_1]  # 所有部装件
        #         for s_j in sub_job:  # 遍历每一个未完成的部装件
        #             if is_finish[np.where(is_finish[:, 0] == s_j)[0], 1] == 0:
        #                 no_finish_sub_job.append(s_j)
        #         if not no_finish_sub_job:  # 该装配件下所有部件均已加工完成
        #             s_pt = 0
        #         else:
        #             pt_l = []  # 所有部件的加工时间记录
        #             for s_j_1 in no_finish_sub_job:
        #                 s_mat = self.job_material[s_j_1]  # 计算物料在所有设备上的平均加工时间
        #                 can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == s_mat, '速率'].tolist()
        #                 ps = sum(can_use_machine_speed) / len(can_use_machine_speed)
        #                 pt = j_1_num * ps
        #                 pt_l.append(pt)
        #             s_pt = max(pt_l)  # 取出所有部装工件加工时间最大值
        #         all_pt.append(f_pt + s_pt)
        #     max_pt = max(all_pt)  # 该任务对应订单的剩余总时间
        #     sort.append([max_pt, process_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def mwkr_eet(self, mask, done, is_finish, result):
        end_time_dict = {}
        for key, values in result.items():
            if not values:
                end_time_dict[key] = 0
            else:
                end_time_dict[key] = values[-1][-1]

        all_order = self.order_data["订单编码"].drop_duplicates()
        order_remain_time = {}
        m_j_orig = self.m_j_orig
        for order in all_order:
            order_job = self.order_data.loc[
                self.order_data["订单编码"] == order, "工单编号"
            ].tolist()
            flag = 0
            temp = []
            for j in order_job:
                if is_finish[np.where(is_finish[:, 0] == j)[0], 1] == 0:
                    flag = 1
                    # 计算工件的平均加工时间
                    j_idx = np.where(m_j_orig[:, 1] == j)[0]
                    machine_list = m_j_orig[j_idx, 0]
                    material = m_j_orig[j_idx[0], 2]
                    speeds = np.array(
                        [self.prod_speed[m][int(material)] for m in machine_list]
                    )
                    pt_avg = np.mean(speeds)
                    temp.append(pt_avg)
            if not temp:
                order_remain_time[order] = 0
            else:
                order_remain_time[order] = sum(temp) / len(temp)
        sort = np.zeros((self.m_j_array.shape[0], 2), int)
        temp_done = 1 - done
        new_mask = (mask * temp_done).flatten()  # new_mask为1即为满足约束的边
        sort[new_mask == 0, :] = [-1, -1]
        idx_list = np.where(new_mask == 1)[0]
        for i in idx_list:
            order_i = self.job_order[self.m_j_orig[i, 1]]
            sort[i, 0] = order_remain_time[order_i]
            sort[i, 1] = end_time_dict[self.m_j_orig[i, 0]] + self.m_j_orig[
                i, 4
            ].astype(int)
        indices = np.arange(len(sort)).reshape(-1, 1)
        sort_with_indices = np.hstack((sort, indices))  # 合并成新矩阵
        sort_arr = sort_with_indices[
            np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))
        ]
        index = -1
        for i in range(len(sort_arr)):
            if new_mask[int(sort_arr[i, 2])] == 1:
                index = int(sort_arr[i, 2])
                break

        # sort = []
        # temp_done = 1 - done
        # new_mask = mask * temp_done  # new_mask为1即为满足约束的边
        # for i in range(self.m_j_array.shape[0]):
        #     if mask[i] == 0 or done[i] == 1:
        #         sort.append([-1, -1])
        #         continue
        #     info = self.m_j_orig_dict[i]
        #     machine = info[0]
        #     job = info[1]
        #     material = int(info[2])
        #     order = self.job_order[job]
        #     order_num = self.order_info[job]
        #     speed = self.prod_speed[machine][material]
        #     process_time = order_num * speed
        #     # 找出该订单下对应的未完成的总装任务
        #     order_final_job = self.order_data.loc[self.order_data['订单编码'] == order, '工单编号'].tolist()
        #     no_finish_final_job = []
        #     for j_ in order_final_job:
        #         if is_finish[np.where(is_finish[:, 0] == j_)[0], 1] == 0:
        #             no_finish_final_job.append(j_)
        #     all_pt = []  # 记录该订单下所有装配件的处理时间
        #     for j_1 in no_finish_final_job:  # 遍历每一个未完成的总装件
        #         no_finish_sub_job = []
        #         j_1_num = self.order_info[j_1]
        #         f_mat = self.job_material[j_1]
        #         # 计算总装件的加工时间
        #         f_can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == f_mat, '速率'].tolist()
        #         f_pt = sum(f_can_use_machine_speed) / len(f_can_use_machine_speed)
        #         sub_job = self.order_level[j_1]  # 所有部装件
        #         for s_j in sub_job:  # 遍历每一个未完成的部装件
        #             if is_finish[np.where(is_finish[:, 0] == s_j)[0], 1] == 0:
        #                 no_finish_sub_job.append(s_j)
        #         if not no_finish_sub_job:  # 该装配件下所有部件均已加工完成
        #             s_pt = 0
        #         else:
        #             pt_l = []  # 所有部件的加工时间记录
        #             for s_j_1 in no_finish_sub_job:
        #                 s_mat = self.job_material[s_j_1]  # 计算物料在所有设备上的平均加工时间
        #                 can_use_machine_speed = self.line_info.loc[self.line_info['物料编码'] == s_mat, '速率'].tolist()
        #                 ps = sum(can_use_machine_speed) / len(can_use_machine_speed)
        #                 pt = j_1_num * ps
        #                 pt_l.append(pt)
        #             s_pt = max(pt_l)  # 取出所有部装工件加工时间最大值
        #         all_pt.append(f_pt + s_pt)
        #     max_pt = max(all_pt)  # 该任务对应订单的剩余总时间
        #     m_scheme = result[machine]
        #     if not m_scheme:
        #         change_time = 0
        #         end_time = 0
        #     else:
        #         last_scheme = m_scheme[-1]
        #         end_time = last_scheme[-1]
        #         change_time = 0
        #         if material != last_scheme[3]:
        #             if job in self.top_level_job:
        #                 change_time = self.top_change_time
        #             else:
        #                 change_time = self.sub_change_time
        #     new_end_time = end_time + process_time + change_time
        #     sort.append([max_pt, new_end_time])
        # sort = np.array(sort)
        # indices = np.arange(len(sort)).reshape(-1, 1)
        # sort_with_indices = np.hstack((sort, indices))
        # sort_arr = sort_with_indices[np.lexsort((sort_with_indices[:, 1], -sort_with_indices[:, 0]))]
        # index = -1
        # for i in range(len(sort_arr)):
        #     if new_mask[int(sort_arr[i, 2])] == 1:
        #         index = int(sort_arr[i, 2])
        #         break

        return index

    def llm(self, mask, done, result, code, now_time, feature):
        index = -1
        temp_done = 1 - done
        new_mask = mask * temp_done
        min_priority = np.inf
        start = time.time()
        j_feature = feature[:, 0:5]
        m_feature = feature[:, 5:8]
        e_feature = feature[:, 8]
        # feature = self.state.get_feature_1(result, done, mask, is_finish_task, can_use_machine, feature)
        end = time.time() - start
        temp_ = []
        # 在循环外部执行一次代码编译
        start_1 = time.time()
        try:
            # exec(code, globals())
            # # 获取函数引用并存入局部变量
            # cal_priority_func = globals()['cal_priority']
            cal_priority_func = code
            if callable(code):
                cal_priority_func = code
            else:
                exec(code, globals())
            # # 获取函数引用并存入局部变量
                cal_priority_func = globals()['cal_priority']
        except Exception as e:
            print(f"Compilation Error: {e}")
            traceback.print_exc()
            return -1

        min_priority = float("inf")
        index = -1

        # 预先获取数组长度避免重复查询
        n = self.m_j_array.shape[0]

        for i in range(n):
            if new_mask[i] == 0:
                continue

            try:
                # 使用局部变量缓存当前数据
                j = j_feature[i]
                m = m_feature[i]
                e = e_feature[i]

                # 直接传递参数避免创建字典
                priority = cal_priority_func(
                    status=j[0],
                    num_neighboring_machine=j[1],
                    processing_time=j[2],
                    start_time=j[3],
                    delivery_time=j[4],
                    available_time=m[0],
                    num_neighboring_operation=m[1],
                    utilization=m[2],
                    processing_tm=e,
                )
                if priority < min_priority:
                    min_priority = priority
                    index = i

            except Exception as e:
                # print(f"Runtime Error at index {i}: {e}")
                # traceback.print_exc()
                return index  # 保持原错误处理逻辑
        end_1 = time.time() - start_1
        return index

        # for i in range(self.m_j_array.shape[0]):
        #     if new_mask[i] == 0:
        #         continue
        #     try:
        #         exec(code, globals())
        #         params = {
        #             'status': j_feature[i][0],
        #             'num_neighboring_machine': j_feature[i][1],
        #             'processing_time': j_feature[i][2],
        #             'start_time': j_feature[i][3],
        #             'delivery_time': j_feature[i][4],
        #             'available_time': m_feature[i][0],
        #             'num_neighboring_operation': m_feature[i][1],
        #             'utilization': m_feature[i][2],
        #             'processing_tm': e_feature[i][0],
        #         }
        #         priority = globals()['cal_priority'](**params)
        #         if priority < min_priority:
        #             min_priority = priority
        #             index = i
        #         # temp_.append([priority])
        #     except Exception as e:
        #         index = -1
        #         print(f"Error: {e}")
        #         print("错误发生在以下位置:")
        #         traceback.print_exc()
        #         return index
        #
        # return index

    def gp(self, mask, done, result, rule_fun, now_time):
        index = -1
        temp_done = 1 - done
        new_mask = mask * temp_done
        min_priority = np.inf
        j_feature, m_feature, e_feature = self.state.get_feature(
            result, done, mask, now_time, self.all_job, self.all_machine
        )
        for i in range(self.m_j_array.shape[0]):
            if new_mask[i] == 0:
                continue

            # class FeatureContainer:
            #     def __init__(self, j_row, m_row, e_row):
            #         # 按FEATURE_NAMES顺序映射特征
            #         self.status = j_row[0]  # from j_feature
            #         self.num_neighboring_machine = j_row[1]  # from j_feature
            #         self.processing_time = j_row[2]  # from j_feature
            #         self.start_time = j_row[3]  # from j_feature
            #         self.delivery_time = j_row[4]  # from j_feature
            #         self.available_time = m_row[0]  # from m_feature
            #         self.num_neighboring_operation = m_row[1]  # from m_feature
            #         self.utilization = m_row[2]  # from m_feature
            #         self.processing_tm = e_row[0]  # from e_feature

            # # 创建特征容器实例
            # features = FeatureContainer(
            #     j_row=j_feature[i],
            #     m_row=m_feature[i],
            #     e_row=e_feature[i]
            # )
            features = np.concatenate(
                [j_feature[i], m_feature[i], e_feature[i]]
            ).tolist()
            priority = rule_fun(*features)
            if priority < min_priority:
                min_priority = priority
                index = i

        return index
