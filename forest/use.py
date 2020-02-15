#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from getm import Get_list
from forest import forest_t
from inget import Get_in


with open(r'test_t.csv', mode='w') as file:
    file.write('cpu_usage,vcpus,memory.usage,disk.ephemeral.size,disk.root.size,compute.instance.booting.time,Outcome')
    file.write('\n')

    listin = Get_in()

    for i in range(len(listin)):
        cpu = Get_list("cpu", listin[i])
        memory_usage = Get_list("memory.usage", listin[i])
        vcpus = Get_list("vcpus", listin[i])
        disk_ephemeral_size = Get_list("disk.ephemeral.size", listin[i])
        disk_root_size = Get_list("disk.root.size", listin[i])
        compute_instance_booting_time = Get_list(
            "compute.instance.booting.time", listin[i])

        cpu_usage1 = round(cpu/(5*60*(10**9)), 4)
        cpu_usage = 100*cpu_usage1

        file.write(str(cpu_usage)+','+str(vcpus)+','+str(memory_usage)+','+str(disk_ephemeral_size) +
                ','+str(disk_root_size)+','+str(compute_instance_booting_time)+',?')
        file.write('\n')

insid = forest_t()


listin = Get_in()
listid = list()

for i in range(len(insid)):
    listid.append(listin[i-1])

print(listid)


# mail_host = "smtp.qq.com"
# mail_user = "2842215855@qq.com"
# mail_pass = "msppwbwgajaydddj"

# sender = '2842215855@qq.com'
# receivers = ['192917215@qq.com']

# message = MIMEText('根据预测，以下的虚拟机有存在故障的风险：\n'+str(listid), 'plain', 'utf-8')
# message['From'] = Header("alarm", 'utf-8')
# message['To'] = Header("user", 'utf-8')

# subject = '故障预测'
# message['Subject'] = Header(subject, 'utf-8')

# if len(insid) != 0:
#     try:
#         smtpobj = smtplib.SMTP_SSL(mail_host, 465)
#         smtpobj.set_debuglevel(1)
#         smtpobj.login(mail_user, mail_pass)
#         smtpobj.sendmail(sender, receivers, message.as_string())
#         print("邮件发送成功")
#         smtpobj.quit()
#     except smtplib.SMTPException as e:
#         print("Error:无法发送邮件")
#         print(e)
