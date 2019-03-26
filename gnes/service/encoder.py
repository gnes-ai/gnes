import zmq
import zmq.decorators as zmqd

from .base import BaseService, MessageType


class EncoderService(BaseService):
    @zmqd.context()
    @zmqd.socket(zmq.PULL)
    @zmqd.socket(zmq.PUSH)
    def _run(self, _, frontend, sink):
        frontend.bind('tcp://%s:%d' % (self.args.address_encoder, self.args.port_encoder))
        sink.bind('tcp://%s:%d' % (self.args.address_sink, self.args.port_sink))

        # receive job from frontend, send checksum to sink and do encoding
        while True:
            try:
                request = frontend.recv_multipart()
                client_id, req_id, msg_type, msg_content = request
            except ValueError:
                self.logger.error('received a wrongly-formatted request (expected 4 frames, got %d)' % len(request))
                self.logger.error('\n'.join('field %d: %s' % (idx, k) for idx, k in enumerate(request)), exc_info=True)
            else:
                if msg_type == MessageType.terminate:
                    break
                elif msg_type == MessageType.is_ready:
                    # propagate to out
                    pass
                elif msg_type == MessageType.show_status:
                    # propagate to out
                    pass
                elif msg_type == MessageType.data:
                    # do actual job
                    pass

    def _send_close_signal(self):
        pass
