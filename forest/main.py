import numpy as np
# from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

data = './data.csv'


class Forest(object):

    def __init__(self):
        pass

    def a(self):
        pass

datas = np.loadtxt(data, delimiter=',', skiprows=1)
X_train = datas[:,0:-1]
y_train = datas[:, -1]
print(X_train)
print(y_train)
# with open(data, 'r') as f:
#     train = csv.reader(f)
#     print(np.array(list(train)[1:]))