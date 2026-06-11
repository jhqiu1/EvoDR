import time
import datetime
import pandas as pd
import numpy as np
import time


class DataProcess:
    def __init__(self):
        self.allLineList = []  # 所有产线
        self.lineDataF = {}  # 产线原始数据
        self.lineData = {}  # 产线数据
        self.productLine = {}  # 物料产线资质
        self.productSpeed = {}  # 生产速度
        self.materialDataF = {}  # 物ist料原始数据
        self.materialList = []  # 物料数据
        self.material = {}  # 物料数据
        self.allMaterial = []  # 所有物料数据
        self.orderlDataF = {}  # 定单原始数据
        self.orderTaskData = {}  # 定单工单关系
        self.taskOrderData = {}  # 工单定单关系
        self.lineProduct = {}  # 产线和产品关系
        # self.taskWOData = {}  # 工单详情信息
        self.taskWOMaterial = {}  # 工单物料
        self.taskWONumber = {}  # 工单物料数量
        self.taskWOFinishS = {}  # 工单截至日期
        self.taskWOArriveS = {}  # 工单到达日期
        self.taskWOOrder = {}  # 工单的定单
        self.jobWOOrder = {}  # 所有作业归属订单
        self.taskWOStartS = {}  # 工单截至日期
        self.orderList = []  # 定单数列
        self.orderAssJobNum =  {}  # 订单下面的装配任务数量
        self.orderArriveTime =  {}  # 订单到达交货时间
        self.orderPDeliveryTime =  {}  # 订单计划交货时间
        self.orderDeliveryTime =  {}  # 订单实际交货时间
        self.topMatChangeTime = 10 * 60  # 顶层物料换产时间
        self.secondMatChangeTime = 30 * 60  # 二层物料换产时间
        self.thirdMatChangeTime = 30 * 60  # 三层物料换产时间
        self.leadTime = 1 * 60  # 提前期
        self.topMaterial = []  # 物料数组
        self.secondMaterial = []  # 物料数组
        self.thirdMaterial = []  # 物料数组
        self.materialLevel = {}  # 物料级别
        self.startTime3 = '2022-01-28 00:00:00'  # 起始时间
        self.beginTime = ''  # datetime
        self.parallelOrderList = []  # 并行机定单集合
        # 运行过程基础数据（总装）
        self.assemblyLineList = []  # 总装线数列
        self.assemblyOrderList = []  # 总装线待定单集合
        self.assemblyOrderFinishDo = {}  # 总装订单的所属工单完成情况
        self.orderFinishDo = {}  # 订单的所属工单完成情况
        self.assemblyNowMaterial = {}  # 总装线当前加工物料
        self.assemblyNowWOrder = {}  # 总装线当前加工工单
        self.assemblyNowTaktTime = {}  # 总装线当前单个加工物料所需要时间
        self.assemblyNowTime = {}  # 总装线当前单个加工物料当前积累时间
        self.assemblyNowStayTime = {}  # 总装线当前工单加工积累总时间
        self.assemblyNowStayNum = {}  # 总装线当前工单加工积累总数量
        self.assemblyNetOrder = {}  # 总装线下一个加工工单
        self.assemblyWaitTime = {}  # 总装线下一个工单的启动时间
        self.assemblyBeforeMaterial = {}  # 总装线上工单的加工物料
        self.assemblyOrderResult = {}  # 总装线订单完成情况
        self.topWarehouse = {}  # 成品库存
        # 运行过程基础数据（部装）
        self.subassemblyLineList = []  # 部装线数列
        self.subassemblyOrderList = []  # 部装线待定单集合
        self.subassemblyNowMaterial = {}  # 部装线当前加工物料
        self.subassemblyNowWOrder = {}  # 部装线当前加工工单
        self.subassemblyNowTaktTime = {}  # 部装线当前单个加工物料所需要时间
        self.subassemblyNowTime = {}  # 部装线当前单个加工物料当前积累时间
        self.subassemblyNowStayTime = {}  # 部装线当前工单加工积累总时间
        self.subassemblyNowStayNum = {}  # 部装线当前工单加工积累总数量
        self.subassemblyNetOrder = {}  # 部装线下一个加工工单
        self.subassemblyWaitTime = {}  # 部装线下一个工单的启动时间
        self.subassemblyBeforeMaterial = {}  # 部装线上工单的加工物料
        self.subassemblyOrderResult = {}  # 部装线订单完成情况
        self.secondWarehouse = {}  # 第二层库存
        # 运行过程基础数据（并行机）
        self.parallelMachineList = []  # 并行机数列
        self.parallelOrderList = []  # 并行机待定单集合
        self.parallelNowMaterial = {}  # 并行机当前加工物料
        self.parallelNowWOrder = {}  # 并行机当前加工工单
        self.parallelNowTaktTime = {}  # 并行机当前单个加工物料所需要时间
        self.parallelNowTime = {}  # 并行机当前单个加工物料当前积累时间
        self.parallelNowStayTime = {}  # 并行机当前工单加工积累总时间
        self.parallelNowStayNum = {}  # 并行机当前工单加工积累总数量
        self.parallelNetOrder = {}  # 并行机下一个加工工单
        self.parallelWaitTime = {}  # 并行机下一个工单的启动时间
        self.parallelBeforeMaterial = {}  # 并行机上工单的加工物料
        self.thirdWarehouse = {}  # 第三层库存
        #     模型全局参数
        self.timeNow = 0
        self.timeLong = 1000
        self.xlsx_file = r"DataSmall/测试数据-O200-M20-L9-S8-07260941.xlsx"
        self.changeTimeData = {}

    def getData(self):
        # self.xlsx_file = r"DataSmall/多级共享件测试数据Small.xlsx"
        # self.xlsx_file = r"DataSmall/测试数据-O200-M20-L9-S8-07260941.xlsx"
        st = time.time()
        self.getMatData()
        self.getLineData()
        self.getOrderData()

    # 获取原料数据
    def getMatData(self):
        self.materialDataF = pd.read_excel(self.xlsx_file, sheet_name=0)
        # self.orderlDataF = pd.read_excel( xlsx_file, sheet_name=3 )
        materialDataF = self.materialDataF
        materialList = np.array(materialDataF['上层编码'].drop_duplicates())
        self.allMaterial = materialList
        material = {}
        # 获取唯一top物料获取bomlist
        for j in range(len(materialList)):
            # 材料数列定义物料行
            condition = '上层编码' + '==' + str(materialList[j])
            topMaterial = materialDataF.query(condition)
            material[materialList[j]] = []
            for i in range(len(topMaterial.index)):
                # print( topMaterial.loc[topMaterial.index[i], ['下层编码']]['下层编码'] )
                material[materialList[j]].append(topMaterial.loc[topMaterial.index[i], ['下层编码']]['下层编码'])
                # 获取当前物料层级 level = *:[1/2/3]
            self.materialLevel[materialList[j]] = []
            self.materialLevel[materialList[j]].append(
                topMaterial.loc[topMaterial.index[0], ['上层物料层级']]['上层物料层级'])
        self.material = material
        # 获取当前不同层级物料 top = [*,*,*,*,*]
        for j in range(len(materialDataF)):
            if materialDataF.loc[j, ['上层物料层级']]['上层物料层级'] == 1:
                self.topMaterial.append(materialDataF.loc[j, ['上层编码']]['上层编码'])
            elif materialDataF.loc[j, ['上层物料层级']]['上层物料层级'] == 2:
                self.secondMaterial.append(materialDataF.loc[j, ['上层编码']]['上层编码'])
            else:
                self.thirdMaterial.append(materialDataF.loc[j, ['上层编码']]['上层编码'])
        for material in self.thirdMaterial:
            self.thirdWarehouse[material] = 0
        for material in self.secondMaterial:
            self.secondWarehouse[material] = 0
        for material in self.topMaterial:
            self.topWarehouse[material] = 0
        pass

        # 获取原料数据

    # 处理产线和生产效率数据
    def getLineData(self):
        # 获取产线数据
        self.lineDataF = pd.read_excel(self.xlsx_file, sheet_name=2)
        allLineList = np.array(self.lineDataF['生产线'].drop_duplicates())
        lineDataF = self.lineDataF
        allMaterial = self.allMaterial
        self.allLineList = allLineList
        # 获取[mat]:[pro1, pro2 ,pro3 ]
        lineProduct = {}
        productSpeed = {}
        for i in range(len(allLineList)):
            self.changeTimeData[allLineList[i]] = []
            condition = '生产线' + '==' + '"' + str(allLineList[i]) + '"'
            canLineD = lineDataF.query(condition)
            lineProduct[allLineList[i]] = []
            # 产线分类
            productSpeed[allLineList[i]] = {}
            if self.materialLevel[lineDataF.loc[canLineD.index[0], ['物料编码']]['物料编码']][0] == 2:
                self.subassemblyLineList.append(allLineList[i])
                self.subassemblyNowMaterial[allLineList[i]] = -1  # 部装线当前加工物料
                self.subassemblyNowWOrder[allLineList[i]] = -1  # 部装线当前加工工单
                self.subassemblyNowTaktTime[allLineList[i]] = -1  # 部装线当前单个加工物料所需要时间
                self.subassemblyNowTime[allLineList[i]] = -1  # 部装线当前单个加工物料当前积累时间
                self.subassemblyNowStayTime[allLineList[i]] = -1  # 部装线当前工单加工积累总时间
                self.subassemblyNowStayNum[allLineList[i]] = -1  # 部装线当前工单加工积累总数量
                self.subassemblyNetOrder[allLineList[i]] = -1  # 部装线下一个工单
                self.subassemblyBeforeMaterial[allLineList[i]] = -1  # 部装线上工单的加工物料
                self.subassemblyWaitTime[allLineList[i]] = -1  # 部装线下一个工单待开工时间
            elif self.materialLevel[lineDataF.loc[canLineD.index[0], ['物料编码']]['物料编码']][0] == 3:
                self.parallelMachineList.append(allLineList[i])
                self.parallelNowMaterial[allLineList[i]] = -1  # 并行机当前加工物料
                self.parallelNowWOrder[allLineList[i]] = -1  # 并行机当前加工工单
                self.parallelNowTaktTime[allLineList[i]] = -1  # 并行机当前单个加工物料所需要时间
                self.parallelNowTime[allLineList[i]] = -1  # 并行机当前单个加工物料当前积累时间
                self.parallelNowStayTime[allLineList[i]] = -1  # 并行机当前工单加工积累总时间
                self.parallelNowStayNum[allLineList[i]] = -1  # 并行机当前工单加工积累总数量
                self.parallelNetOrder[allLineList[i]] = -1  # 并行机下一个工单
                self.parallelWaitTime[allLineList[i]] = -1  # 并行机下一个工单待开工时间
                self.parallelBeforeMaterial[allLineList[i]] = -1  # 并行机上工单的加工物料
            else:
                self.assemblyLineList.append(allLineList[i])
                self.assemblyNowMaterial[allLineList[i]] = -1  # 总装线当前加工物料
                self.assemblyNowWOrder[allLineList[i]] = -1  # 总装线当前加工工单
                self.assemblyNowTaktTime[allLineList[i]] = -1  # 总装线当前单个加工物料所需要时间
                self.assemblyNowTime[allLineList[i]] = -1  # 总装线当前单个加工物料当前积累时间
                self.assemblyNowStayTime[allLineList[i]] = -1  # 总装线当前工单加工积累总时间
                self.assemblyNowStayNum[allLineList[i]] = -1  # 总装线当前工单加工积累总数量
                self.assemblyNetOrder[allLineList[i]] = -1  # 总装线下一个工单
                self.assemblyWaitTime[allLineList[i]] = -1  # 总装线下一个工单待开工时间
                self.assemblyBeforeMaterial[allLineList[i]] = -1  # 总装线上工单的加工物料
            # 获取[物料][产线]：[速率]
            for j in range(len(canLineD.index)):
                lineProduct[allLineList[i]].append(lineDataF.loc[canLineD.index[j], ['物料编码']]['物料编码'])
                productSpeed[allLineList[i]][lineDataF.loc[canLineD.index[j], ['物料编码']]['物料编码']] = 0
                productSpeed[allLineList[i]][lineDataF.loc[canLineD.index[j], ['物料编码']]['物料编码']] = round(
                    lineDataF.loc[canLineD.index[j], ['速率']]['速率'], 0)
        self.lineProduct = lineProduct
        self.productSpeed = productSpeed

        pass

    def getOrderData(self):
        self.beginTime = datetime.datetime.strptime(self.startTime3, '%Y-%m-%d %H:%M:%S')
        orderlDataF = pd.read_excel(self.xlsx_file, sheet_name=4)
        self.orderlDataF = orderlDataF
        orderList = np.array(self.orderlDataF['订单编码'].drop_duplicates())
        self.orderList = orderList
        for orderStr in orderList:
            self.orderFinishDo[orderStr] = 0
            self.orderAssJobNum[orderStr] = 0 # 订单的所属装配任务数量
            self.orderArriveTime[orderStr] =  0  # 订单到达交货时间
            self.orderPDeliveryTime[orderStr] =  0  # 订单计划交货时间
            self.orderDeliveryTime[orderStr] =  0  # 订单实际交货时间
        # 建立工单详情
        for i in range(len(orderlDataF)):
            # 当前工单属于哪个车间进行调度

            if self.materialLevel[orderlDataF.loc[i, ['装配件编码']]['装配件编码']][0] == 2:
                self.subassemblyOrderList.append(orderlDataF.loc[i, ['工单编号']]['工单编号'])
            elif self.materialLevel[orderlDataF.loc[i, ['装配件编码']]['装配件编码']][0] == 3:
                self.parallelOrderList.append(orderlDataF.loc[i, ['工单编号']]['工单编号'])
            else:
                self.assemblyOrderList.append(orderlDataF.loc[i, ['工单编号']]['工单编号'])
                self.assemblyOrderResult[orderlDataF.loc[i, ['工单编号']]['工单编号']] = 0
            # 构建工单信息数列，taskWOOrder：工单-定单；taskWOMaterial-物料；taskWONumber：工单-数量
            self.taskWONumber[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            self.taskWONumber[orderlDataF.loc[i, ['工单编号']]['工单编号']] = orderlDataF.loc[i, ['工单数量']][
                '工单数量']
            self.taskWOMaterial[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            self.taskWOMaterial[orderlDataF.loc[i, ['工单编号']]['工单编号']] = orderlDataF.loc[i, ['装配件编码']][
                '装配件编码']
            self.taskWOOrder[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            self.taskWOOrder[orderlDataF.loc[i, ['工单编号']]['工单编号']] = orderlDataF.loc[i, ['订单编码']][
                '订单编码']
            self.jobWOOrder[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            self.jobWOOrder[orderlDataF.loc[i, ['工单编号']]['工单编号']] = orderlDataF.loc[i, ['订单编码']][
                '订单编码']
            self.orderAssJobNum[orderlDataF.loc[i, ['订单编码']]['订单编码']] +=1
            # 最早开工时间
            self.taskWOStartS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            date = orderlDataF.loc[i, ['最早开工时间']]['最早开工时间']
            diff = date - self.beginTime
            # print( "两个时间相差{0}秒".format( diff.seconds ) )
            self.taskWOStartS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = diff.seconds
            # 需求时间
            self.taskWOFinishS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            self.taskWOArriveS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = {}
            date = orderlDataF.loc[i, ['需求时间']]['需求时间']
            # date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            diff = time.mktime(date.timetuple()) - (time.mktime(self.beginTime.timetuple()))
            arrtime = time.mktime(orderlDataF.loc[i, ['最早开工时间']]['最早开工时间'].timetuple()) - (time.mktime(self.beginTime.timetuple()))
            self.orderArriveTime[orderlDataF.loc[i, ['订单编码']]['订单编码']]=arrtime
            self.orderPDeliveryTime[orderlDataF.loc[i, ['订单编码']]['订单编码']]=diff
            # diff = date - self.beginTime
            # diff = time.mktime(diff.timetuple())
            # print( "两个时间相差{0}秒".format( diff.seconds ) )
            # diff = time.mktime(date.timetuple()) - (time.mktime(self.beginTime.timetuple())+86400*11)
            self.taskWOFinishS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = diff
            self.taskWOArriveS[orderlDataF.loc[i, ['工单编号']]['工单编号']] = arrtime
        self.addsubOrder()
        pass

    def runModel(self):
        for self.timeNow in range(self.timeLong):
            self.parMachinesSchedule()
            self.subassemblySchedule()
            self.assemblySchedule()

            # print(self.timeNow)
        pass

    # 并行机调度
    def addsubOrder(self):
        temp = 1
        orderTaskData = {}
        for order in self.assemblyOrderList:
            orderTaskData[order] = []
            self.assemblyOrderFinishDo[order] = 0
            for index in range(len(self.material[self.taskWOMaterial[order]])):
                # print(self.material[self.taskWOMaterial[order]][index])
                orderStr = ''
                orderStr = ('A%g' % temp)
                self.subassemblyOrderResult[orderStr] = 0
                self.subassemblyOrderList.append(orderStr)
                self.taskWONumber[orderStr] = {}
                self.taskWONumber[orderStr] = self.taskWONumber[order]
                # 记录工单与所属订单关系
                self.taskOrderData[orderStr] = {}
                self.taskOrderData[orderStr] = order
                self.taskWOMaterial[orderStr] = {}
                self.taskWOMaterial[orderStr] = self.material[self.taskWOMaterial[order]][index]
                self.taskWOOrder[orderStr] = {}
                self.taskWOOrder[orderStr] = order
                self.jobWOOrder[orderStr] = {}
                self.jobWOOrder[orderStr] = self.taskWOOrder[order]
                self.taskWOFinishS[orderStr] = {}
                self.taskWOFinishS[orderStr] = self.taskWOFinishS[order]
                self.taskWOArriveS[orderStr] = {}
                self.taskWOArriveS[orderStr] = self.taskWOArriveS[order]
                orderTaskData[order].append(orderStr)
                temp += 1
        self.orderTaskData = orderTaskData
        pass

# import pickle
# st = time.time()
#
# # 加载历史模型数据
# fileObject = open('dataSmallFile0709.txt', 'wb')
# # 保存模型
# data = DataProcess()
# data.getData()
#
# temp = {}
# temp[0]=0
#
# temp[1]=0
#
# temp[2]=0
#
# temp[3]=0
#
# for order in data.assemblyOrderList :
#     if data.material[data.taskWOMaterial[order]]==[202, 322]:
#         temp[0]+= data.taskWONumber[order]
#     elif data.material[data.taskWOMaterial[order]]==[202, 323]:
#         temp[1]+= data.taskWONumber[order]
#     elif data.material[data.taskWOMaterial[order]]==[201, 322]:
#         temp[2]+= data.taskWONumber[order]
#     elif data.material[data.taskWOMaterial[order]]==[201, 323]:
#         temp[3]+= data.taskWONumber[order]
#
# print(temp)
#
#
# pickle.dump(data, fileObject)
# fileObject.flush()
# fileObject.close()
