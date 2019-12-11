import time
import threading


from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client
from zunclient import client as zun_client
from neutronclient.v2_0 import client as neutron_client

from openstack_dashboard.api.task_common import get_credential
from openstack_dashboard.api.task_common import Tasks
from openstack_dashboard.api.scaling import Stack

from openstack_dashboard.api import task_common
admin_openrc = task_common.admin_openrc


class Schedule(threading.Thread):

    def __init__(self):
        super(Schedule, self).__init__()
        auth = identity.Password(
            **get_credential(admin_openrc=admin_openrc))
        sess = session.Session(auth=auth)
        # self.glance = glance_client.Client(version='2', session=sess)
        self.nova = nova_client.Client(version='2', session=sess)
        self.zun = zun_client.Client(version='1', session=sess)
        self.neutron = neutron_client.Client(session=sess)
        self.hypervisors = self.nova.hypervisors.list()

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
                    stack = Stack(admin_openrc=admin_openrc)
                    stack.setup_parameters(name, image.name, flavor.name,
                                network['name'], key_name, task_name, user_data)
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
