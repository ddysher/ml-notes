import pika
import sys
import json
import os
import time
import rollbar
import threading
import time
from sh import tail
from pika.exceptions import ConnectionClosed

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://backend.riseml.com')
ROLLBAR_ENDPOINT = BACKEND_URL + '/errors/logsidecar/'
CLUSTER_ID = os.environ.get('CLUSTER_ID')
AMQP_URL = os.environ.get('AMQP_URL')
LOG_JOB_ID = os.environ.get('LOG_JOB_ID')
LOG_QUEUE = os.environ.get('LOG_QUEUE')
LOGFILE = os.environ.get('LOGFILE')

channel = None

class WatchLog(threading.Thread):
    daemon = True

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self):
        print("My watch has started: %s" % self.filename)
        while True:
            wait_until_exists(self.filename)
            if open(self.filename, 'r').read():
                # wait a second before terminating
                if channel:
                    channel.close()
                time.sleep(1)
                print("My watch has ended")
                os._exit(0)
            time.sleep(1)


def get_log_channel(amqp_url, queue):
    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
    log_channel = connection.channel()
    log_channel.queue_declare(queue=queue)
    return log_channel


def log(message, amqp_url, queue, job_id):
    global channel
    while True:
        try:
            if not channel:
                channel = get_log_channel(amqp_url, queue)
            channel.basic_publish('',
                                  queue,
                                  json.dumps({'log': job_id,
                                              'msg': message}),
                                  pika.BasicProperties(content_type='text/plain',
                                                       delivery_mode=1))
            break
        except ConnectionClosed as e:
            print('Failed sending log message: %s' % e)
            print('Retrying.')
            channel = None
            time.sleep(1)


def wait_until_exists(filename, sleep_interval=0.3):
    while not os.path.isfile(filename):
        time.sleep(sleep_interval)


def stream_logfile(logfile, amqp_url, queue, job_id):
    for line in tail("-f", "-n+1", logfile, _out_bufsize=1, _iter=True):
        log(line, amqp_url, queue, job_id)


def main():
    print('Waiting for logfile to come up')
    wait_until_exists(LOGFILE)
    print('Streaming logfile')
    stream_logfile(LOGFILE, AMQP_URL, LOG_QUEUE, LOG_JOB_ID)


if __name__ == '__main__':
    if ENVIRONMENT not in ['development', 'test']:
        rollbar.init(
            CLUSTER_ID, # Use cluster id as access token
            ENVIRONMENT,
            endpoint=ROLLBAR_ENDPOINT,
            root=os.path.dirname(os.path.realpath(__file__)))

    if os.environ.get('TERMINATION_LOGFILE'):
        watch_log = WatchLog(os.environ.get('TERMINATION_LOGFILE'))
        watch_log.start()
    if ENVIRONMENT not in ['development', 'test']:
        try:
            main()
        except:
            rollbar.report_exc_info()
            raise
    else:
        main()
