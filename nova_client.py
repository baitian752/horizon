from keystoneauth1 import identity
from keystoneauth1 import session
from novaclient import client as nova_client

admin_openrc='/etc/kolla/admin-openrc.sh'

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
nova = nova_client.Client(version='2', session=sess)
