import json
from tests.utils import (sample_images, get_response,
                         img_to_base64, set_image_path)
from tests.test_predict_json import BaseAPITest


class TestSampleImages(BaseAPITest):
    """ Basic Tests that run for a list of sample images
        for predict_json api.
    """

    def setUp(self):
        super(TestSampleImages, self).setUp()
        self.api = "/predict_json"
        self.response = get_response(self.client, self.api,
                                     self.headers, self.data)
        self.output = json.loads(self.response.data)

    def test_response(self):
        """ checks if the response is success and not none """
        for image in sample_images:
            self.data = img_to_base64(set_image_path(image))
            self.assertEqual(self.response.status_code, 200)
            self.assertEqual(bool(self.output), True)
            self.assertIsNone(self.output["error"])


class TestSampleImagesTemplates(BaseAPITest):
    """ Basic Tests that run for a list of sample images
        for get_card_templates api.
    """

    def setUp(self):
        super(TestSampleImagesTemplates, self).setUp()
        self.api = "/get_card_templates"
        self.response = self.client.get(self.api)
        self.output = json.loads(self.response.data)

    def test_response(self):
        """ checks if the response is success and not none """
        for image in sample_images:
            self.data = img_to_base64(set_image_path(image))
            self.assertEqual(self.response.status_code, 200)
            self.assertEqual(bool(self.output), True)
            key = bool(self.output.get("templates"))
            self.assertTrue(key, msg="Key 'templates' not found")
