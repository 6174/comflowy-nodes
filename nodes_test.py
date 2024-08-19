import json
import unittest
from flowy.nodes import FlowyHttpRequest

class TestFlowyHttpRequest(unittest.TestCase):
    def test_send_http_request_get(self):
        # Arrange
        flowy_http_request = FlowyHttpRequest()
        url = "https://jsonplaceholder.typicode.com/posts/1"
        method = "GET"
        headers = {}
        body = {}
        output_type = "TEXT"

        # Act
        result = flowy_http_request.send_http_request(
            url, method, headers, body
        )
        
        # Parse the result
        parsed_result = result["result"][0]

        print(parsed_result)
        
        # Assert
        self.assertIn("userId", parsed_result)
        self.assertIn("id", parsed_result)
        self.assertIn("title", parsed_result)
        self.assertIn("body", parsed_result)

    def test_send_http_request_post(self):
        # Arrange
        flowy_http_request = FlowyHttpRequest()
        url = "https://jsonplaceholder.typicode.com/posts"
        method = "POST"
        headers = {"Content-type": "application/json; charset=UTF-8"}
        body = {"title": "foo", "body": "bar", "userId": 1}
        output_type = "TEXT"

        # Act
        result = flowy_http_request.send_http_request(
            url, method, headers, body
        )

        # Parse the result
        parsed_result = result["result"][0]

        print(parsed_result)
        # Assert
        self.assertIn("id", parsed_result)
        self.assertEqual(parsed_result["title"], "foo")
        self.assertEqual(parsed_result["body"], "bar")
        self.assertEqual(parsed_result["userId"], 1)

    # Add more tests for PUT, DELETE, PATCH, and error handling


if __name__ == "__main__":
    unittest.main()
