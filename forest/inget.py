#!/usr/bin/python
# -*- coding: utf-8 -*-

import os


def Get_in():
    os.system("cat /dev/null > result.txt")
    cmd = "gnocchi resource list  > result.txt"
    os.popen(cmd).read()

    with open("result.txt", "r") as file1:
        list_row = file1.readlines()
    m = len(list_row)
    list_source = []
    list_column = []
    s1 = set()
    listin = []

    for i in range(4, m - 1):
        list_column = list_row[i].strip().strip('|').split('|', 9)
        list_source.append(list_column)

    for i in range(m - 5):
        for _ in range(3):
            if list_source[i][1].strip() == "instance":
                s1.add(list_source[i][0].strip())

    for value in s1:
        listin.append(value)

    return listin


listin = list()
listin = Get_in()
print(listin)
