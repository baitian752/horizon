import json
import time
import threading
import datetime

from keystoneauth1 import identity
from keystoneauth1 import session
from heatclient import client as heat_client
from gnocchiclient import client as gnocchi_client
from novaclient import client as nova_client
from zunclient import client as zun_client

from openstack_dashboard.api.task_common import get_credential
from openstack_dashboard.api.task_common import Tasks


stack_template = {
    'files': {},
    'disable_rollback': True,
    'parameters': {
        u'name': u'instance name',
        u'image': u'cirros',
        u'flavor': u'm1.tiny',
        u'network': u'demo-net',
        u'key_name': u'mykey',
        u'task_name': u'task name',
        u'user_data': u'#!/bin/bash\necho Hello OpenStack\n'
    },
    'stack_name': u'stack-name',
    'environment': {},
    'template': {
        u'heat_template_version': u'2016-10-14',
        u'description': u'Example auto scale group and policy',
        u'parameters': {
            u'name': {
                u'default': u'instance name',
                u'type': u'string',
                u'description': u'instance name'
            },
            u'image': {
                u'default': u'cirros',
                u'type': u'string',
                u'description': u'image used to create instance'
            },
            u'flavor': {
                u'default': u'm1.tiny',
                u'type': u'string',
                u'description': u'instance flavor to be used'
            },
            u'network': {
                u'default': u'demo-net',
                u'type': u'string',
                u'description': u'project network to attach instance to'
            },
            u'external_network': {
                u'default': u'public1',
                u'type': u'string',
                u'description': u'network used for floating IPs'
            },
            u'key_name': {
                u'default': u'mykey',
                u'type': u'string',
                u'description': u'keypair to be used'
            },
            u'task_name': {
                u'default': u'task name',
                u'type': u'string',
                u'description': u'task name'
            },
            u'user_data': {
                u'default': u'#!/bin/bash\necho Hello OpenStack\n',
                u'type': u'string',
                u'description': u'user data'
            }
        },
        u'resources': {
            u'scale_group': {
                u'type': u'OS::Heat::AutoScalingGroup',
                u'properties': {
                    u'min_size': 1,
                    u'desired_capacity': 1,
                    u'cooldown': 60,
                    u'resource': {
                        u'type': u'OS::Nova::Server',
                        u'properties': {
                            u'name': {
                                u'get_param': u'name'
                            },
                            u'image': {
                                u'get_param': u'image'
                            },
                            u'flavor': {
                                u'get_param': u'flavor'
                            },
                            u'networks': [
                                {
                                    u'network': {
                                        u'get_param': u'network'
                                    }
                                }
                            ],
                            u'key_name': {
                                u'get_param': u'key_name'
                            },
                            u'metadata': {
                                u'metering.server_group': {
                                    u'get_param': u'OS::stack_id'
                                },
                                u'task_name': {
                                    u'get_param': u'task_name'
                                }
                            },
                            u'user_data_format': u'RAW',
                            u'user_data': {
                                u'get_param': u'user_data'
                            }
                        }
                    },
                    u'max_size': 3
                }
            },
            u'scaleup_policy': {
                u'type': u'OS::Heat::ScalingPolicy',
                u'properties': {
                    u'auto_scaling_group_id': {
                        u'get_resource': u'scale_group'
                    },
                    u'adjustment_type': u'change_in_capacity',
                    u'scaling_adjustment': 1,
                    u'cooldown': 60
                }
            },
            u'scaledown_policy': {
                u'type': u'OS::Heat::ScalingPolicy',
                u'properties': {
                    u'auto_scaling_group_id': {
                        u'get_resource': u'scale_group'
                    },
                    u'adjustment_type': u'change_in_capacity',
                    u'scaling_adjustment': -1,
                    u'cooldown': 60
                }
            }
        },
        u'outputs': {
            u'scaleup_policy_signal_url': {
                u'value': {
                    u'get_attr': [u'scaleup_policy', u'signal_url']
                }
            },
            u'scaledown_policy_signal_url': {
                u'value': {
                    u'get_attr': [u'scaledown_policy', u'signal_url']
                }
            }
        }
    }
}


class UTC(datetime.tzinfo):
    # can be configured here
    _offset = datetime.timedelta(seconds=0)
    _dst = datetime.timedelta(0)
    _name = "+00:00"

    def utcoffset(self, dt):
        return self.__class__._offset

    def dst(self, dt):
        return self.__class__._dst

    def tzname(self, dt):
        return self.__class__._name


