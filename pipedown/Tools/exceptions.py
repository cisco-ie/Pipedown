"""Custom exceptions for Pipedown."""
import json
from grpc.framework.interfaces.face.face import AbortionError

class GRPCError(Exception):
    """Raised when there is an error returned by the GRPC Client."""
    def __init__(self, err):
        self.err = json.loads(err)
        message = self.err['cisco-grpc:errors']['error'][0]
        if 'error-message' in self.err:
            self.message = 'A gRPC error occurred: %s', message['error-message']
        elif 'error-tag' in self.err:
            self.message = 'A gRPC error occurred: %s', message['error-tag']

class ProtocolError(Exception):
    """Raised when an invalid protocol is submitted."""
    def __init__(self, protocol):
        self.protocol = protocol
        self.message = "Invalid protocol type '%s'.", protocol

class ConnectionError(AbortionError):
