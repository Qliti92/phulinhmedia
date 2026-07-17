from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from .models import Task


class TaskDeletePermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", password="test", full_name="Admin", role=User.Role.ADMIN
        )
        self.manager = User.objects.create_user(
            email="manager@example.com", password="test", full_name="Manager", role=User.Role.MANAGER
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", password="test", full_name="Staff", role=User.Role.STAFF
        )

    def test_admin_can_delete_task(self):
        task = Task.objects.create(title="Admin deletes", created_by=self.manager)
        self.client.force_login(self.admin)
        response = self.client.post(reverse("task_delete", args=[task.pk]))
        self.assertRedirects(response, reverse("tasks"))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_manager_cannot_delete_task(self):
        task = Task.objects.create(title="Manager forbidden", created_by=self.manager)
        self.client.force_login(self.manager)
        response = self.client.post(reverse("task_delete", args=[task.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_staff_cannot_delete_task(self):
        task = Task.objects.create(title="Staff forbidden", assignee=self.staff, created_by=self.manager)
        self.client.force_login(self.staff)
        response = self.client.post(reverse("task_delete", args=[task.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
