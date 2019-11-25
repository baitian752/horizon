import time
import threading
import json
import sqlite3

from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client
from zunclient import client as zun_client
from neutronclient.v2_0 import client as neutron_client

from horizon.utils.memoized import memoized
from openstack_dashboard.contrib.developer.profiler import api as profiler

from openstack_dashboard.api._nova import novaclient
from zun_ui.api.client import zunclient, neutronclient


@memoized
def taskclient(request):
    if request.DATA.virtualization == 'Virtual Machine':
        return novaclient(request)
    elif request.DATA.virtualization == 'Docker':
        return zunclient(request)


@profiler.trace
def task_create(request):
    return taskclient(request).services.


@profiler.trace
def task_delete(request, task_id):
    return taskclient(request).tasks.delete(task_id)




class Schedule(threading.Thread):

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        super(Schedule, self).__init__()
        self.auth = identity.Password(**self.get_credential(admin_openrc=admin_openrc))
        self.sess = session.Session(auth=self.auth)
        self.nova = nova_client.Client(version='2', session=self.sess)
        self.zun = zun_client.Client(version='2', session=self.sess)
        self.neutron = neutron_client.Client(session=self.sess)
        self.hypervisors = self.nova.hypervisors.list()

    def run(self):
        self.database = Database('tasks')
        while True:
            time.sleep(10)
            self.database.update_priorities()
            task = self.database.get_task()
            while not task:
                time.sleep(10)
                task = self.database.get_task()
            config = task.get('config', None)
            if config:
                print(config)
                time.sleep(10)
                # config = json.loads(config)
                # virtualization = config.get('virtualization', 'Docker')
                # if virtualization == 'Virtual Machine':
                #     name = config['name']
                #     image = novaclient.glance.find_image(config['source_id'])
                #     flavor = novaclient.flavors.get(config['flavor_id'])
                #     userdata = config['user_data']
                #     meta = config['meta']
                #     nics = config['nics']
                #     self.check_resources(flavor.vcpus, flavor.ram, 1)
                #     self.run_server(name, image, flavor, userdata, meta, nics)
                # elif virtualization == 'Docker':
                #     name = config['name']
                #     image = config['image']
                #     command = config['command'].strip().split()
                #     cpu = config['cpu']
                #     memory = config['memory']
                #     self.check_resources(cpu, memory, flavor.disk)
                #     self.run_container(name, image, command, cpu, memory)
            self.database.delete(task.get('id', 0))

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

    def check_resources(self, vcpus, ram, disk):
        flag = False
        while not flag:
            for hypervisor in self.hypervisors:
                if hypervisor.vcpus - hypervisor.vcpus_used >= vcpus and \
                    hypervisor.free_ram_mb >= ram and \
                    hypervisor.free_disk_gb >= disk:
                    flag = True
                    break
            if not flag:
                time.sleep(10)


class Database(object):

    def __init__(self, table_name):
        self.table_name = table_name
        self.conn = sqlite3.connect('tasks.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute(''' select count(name) from sqlite_master
                                where type='table' and name='%s' ''' % self.table_name)
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(''' create table %s
                                    (id integer primary key autoincrement,
                                     name char(128) not null,
                                     status char(50) not null,
                                     virtualization char(50) not null,
                                     cpu int not null,
                                     ram int not null,
                                     disk int not null,
                                     job text not null,
                                     estimated_time_of_execution int not null,
                                     execution_frequency int not null,
                                     main_job char(128) not null,
                                     require_hardware int not null,
                                     priority_coef int not null,
                                     priority int not null,
                                     created_time datetime not null)''' % self.table_name)
        self.conn.commit()

    def add(self, priority, config):
        self.cursor.execute(''' insert into %s (priority, config) values (%s, '%s') ''' % (self.table_name, priority, config))
        self.conn.commit()

    def delete(self, task_id):
        self.cursor.execute(''' delete from %s where id=%s''' % (self.table_name, task_id))
        self.conn.commit()

    def get_task(self):
        self.cursor.execute(''' select * from %s order by priority desc ''' % self.table_name)
        task = self.cursor.fetchone()
        if task:
            return {
                'id': task[0],
                'priority': task[1],
                'config': task[2]
            }

    def update_priorities(self):
        pass

    def __del__(self):
        self.cursor.close()
        self.conn.close()


Schedule().start()
