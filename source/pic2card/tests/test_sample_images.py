import json
from tests.utils import (sample_images, get_response,
                         img_to_base64, set_image_path)
from tests.test_predict_json import BaseAPITest


class TestSampleImages(BaseAPITest):
    """ Basic Tests that run for a list of sample images."""

    @classmethod
    def setUpClass(cls):
        super(TestSampleImages, cls).setUpClass()
        cls.api = "/predict_json"
        cls.response = get_response(cls.client, cls.api, cls.headers, cls.data)
        cls.output = json.loads(cls.response.data)

    def test_status_code(self):
        """ checks if the response has a success status code 200 """
        for image in sample_images:
            self.data = img_to_base64(set_image_path(image))
            self.assertEqual(self.response.status_code, 200)

    def test_response(self):
        """ checks if the response is not empty or None """
        for image in sample_images:
            self.data = img_to_base64(set_image_path(image))
            self.assertEqual(bool(self.output), True)
            self.assertIsNone(self.output["error"])
