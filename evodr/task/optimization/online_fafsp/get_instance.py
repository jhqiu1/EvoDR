import pickle
import os
import evodr.task.optimization.online_fafsp.old_dataProcessing
import os, sys

sys.path.append(
    os.path.dirname(os.path.abspath(__file__))  # This is for finding all the modules
)


def load_data(txt):
    # fileObject = open('edd_memories_gpuV2.txt', 'wb')
    # # 保存模型
    # file_url = './data_test/m13-m26-f0.5-arrive20-u1.txt'

    # 获取当前执行的python脚本所在的目录
    script_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
    )
    # 基于脚本目录构建文件路径
    file_url = os.path.join(script_dir, "example", "online_fafsp", "data_test", txt)
    # case init
    fileObject = open(file_url, "rb")
    Datas = pickle.load(fileObject)
    # print( '数据预处理时间为', time.time() - st )
    fileObject.close()

    return Datas
