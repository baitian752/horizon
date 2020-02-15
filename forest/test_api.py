from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client
from gnocchiclient import client as gnocchi_client


admin_openrc = '/etc/kolla/admin-openrc.sh'

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

auth = identity.Password(**get_credential(admin_openrc=admin_openrc))
sess = session.Session(auth=auth)

gnocchi = gnocchi_client.Client(version='1', session=sess)
nova = nova_client.Client(version='2', session=sess)
server_id = nova.servers.list()[0].id
server = nova.servers.get(server_id)
flavor = nova.flavors.get(server.flavor.get('id'))
divisor = flavor.vcpus * 3e9

# cpu_usage
gnocchi.aggregates.fetch(operations='(/ (metric cpu rate:mean) %s)' % divisor, search='id=%s' % server_id)

# vcpus
flavor.vcpus

# memory_usage
gnocchi.aggregates.fetch(operations='(metric memory.usage mean)', search='id=%s' % server_id)

# disk.ephemeral.size
flavor.ephemeral

# disk.root.size
flavor.disk

# compute.instance.booting.time
gnocchi.aggregates.fetch(operations='(metric compute.instance.booting.time mean)', search='id=%s' % server_id)