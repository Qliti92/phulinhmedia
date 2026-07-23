from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0005_project_financial_fields")]

    operations = [
        migrations.RemoveField(model_name="project", name="cost"),
        migrations.RemoveField(model_name="project", name="revenue"),
        migrations.AddField(
            model_name="project",
            name="financial_result",
            field=models.CharField(
                blank=True,
                choices=[("profit", "Lãi"), ("loss", "Lỗ")],
                max_length=10,
                verbose_name="Kết quả lãi/lỗ",
            ),
        ),
    ]
