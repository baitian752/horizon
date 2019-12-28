#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import random

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


def forest_t():

    data = pd.read_csv(r'./data.csv')
    print("数据相关信息：\n")
    print(data.describe())
    print("DataHead")
    print(data.head())
    print(data.shape)
    index = data.index
    class_names = np.unique(data.iloc[:, 1])
    print("Classnames:")
    print(class_names)

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        data.loc[:, data.columns != 'Outcome'], data['Outcome'], stratify=data['Outcome'], random_state=66)

    from sklearn.model_selection import GridSearchCV
    from sklearn.model_selection import RandomizedSearchCV
    max_depth = [int(x) for x in np.linspace(10, 100, num=10)]
    max_depth.append(None)

    rf = RandomForestClassifier(n_estimators=100, random_state=0)

    rf.fit(X_train, y_train)
    y_train_pred = rf.predict(X_train)
    y_test_pred = rf.predict(X_test)
    print(rf.feature_importances_)
    print("Accuracy on training set:{:.3f}". format(
        rf. score(X_train, y_train)))
    print("Accuracy on test set:{:.3f}". format(rf. score(X_test, y_test)))

    from sklearn.metrics import mean_squared_error, explained_variance_score, mean_absolute_error, r2_score
    print("决策树模型评估--训练集：")
    print('训练r^2:', rf.score(X_train, y_train))
    print('均方差', mean_squared_error(y_train, y_train_pred))
    print('绝对差', mean_absolute_error(y_train, y_train_pred))
    print('解释度', explained_variance_score(y_train, y_train_pred))
    print("决策树模型评估--验证集：")
    print('验证r^2:', rf.score(X_test, y_test))
    print('均方差', mean_squared_error(y_test, y_test_pred))
    print('绝对差', mean_absolute_error(y_test, y_test_pred))
    print('解释度', explained_variance_score(y_test, y_test_pred))

    data_pred = pd.read_csv(r'./test_t.csv')
    index = data_pred.index
    print("预测：")
    print(index)

    X_test1 = data_pred.loc[:, data_pred.columns != 'Outcome']
    y_pred = rf.predict(X_test1)
    print(y_pred)
    insid = list()
    for i in range(len(y_pred)):
        if y_pred[i] == 1:
            insid.append(i)
    return insid
