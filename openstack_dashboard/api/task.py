import time
import threading
import sqlite3

from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client
from zunclient import client as zun_client
from neutronclient.v2_0 import client as neutron_client

from openstack_dashboard.api.scaling import Stack


def get_credential(admin_openrc):
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


class Schedule(threading.Thread):

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        super(Schedule, self).__init__()
        auth = identity.Password(
            **get_credential(admin_openrc=admin_openrc))
        sess = session.Session(auth=auth)
        # self.glance = glance_client.Client(version='2', session=sess)
        self.nova = nova_client.Client(version='2', session=sess)
        self.zun = zun_client.Client(version='1', session=sess)
        self.neutron = neutron_client.Client(session=sess)
        self.hypervisors = self.nova.hypervisors.list()
        self.admin_openrc = admin_openrc

    def run(self):
        time.sleep(10)
        self.tasks = Tasks('tasks')
        while True:
            time.sleep(3)
            task = self.tasks.get_task()
            while not task:
                time.sleep(3)
                task = self.tasks.get_task()
            if task['virtualization'] == 'Virtual Machine':
                image = self.get_image()
                name = image.name
                flavor = self.get_flavor(task)
                network = self.get_network()
                nics = [{'net-id': network['id']}]
                key_name = self.get_keypair()
                task_name = task['name']
                meta = {'task_name': task_name}
                user_data = task['job']
                self.check_resources(flavor.vcpus, flavor.ram, flavor.disk)
                if task['auto_scaling'] == 'Yes':
                    stack = Stack(admin_openrc=self.admin_openrc)
                    stack.setup_parameters(name, image.name, flavor.name,
                                network['name'], key_name, task, user_data)
                    stack.launch()
                else:
                    self.run_server(name, image, flavor, user_data,
                                    meta, nics, key_name)
            elif task['virtualization'] == 'Docker':
                name = task['name']
                image = 'ubuntu'
                command = task['job'].split()
                cpu = task['cpu']
                memory = task['ram']
                self.check_resources(cpu, memory, 1)
                container = self.run_container(name, image, command,
                                               cpu, memory)
                if task['auto_scaling'] == 'Yes':
                    self.tasks.add_autoscaling_container(container.uuid)
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

    def get_network(self):
        networks = self.neutron.list_networks()['networks']
        network = networks[0]
        for item in networks:
            if not item['router:external']:
                network = item
                break
        return network

    def get_keypair(self):
        keypairs = self.nova.keypairs.list()
        keypair = keypairs[0].name
        for item in keypairs:
            if item.name == 'mykey':
                keypair = item.name
                break
        return keypair

    def run_server(self, name, image, flavor, user_data, meta, nics, key_name):
        self.nova.servers.create(name=name, image=image, flavor=flavor,
                                 userdata=user_data, meta=meta, nics=nics,
                                 key_name=key_name)

    def run_container(self, name, image, command, cpu, memory):
        return self.zun.containers.run(name=name, image=image, command=command,
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
                time.sleep(3)


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
                                     auto_scaling character(4) not null,
                                     created_timestamp real not null)'''
                                     % self.table_name)
        self.cursor.execute(''' select count(name) from sqlite_master
                                where type='table' and name='config' ''')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(''' create table config
                                    (id integer primary key autoincrement,
                                     precedence_schema character(50) 
                                     not null) ''')
            self.cursor.execute(''' insert into config (precedence_schema)
                                    values ('Execution time') ''')
        self.cursor.execute(''' select count(name) from sqlite_master 
                                where type='table' and 
                                name='autoscaling_containers' ''')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute(''' create table autoscaling_containers
                                    (id integer primary key autoincrement,
                                     uuid character(50) not null) ''')
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
                                auto_scaling,
                                created_timestamp
                                ) values 
                                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
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
                             data['auto_scaling'],
                             data['created_timestamp']
                            ))
        self.conn.commit()

    def delete(self, task_id):
        self.cursor.execute(''' delete from %s where id=? '''
                                % self.table_name, (task_id,))
        self.conn.commit()

    def get_task(self):
        precedence_schema = self.get_precedence_schema()
        if precedence_schema == 'Execution time':
            self.cursor.execute(''' select * from %s where status='ready'
                                    and estimated_time_of_execution=
                                    (select min(estimated_time_of_execution) 
                                    from %s where status='ready') order by 
                                    priority desc '''
                                    % (self.table_name, self.table_name))
            tasks = self.cursor.fetchall()
            if not tasks:
                return
            task = tasks[0]
            tasks = [item for item in tasks if item[12] == task[12]]
            for item in tasks:
                if item[14] < task[14]:
                    task = item
        elif precedence_schema == 'Waiting time':
            self.cursor.execute(''' select * from %s where status='ready'
                                    order by created_timestamp asc '''
                                    % self.table_name)
            task = self.cursor.fetchone()
        else: # precedence_schema == 'Priority':
            self.cursor.execute(''' select * from %s where status='ready' and
                                    priority=(select max(priority) from %s
                                    where status='ready') order by 
                                    estimated_time_of_execution asc '''
                                    % (self.table_name, self.table_name))
            tasks = self.cursor.fetchall()
            if not tasks:
                return
            task = tasks[0]
            tasks = [item for item in tasks if item[8] == task[8]]
            for item in tasks:
                if item[8] < task[8]:
                    task = item
        if not task:
            return
        task = list(task)
        if task[3] == 'Auto':
            if task[11] == 'Yes':
                task[3] = 'Virtual Machine'
            elif not task[7]:
                task[3] = 'Docker'
            else:
                self.cursor.execute(''' select * from %s where status='finished'
                                        and job='%s' order by created_timestamp
                                        desc ''' % (self.table_name, task[7]))
                old_task = self.cursor.fetchone()
                if old_task:
                    task[3] = old_task[3]
                else:
                    task[3] = 'Docker'
            self.cursor.execute(''' update %s set virtualization='%s' where
                                    id=%s '''
                                    % (self.table_name, task[3], task[0]))
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
            'auto_scaling': task[13],
            'created_timestamp': task[14]
        }

    def update_status(self, task_id, status):
        self.cursor.execute(''' update %s set status='%s' where id=%s '''
                                % (self.table_name, status, task_id))
        self.conn.commit()

    def get_precedence_schema(self):
        self.cursor.execute(''' select * from config ''')
        precedence_schema = self.cursor.fetchone()[1]
        return precedence_schema

    def update_precedence_schema(self, precedence_schema):
        self.cursor.execute(''' select * from config ''')
        config_id = self.cursor.fetchone()[0]
        self.cursor.execute(''' update config set precedence_schema='%s' where
                                id=%s ''' % (precedence_schema, config_id))
        self.conn.commit()

    def get_autoscaling_containers(self):
        self.cursor.execute(''' select * from autoscaling_containers ''')
        containers = self.cursor.fetchall()
        return [item[1] for item in containers]

    def add_autoscaling_container(self, uuid):
        self.cursor.execute(''' insert into autoscaling_containers (uuid)
                                values (?) ''', (uuid,))
        self.conn.commit()

    def delete_autoscaling_container(self, uuid):
        self.cursor.execute(''' delete from autoscaling_containers where
                                uuid=? ''', (uuid,))
        self.conn.commit()

    def __del__(self):
        self.cursor.close()
        self.conn.close()
