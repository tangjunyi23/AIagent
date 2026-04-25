import unittest

from audit_api.casing import to_camel, to_snake


class CasingTests(unittest.TestCase):
    def test_to_camel_converts_nested_resource_names(self) -> None:
        payload = {
            "project_id": "project_1",
            "sample_ids": ["sample_1"],
            "policy": {"network_policy": "none"},
        }

        self.assertEqual(
            to_camel(payload),
            {
                "projectId": "project_1",
                "sampleIds": ["sample_1"],
                "policy": {"networkPolicy": "none"},
            },
        )

    def test_to_snake_converts_nested_resource_names(self) -> None:
        payload = {
            "projectId": "project_1",
            "sampleIds": ["sample_1"],
            "policy": {"networkPolicy": "none"},
        }

        self.assertEqual(
            to_snake(payload),
            {
                "project_id": "project_1",
                "sample_ids": ["sample_1"],
                "policy": {"network_policy": "none"},
            },
        )


if __name__ == "__main__":
    unittest.main()
