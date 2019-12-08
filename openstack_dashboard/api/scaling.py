import json
import time
import threading
import datetime

from keystoneauth1 import identity
from keystoneauth1 import session
from heatclient import client as heat_client
# from aodhclient import client as aodh_client
from gnocchiclient import client as gnocchi_client
from novaclient import client as nova_client


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


fetch_option = '(/ (* 100 (metric cpu rate:mean)) %s)'


class Scaling(threading.Thread):

    def __init__(self, admin_openrc='/etc/kolla/admin-openrc.sh'):
        super(Scaling, self).__init__()
        auth = identity.Password(**self.get_credential(admin_openrc=admin_openrc))
        sess = session.Session(auth=auth)
        self.heat = heat_client.Client(version='1', session=sess)
        self.gnocchi = gnocchi_client.Client(version='1', session=sess)
        self.nova = nova_client.Client(version='2', session=sess)

    def run(self):
        while True:
            time.sleep(10)
            for stack in self.heat.stacks.list():
                scale_group = self.heat.resources.get(stack_id=stack.id, resource_name='scale_group')
                links = scale_group.to_dict().get('links')
                nested_url = ''
                for link in links:
                    if link.get('rel') == 'nested':
                        nested_url = link.get('href')
                if not nested_url:
                    break
                scale_data = self.heat.http_client.get(url=nested_url)
                scale_data = json.loads(scale_data.content)
                resources = scale_data.get('stack').get('outputs')[0].get('output_value')
                instances = resources.values()
                scaleup = False
                scaledown = False
                for instance in instances:
                    server = self.nova.servers.get(instance)
                    flavor = self.nova.flavors.get(server.flavor['id'])
                    divisor = 60 * flavor.vcpus * 10 ** 9
                    datas = self.gnocchi.aggregates.fetch(operations=fetch_option % divisor, search='id=%s' % instance)
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
                    if not datas['measures'][instance]['cpu'].get('rate:mean', None):
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
                    self.heat.resources.signal(stack_id=stack.id, resource_name='scaleup_policy')
                if not scaleup and scaledown:
                    self.heat.resources.signal(stack_id=stack.id, resource_name='scaledown_policy')

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
