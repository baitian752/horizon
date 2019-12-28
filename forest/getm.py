#!/usr/bin/python
# -*- coding: utf-8 -*-

import os


def Get_list(mname, inid):
    os.system("cat /dev/null > result.txt")
    cmd = "gnocchi measures show" + mname + " --resource-id" + inid + " > result.txt"
    os.popen(cmd).read()

    with open("result.txt", "r") as file1:
        list_row = file1.readlines()
        m = len(list_row)

    list_source = []
    list_column = []
    for i in range(4, m - 1):
        list_column = list_row[i].strip().strip('|').split('|', 2)
        list_source.append(list_column)
    k = len(list_source)
    if k == 0:
        s = 0
    else:
        s = float(list_source[k - 1][2].strip())
    return s
