from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from .models import Project


class ProjectDeletePermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", password="test", full_name="Admin", role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            email="manager@example.com", password="test", full_name="Manager", role=User.Role.MANAGER
        )
        self.other_manager = User.objects.create_user(
            email="other@example.com", password="test", full_name="Other", role=User.Role.MANAGER
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", password="test", full_name="Staff", role=User.Role.STAFF
        )

    def test_admin_can_delete_any_project(self):
        project = Project.objects.create(domain="admin-delete.example", created_by=self.other_manager)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertRedirects(response, reverse("projects"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_manager_can_delete_project_they_created(self):
        project = Project.objects.create(
            domain="manager-delete.example", manager=self.manager, created_by=self.manager
        )
        self.client.force_login(self.manager)
        response = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertRedirects(response, reverse("projects"))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_manager_cannot_delete_project_created_by_someone_else(self):
        project = Project.objects.create(
            domain="other-manager.example", manager=self.manager, created_by=self.other_manager
        )
        self.client.force_login(self.manager)
        response = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_staff_cannot_delete_project(self):
        project = Project.objects.create(domain="staff-forbidden.example", staff=self.staff, created_by=self.staff)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("project_delete", args=[project.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
