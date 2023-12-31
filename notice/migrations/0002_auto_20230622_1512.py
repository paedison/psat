# Generated by Django 3.2.19 on 2023-06-22 06:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notice', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='contents',
            new_name='content',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='hits',
            new_name='hit',
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField(verbose_name='내용')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='작성일')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('post', models.ForeignKey(db_column='post_id', on_delete=django.db.models.deletion.CASCADE, to='notice.post', verbose_name='게시글')),
                ('user', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='사용자 ID')),
            ],
        ),
    ]
