import json

import pika
from pika.exceptions import AMQPConnectionError

import exceptions
import time

from joulupukki.common.datamodel.build import Build
from joulupukki.common.datamodel.project import Project
from joulupukki.common.datamodel.user import User
import logging


class Carrier(object):
    def __init__(self, server, port, username, password, vhost, exchange,
                 queue="default.queue"):
        """queues:
        * builds
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.exchange = exchange
        self.closing = False

        self.queue = queue
        self.connect()

    def connect(self):
        logging.info("Connecting to rabbitmq server...")
        rabbit_credentials = pika.PlainCredentials(self.username, self.password, self.vhost)
        parameters = pika.ConnectionParameters(
                host=self.server,
                port=self.port,
                credentials=rabbit_credentials,
                )
        try:
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logging.info("Connected to %s:%s.", self.server, self.port)
        except Exception:
            logging.error("Can't connect to rabbitmq server. "
                          "Probable authentication error")
            return False
        return True

    def on_connection_closed(self):
        self.channel = None
        logging.info("RabbitMQ connection closed.")
        if not self.closing:
            while not self.connect():
                logging.info("RabbitMQ connection closed, reopening in 5 seconds.")
                time.sleep(5)
            self.declare_queue(self.queue)
            self.declare_builds()

    def declare_builds(self):
        self.channel.queue_declare(queue='builds')

    def declare_queue(self, queue='default.queue'):
        self.channel.queue_declare(queue=queue)

    def send_message(self, message, queue='default.queue'):
        try:
            self.channel.basic_publish(exchange='', routing_key=queue,
                                       body=json.dumps(message))
        except AMQPConnectionError:
            self.on_connection_closed()
            self.channel.basic_publish(exchange='', routing_key=queue,
                                       body=json.dumps(message))
        except Exception as exp:
            logging.error(exp)
            return False
        return True

    def send_build(self, build):
        try:
            self.channel.basic_publish(exchange='', routing_key='builds.queue',
                                       body=json.dumps(build.dumps()))
        except AMQPConnectionError:
            self.on_connection_closed()
            self.channel.basic_publish(exchange='', routing_key='builds.queue',
                                       body=json.dumps(build.dumps()))
        except Exception as exp:
            logging.error(exp)
            return False
        return True

    def get_build(self):
        build_data = self.get_message('builds.queue')
        if build_data is not None:
            build = Build(build_data)
            build.user = User.fetch(build_data['username'], sub_objects=False)
            if build.user is None:
                return None
            build.project = Project.fetch(build.user.username,
                                          build_data['project_name'],
                                          sub_objects=False)
            return build

    def get_message(self, queue):
        message_data = None
        try:
            method_frame, header_frame, body = (
                self.channel.basic_get(queue)
            )
            if body is None:
                return None
            message_data = json.loads(body)
            self.channel.basic_ack(method_frame.delivery_tag)
        except AMQPConnectionError:
            self.on_connection_closed()

            method_frame, header_frame, body = (
                self.channel.basic_get(queue)
            )
            if body is None:
                return None
            message_data = json.loads(body)
            self.channel.basic_ack(method_frame.delivery_tag)

        except Exception as exp:
            logging.error(exp)
            return None

        return message_data
