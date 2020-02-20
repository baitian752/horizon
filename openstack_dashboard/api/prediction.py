import os
import pytz
from datetime import datetime

import numpy as np
from sklearn.externals import joblib

from horizon.utils.memoized import memoized

from keystoneauth1 import identity
from keystoneauth1 import session

from gnocchiclient import client as gnocchi_client
from openstack_dashboard.api import base
from openstack_dashboard.api import _nova


def gen_model(datapath, modelpath):

    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    # from sklearn.metrics import accuracy_score

    data = np.loadtxt(datapath, delimiter=',', skiprows=1)
    X = data[:, 0:-1]
    y = data[:, -1]

    rfc = RandomForestClassifier(n_estimators=100, \
        random_state=np.random.randint(0, 99))
    rfc.fit(X, y)

    joblib.dump(rfc, modelpath)


datapath='openstack_dashboard/local/data/prediction_train.csv'
modelpath='openstack_dashboard/local/data/model.m'

if not os.path.exists(modelpath):
    gen_model(datapath, modelpath)

rfc = joblib.load(modelpath)

gmt8 = pytz.timezone('Asia/Shanghai')
get_microversion = _nova.get_microversion


def get_auth_params_from_request(request):
    """Extracts properties needed by gnocchiclient call from the request object.

    These will be used to memoize the calls to gnocchiclient.
    """
    return (
        request.user.username,
        request.user.domain_name or 'default',
        request.user.token.id,
        base.url_for(request, 'identity')
    )


@memoized
def gnocchiclient(request):
    (
        username,
        domain_name,
        token_id,
        auth_url
    ) = get_auth_params_from_request(request)
    auth = identity.Token(auth_url=auth_url, token=token_id, \
        project_name=username, project_domain_name=domain_name)
    sess = session.Session(auth=auth)
    return gnocchi_client.Client(version='1', session=sess)


@memoized
def novaclient(request):
    microversion = get_microversion(request, ("instance_description",
                                              "auto_allocated_network"))
    return _nova.novaclient(request, version=microversion)


def get_data(request):

    nova = novaclient(request)
    gnocchi = gnocchiclient(request)

    data = []
    for server in nova.servers.list():
        metrics = gnocchi.resource.get('instance', server.id)['metrics'].keys()
        if not set(['cpu', 'memory.usage', 'compute.instance.booting.time']) \
            .issubset(set(metrics)):
            continue
        created = datetime.strptime(server.created, '%Y-%m-%dT%H:%M:%SZ')
        delta = datetime.now(pytz.utc) - pytz.utc.localize(created)
        if delta.total_seconds() < 1300:
            continue
        flavor = nova.flavors.get(server.flavor['id'])
        vcpus = flavor.vcpus
        divisor = vcpus * 3e9
        cpu_usage = gnocchi.aggregates.fetch(operations= \
            '(/ (metric cpu rate:mean) %s)' % divisor, search='id=%s' \
            % server.id)['measures'][server.id]['cpu']['rate:mean']
        memory_usage = gnocchi.aggregates.fetch(operations= \
            '(metric memory.usage mean)', search='id=%s' % server.id) \
            ['measures'][server.id]['memory.usage']['mean']
        disk_ephemeral_size = flavor.ephemeral
        disk_root_size = flavor.disk
        compute_instance_booting_time = gnocchi.aggregates.fetch(operations= \
            '(metric compute.instance.booting.time mean)', search='id=%s' % \
            server.id)['measures'][server.id]['compute.instance.booting.time'] \
            ['mean']

        if not (vcpus and cpu_usage and memory_usage and disk_root_size and \
            compute_instance_booting_time):
            continue

        cn = len(cpu_usage)
        mn = len(memory_usage)

        if cn < 2 or mn < 2:
            continue

        d1 = cpu_usage[0][0] - memory_usage[0][0]
        d2 = cpu_usage[-1][0] - memory_usage[-1][0]
        if d1.total_seconds() > 0:
            memory_usage = memory_usage[1:]
        elif d1.total_seconds() < 0:
            cpu_usage = cpu_usage[1:]
        if d2.total_seconds() > 0:
            cpu_usage = cpu_usage[:-1]
        elif d2.total_seconds() < 0:
            memory_usage = memory_usage[:-1]

        cn = len(cpu_usage)
        mn = len(memory_usage)

        if cn > 100:
            cpu_usage = cpu_usage[-100:]
            memory_usage = memory_usage[-100:]
            cn = 100

        times = [item[0].astimezone(gmt8).strftime("%m-%d %H:%M") \
            for item in cpu_usage]
        cpu_usage = [item[2] for item in cpu_usage]
        vcpus = [vcpus] * cn
        memory_usage = [item[2] for item in memory_usage]
        disk_ephemeral_size = [disk_ephemeral_size] * cn
        disk_root_size = [disk_root_size] * cn

        compute_instance_booting_time = \
            [compute_instance_booting_time[0][2]] * cn

        X = np.array([
            cpu_usage, vcpus, memory_usage, disk_ephemeral_size, \
            disk_root_size, compute_instance_booting_time
        ]).T
        y = rfc.predict_proba(X)

        data.append({
            'id': server.id,
            'name': server.name,
            'data': {
                'times': times,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'y': [item[1] * 100 for item in y]
            }
        })

    return data