class Stack(object):

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        auth = identity.Password(**get_credential(
                                 admin_openrc=admin_openrc))
        sess = session.Session(auth=auth)
        self.heat = heat_client.Client(version='1', session=sess)
        self.stack_template = dict(stack_template)

    def setup_parameters(self, name, image, flavor, network,
                         key_name, task_name, user_data):
        self.stack_template['parameters']['name'] = name
        self.stack_template['parameters']['image'] = image
        self.stack_template['parameters']['flavor'] = flavor
        self.stack_template['parameters']['network'] = network
        self.stack_template['parameters']['key_name'] = key_name
        self.stack_template['parameters']['task_name'] = task_name
        self.stack_template['parameters']['user_data'] = user_data
        self.stack_template['stack_name'] = '-'.join(task_name.split())

    def launch(self):
        self.heat.stacks.create(**self.stack_template)


class Scaling(threading.Thread):

    fetch_option = '(/ (* 100 (metric cpu rate:mean)) %s)'

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        super(Scaling, self).__init__()
        auth = identity.Password(**get_credential(
                                 admin_openrc=admin_openrc))
        sess = session.Session(auth=auth)
        self.heat = heat_client.Client(version='1', session=sess)
        self.gnocchi = gnocchi_client.Client(version='1', session=sess)
        self.nova = nova_client.Client(version='2', session=sess)
        self.zun = zun_client.Client(version='1', session=sess)

    def run(self):
        self.tasks = Tasks('tasks')
        i = 1
        while True:
            print '*' * 50
            print i
            print '*' * 50
            i += 1
            time.sleep(10)
            self.scaling_vms()
            self.scaling_containers()

    def scaling_vms(self):
        for stack in self.heat.stacks.list():
            scale_group = self.heat.resources.get(stack_id=stack.id,
                                                  resource_name='scale_group')
            links = scale_group.to_dict().get('links')
            nested_url = ''
            for link in links:
                if link.get('rel') == 'nested':
                    nested_url = link.get('href')
            if not nested_url:
                break
            scale_data = self.heat.http_client.get(url=nested_url)
            scale_data = json.loads(scale_data.content)
            resources = scale_data.get('stack').get('outputs')[0]. \
                        get('output_value')
            instances = resources.values()
            scaleup = False
            scaledown = False
            for instance in instances:
                server = self.nova.servers.get(instance)
                flavor = self.nova.flavors.get(server.flavor['id'])
                divisor = 60 * flavor.vcpus * 10 ** 9
                datas = self.gnocchi.aggregates.fetch(operations= \
                    self.fetch_option % divisor, search='id=%s' % instance)
                if not datas.get('measures', None):
                    scaleup = False
                    scaledown = False
                    break
                if not datas['measures'].get(instance, None):
                    scaleup = False
                    scaledown = False
                    break
                if not datas['measures'][instance].get('cpu', None):
                    scaleup = False
                    scaledown = False
                    break
                if not datas['measures'][instance]['cpu']. \
                       get('rate:mean', None):
                    scaleup = False
                    scaledown = False
                    break
                measure = datas['measures'][instance]['cpu']['rate:mean'][-1]
                if not measure:
                    scaleup = False
                    scaledown = False
                    break
                last_measure_time = measure[0]
                last_measure_value = measure[2]
                now = datetime.datetime.now(UTC())
                if (now - last_measure_time).seconds > 300:
                    scaleup = False
                    scaledown = False
                    break
                if last_measure_value < 20:
                    if scaleup:
                        scaleup = False
                        scaledown = False
                        break
                    scaledown = True
                if last_measure_value > 80:
                    if scaledown:
                        scaleup = False
                        scaledown = False
                        break
                    scaleup = True
            if scaleup and not scaledown:
                self.heat.resources.signal(stack_id=stack.id,
                                           resource_name='scaleup_policy')
            if not scaleup and scaledown:
                self.heat.resources.signal(stack_id=stack.id,
                                           resource_name='scaledown_policy')

    def scaling_containers(self):
        container_uuids = self.tasks.get_autoscaling_containers()
        print '*' * 50
        print container_uuids
        print '*' * 50
        for uuid in container_uuids:
            try:
                container = self.zun.containers.get(uuid)
                if container.status == 'Running':
                    stats = self.zun.containers.stats(uuid)
                    if stats['MEM %'] < 20:
                        mem_limit = stats['MEM LIMIT(MiB)']
                        if mem_limit > 512:
                            self.zun.containers.update(uuid,
                                                       memory=mem_limit // 2)
                    elif stats['MEM %'] > 80:
                        mem_limit = stats['MEM LIMIT(MiB)']
                        self.zun.containers.update(uuid, memory=mem_limit * 2)
            except Exception as e:
                print e.message
                self.tasks.delete_autoscaling_container(uuid)
