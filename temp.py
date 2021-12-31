'''
import numpy as np
import matplotlib.pyplot as plt

def read_log():
    file = "data.log"
    with open(file) as f:
        """使用while循环每次只读取一行,读到最后一行的时候结束"""
        data = []
        while True:
            lines = f.readline()
            if not lines:
                break
            line = lines.split(',')[:-1]
            data.append(line)
        data  =data[1:]
        data = np.array(data)
        data = data[:,6]
        return data


if __name__ == '__main__':
    data = read_log()
    print(data)
    length = len(data)
    length = np.arange(0, length,1)
    plt.plot(length,data)
'''
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas.core.frame import DataFrame
plt.rcParams['font.sans-serif'] = ['KaiTi']
data = [[41.71,44.26,48.42,48.18,48.91,46.18],[44.43,44.97,49.17,46.21,44.22,43.39],[41.36,42.06,43.32,46.28,45.01,42.72],[45.24,46.17,47.85,51.69,52.22,49.05]]
data = np.array(data).T
data=DataFrame(data)
data.index = [6,7,8,9,10,11]
#data.rename(index = {0:'8',1:'9',2:'10',3:'11'})
print(data)
data.plot.line(xticks=[6,7,8,9,10,11],figsize=(12,12),fontsize=20) # 折线图data1.plot.line(subplots=True) # 显示多个子图plt.show()

plt.show()

