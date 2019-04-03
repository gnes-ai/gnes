import sys

import zmq
import zmq.decorators as zmqd

from gnes.messaging import send_message, Message


@zmqd.context()
@zmqd.socket(zmq.PUSH)
def run(_, sock):
    print('send to port %d' % int(sys.argv[1]))
    with open('tangshi.txt', encoding='utf8') as fp:
        test_data1 = [v for v in fp if v.strip()]
        sock.connect('tcp://0.0.0.0:%d' % int(sys.argv[1]))
        send_message(sock, Message(msg_content=test_data1))


if __name__ == '__main__':
    run()
