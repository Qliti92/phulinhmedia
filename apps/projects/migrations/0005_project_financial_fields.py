from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0004_alter_project_registration_link_1")]

    operations = [
        migrations.AddField(
            model_name="project",
            name="cost",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="Chi phí"),
        ),
        migrations.AddField(
            model_name="project",
            name="revenue",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="Doanh thu"),
        ),
        migrations.AlterField(
            model_name="project",
            name="registration_link_1",
            field=models.URLField(blank=True, verbose_name="Link đăng nhập"),
        ),
    ]
