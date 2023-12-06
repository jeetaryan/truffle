#/var/www/api/api.wsgi
#!/usr/bin/python
import sys
sys.path.insert(0,"/var/www/api/api/")

from api import app as application

import time
import threading
import os
from user_agents import parse
import mod_wsgi

current_requests = {}

def event_handler(name, **kwargs):
    if name == 'request_started':
        environ = kwargs['request_environ']

        request_data = mod_wsgi.request_data()
        request_data['environ'] = environ
        request_data['tracked'] = False

        request_id = environ['mod_wsgi.request_id']

        current_requests[request_id] = (environ, kwargs, request_data)

    elif name == 'request_finished':
        request_data = mod_wsgi.request_data()
        environ = request_data['environ']
        request_id = environ['mod_wsgi.request_id']
        del current_requests[request_id]

        if request_data['tracked']:
            print('FINISHED %s %s %s' % (request_id, kwargs['application_time'], environ['REQUEST_URI']))

mod_wsgi.subscribe_events(event_handler)

last_metrics = None

def monitor(*args):
    global last_metrics

    while True:
        current_metrics = mod_wsgi.process_metrics()

        if last_metrics is not None:
            cpu_user_time = (current_metrics['cpu_user_time'] -
                    last_metrics['cpu_user_time'])
            cpu_system_time = (current_metrics['cpu_system_time'] -
                    last_metrics['cpu_system_time'])

            request_busy_time = (current_metrics['request_busy_time'] -
                    last_metrics['request_busy_time'])

            request_threads = current_metrics['request_threads']

            # report data

            item = {}
            item['time'] = time.time()
            item['measurement'] = 'process'
            item['process_group'] = mod_wsgi.process_group
            item['process_id'] = os.getpid()

            fields = {}

            fields['cpu_user_time'] = cpu_user_time
            fields['cpu_system_time'] = cpu_system_time

            fields['request_busy_time'] = request_busy_time
            fields['request_busy_usage'] = (request_busy_time /
                    mod_wsgi.threads_per_process)

            fields['threads_per_process'] = mod_wsgi.threads_per_process
            fields['request_threads'] = request_threads

            item['fields'] = fields

            now = time.time()

            header = False
            for request_id, (environ, kwargs, request_data) in list(current_requests.items()):
                running_duration = now - kwargs['application_start']
                # Dump data for requests running longer than 2.0 seconds.
                if running_duration > 2.0:
                    if not header:
                        print('STATISTICS', item)
                        header = True
                    request_data['tracked'] = True
                    print('RUNNING %s %s %s' % (request_id, running_duration, environ['REQUEST_URI']))

        last_metrics = current_metrics

        current_time = current_metrics['current_time']
        delay = max(0, (current_time + 1.0) - time.time())
        time.sleep(delay)

thread = threading.Thread(target=monitor)
thread.setDaemon(True)
thread.start()
