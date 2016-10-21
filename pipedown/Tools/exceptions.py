# Copyright 2016 Cisco Systems All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""Custom exceptions for Pipedown."""
import json

class GRPCError(Exception):
    """Raised when there is an error returned by the GRPC Client."""
    def __init__(self, err):
        self.err = err
        try:
            self.err = json.loads(err)
            message = self.err['cisco-grpc:errors']['error'][0]
            if 'error-message' in self.err:
                self.message = 'A gRPC error occurred: %s', message['error-message']
            elif 'error-tag' in self.err:
                self.message = 'A gRPC error occurred: %s', message['error-tag']
        except TypeError:  #err is a str instead of a JSON object
            self.message = err

class ProtocolError(Exception):
    """Raised when an invalid protocol is submitted."""
    def __init__(self, protocol):
        self.protocol = protocol
        self.message = "Invalid protocol type '%s'.", protocol

