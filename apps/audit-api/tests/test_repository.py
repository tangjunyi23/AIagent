import unittest

from audit_api.mock_service import AuditMockService
from audit_api.repository import InMemoryAuditRepository


class InMemoryAuditRepositoryTests(unittest.TestCase):
    def test_allocate_id_tracks_resource_prefixes_independently(self) -> None:
        repository = InMemoryAuditRepository()

        self.assertEqual(repository.allocate_id("project"), "project_1")
        self.assertEqual(repository.allocate_id("project"), "project_2")
        self.assertEqual(repository.allocate_id("analysis"), "analysis_1")

    def test_mock_service_uses_injected_repository_storage(self) -> None:
        repository = InMemoryAuditRepository()
        service = AuditMockService(repository=repository)

        project = service.create_project({"name": "Firmware Lab"})

        self.assertEqual(project["id"], "project_1")
        self.assertIn("project_1", repository.projects)
        self.assertEqual(repository.projects["project_1"]["name"], "Firmware Lab")


if __name__ == "__main__":
    unittest.main()
