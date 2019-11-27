import time
import threading
import sqlite3


from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client
from zunclient import client as zun_client
# from glanceclient import client as glance_client
from neutronclient.v2_0 import client as neutron_client


# from horizon.utils.memoized import memoized
# from openstack_dashboard.contrib.developer.profiler import api as profiler

# from openstack_dashboard.api._nova import novaclient
# from zun_ui.api.client import zunclient, neutronclient


table_name = 'tasks'


# @memoized
# def taskclient(request):
#     if request.DATA.virtualization == 'Virtual Machine':
#         return novaclient(request)
#     elif request.DATA.virtualization == 'Docker':
#         return zunclient(request)


# @profiler.trace
# def task_create(request):
#     pass
#     # return taskclient(request).services.


# @profiler.trace
# def task_delete(request, task_id):
#     return taskclient(request).tasks.delete(task_id)


class Schedule(threading.Thread):

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        super(Schedule, self).__init__()
        self.auth = identity.Password(
            **self.get_credential(admin_openrc=admin_openrc))
        self.sess = session.Session(auth=self.auth)
        # self.glance = glance_client.Client(version='2', session=self.sess)
        self.nova = nova_client.Client(version='2', session=self.sess)
        self.zun = zun_client.Client(version='1', session=self.sess)
        self.neutron = neutron_client.Client(session=self.sess)
        self.hypervisors = self.nova.hypervisors.list()

    def run(self):
        self.tasks = Tasks('tasks')
        while True:
            time.sleep(10)
            task = self.tasks.get_task()
            while not task:
                time.sleep(10)
                task = self.tasks.get_task()
            if task['virtualization'] == 'Virtual Machine':
                image = self.get_image()
                name = image.name
                flavor = self.get_flavor(task)
                userdata = task['job']
                meta = {'task_name': task['name']}
                nics = [{'net-id': self.get_network_id()}]
                self.check_resources(flavor.vcpus, flavor.ram, flavor.disk)
                self.run_server(name, image, flavor, userdata, meta, nics)
            elif task['virtualization'] == 'Docker':
                name = task['name']
                image = 'cirros'
                command = task['job'].split()
                cpu = task['cpu']
                memory = task['ram']
                self.check_resources(cpu, memory, 1)
                self.run_container(name, image, command, cpu, memory)
            self.tasks.update_status(task['id'], 'finished')

    def get_image(self):
        images = self.nova.glance.list()
        image = images[0]
        for item in images:
            if 'ubuntu' in item.name.lower():
                image = item
                break
        return image

    def get_flavor(self, task):
        flavors = self.nova.flavors.list()
        flavor = flavors[-1]
        for item in flavors:
            if item.vcpus >= task['cpu'] and item.ram >= task['ram'] \
                and item.disk >= task['disk']:
                flavor = item
                break
        return flavor

    def get_network_id(self):
        networks = self.neutron.list_networks()['networks']
        network = networks[0]
        for item in networks:
            if not item['router:external']:
                network = item
                break
        return network['id']

    def get_credential(self, admin_openrc):
        credential = {}
        with open(admin_openrc, 'r') as f:
            for line in f.readlines():
                data = line.split()[1]
                k, v = data.split('=', 1)
                credential[k[3:].lower()] = v
        return {
            'username': credential['username'],
            'password': credential['password'],
            'project_name': credential['project_name'],
            'project_domain_name': credential['project_domain_name'],
            'user_domain_name': credential['user_domain_name'],
            'auth_url': credential['auth_url'],
        }

    def run_server(self, name, image, flavor, userdata, meta, nics):
        self.nova.servers.create(name=name, image=image, flavor=flavor,
                                 userdata=userdata, meta=meta, nics=nics)

    def run_container(self, name, image, command, cpu, memory):
        self.zun.containers.create(name=name, image=image, command=command,
                                   cpu=cpu, memory=memory)

    def check_resources(self, cpu, ram, disk):
        flag = False
        while not flag:
            for hypervisor in self.hypervisors:
                if hypervisor.vcpus - hypervisor.vcpus_used >= cpu and \
                    hypervisor.free_ram_mb >= ram and \
                    hypervisor.free_disk_gb >= disk:
                    flag = True
                    break
            if not flag:
                time.sleep(10)


class Tasks(object):

    def __init__(self, table_name):
        self.table_name = table_name
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(''' select count(name) from sqlite_master
                                where type='table' and name='%s' '''
                                % self.table_name)
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(''' create table %s
                                    (id integer primary key autoincrement,
                                     name character(128) not null,
                                     status character(50) not null,
                                     virtualization character(50) not null,
                                     cpu int not null,
                                     ram int not null,
                                     disk int not null,
                                     job text not null,
                                     estimated_time_of_execution real not null,
                                     execution_frequency real not null,
                                     main_job character(128) not null,
                                     require_hardware character(4) not null,
                                     priority int not null,
                                     created_timestamp real not null)'''
                                     % self.table_name)
        self.conn.commit()

    def add(self, data):
        self.cursor.execute(''' insert into %s (
                                name,
                                status,
                                virtualization,
                                cpu,
                                ram,
                                disk,
                                job,
                                estimated_time_of_execution,
                                execution_frequency,
                                main_job,
                                require_hardware,
                                priority,
                                created_timestamp
                                ) values 
                                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
                            % self.table_name,
                            (data['name'],
                             data['status'],
                             data['virtualization'],
                             data['cpu'],
                             data['ram'],
                             data['disk'],
                             data['job'],
                             data['estimated_time_of_execution'],
                             data['execution_frequency'],
                             data['main_job'],
                             data['require_hardware'],
                             data['priority'],
                             data['created_timestamp']
                            ))
        self.conn.commit()

    def delete(self, task_id):
        self.cursor.execute(''' delete from %s where id=?'''
                                % self.table_name, (task_id,))
        self.conn.commit()

    def get_task(self):
        self.cursor.execute(''' select * from %s where status='ready' and
                                estimated_time_of_execution=
                                (select min(estimated_time_of_execution) from %s)
                                order by created_timestamp asc'''
                                % (self.table_name, self.table_name))
        task = self.cursor.fetchone()
        if task:
            task = list(task)
            if task[3] == 'Auto':
                self.cursor.execute(''' select * from %s where status='finished'
                                        and job='%s' order by created_timestamp 
                                        desc ''' % (self.table_name, task[7]))
                old_task = self.cursor.fetchone()
                if old_task:
                    task[3] = old_task[3]
                elif task[11] == 'Yes':
                    task[3] = 'Virtual Machine'
                else:
                    task[3] = 'Docker'
            return {
                'id': task[0],
                'name': task[1],
                'status': task[2],
                'virtualization': task[3],
                'cpu': task[4],
                'ram': task[5],
                'disk': task[6],
                'job': task[7],
                'estimated_time_of_execution': task[8],
                'execution_frequency': task[9],
                'main_job': task[10],
                'require_hardware': task[11],
                'priority': task[12],
                'created_timestamp': task[13]
            }

    def update_status(self, task_id, status):
        self.cursor.execute(''' update %s set status='%s' where id=%s '''
                                % (self.table_name, status, task_id))
        self.conn.commit()

    def __del__(self):
        self.cursor.close()
        self.conn.close()
