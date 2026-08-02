import unittest
from unittest.mock import patch

from tools.build.blender import BlenderMcp, response_error


class FakeConnection:
    def __init__(self, chunks, close_when_empty=True):
        self.chunks = list(chunks)
        self.close_when_empty = close_when_empty

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def settimeout(self, _timeout):
        pass

    def sendall(self, _request):
        pass

    def recv(self, _size):
        if self.chunks:
            return self.chunks.pop(0)
        if self.close_when_empty:
            return b""
        raise AssertionError("MCP client read past the complete JSON response")


class BlenderMcpResponseTests(unittest.TestCase):
    def test_execute_reads_fragmented_json_until_socket_closes(self):
        connection = FakeConnection(
            [b'{"status":"su', b'ccess","result":{}}', b""]
        )
        with patch("tools.build.blender.socket.create_connection", return_value=connection):
            response = BlenderMcp("127.0.0.1", 9876, attempts=1).execute("print('ok')")
        self.assertEqual(response, '{"status":"success","result":{}}')

    def test_execute_returns_complete_json_without_waiting_for_socket_close(self):
        connection = FakeConnection([b'{"status":"success","result":{}}'], close_when_empty=False)
        with patch("tools.build.blender.socket.create_connection", return_value=connection):
            response = BlenderMcp("127.0.0.1", 9876, attempts=1).execute("print('ok')")
        self.assertEqual(response, '{"status":"success","result":{}}')

    def test_json_error_response_is_rejected(self):
        self.assertEqual(
            response_error('{"status":"error","message":"Code execution error"}'),
            "Code execution error",
        )

    def test_success_response_is_accepted(self):
        self.assertIsNone(response_error('{"status":"success","result":{}}'))

    def test_textual_runtime_error_is_rejected(self):
        self.assertIsNotNone(response_error("Traceback: AssertionError"))


if __name__ == "__main__":
    unittest.main()
