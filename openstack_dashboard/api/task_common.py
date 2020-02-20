import sqlite3


admin_openrc = '/etc/openstack-dashboard/admin-openrc.sh'
database = 'openstack_dashboard/local/data/tack.db'


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


class Tasks(object):

    def __init__(self, table_name):
        self.table_name = table_name
        self.conn = sqlite3.connect(database)
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
