# Generated by Django 5.1 on 2024-09-05 06:48

import a_psat.models.lecture_models
import ckeditor.fields
import ckeditor_uploader.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_psat', '0004_alter_problemcollection_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=a_psat.models.lecture_models.subject_choice, default='언어', max_length=2)),
                ('title', models.CharField(blank=True, max_length=20, null=True)),
                ('sub_title', models.CharField(blank=True, max_length=50, null=True)),
                ('youtube_id', models.CharField(blank=True, max_length=20, null=True)),
                ('content', ckeditor_uploader.fields.RichTextUploadingField(default='')),
                ('order', models.SmallIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '강의',
                'verbose_name_plural': '강의',
                'db_table': 'a_psat_lecture',
                'ordering': ['subject', 'order'],
            },
        ),
        migrations.CreateModel(
            name='LectureTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='name')),
                ('slug', models.SlugField(allow_unicode=True, max_length=100, unique=True, verbose_name='slug')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '강의 태그',
                'verbose_name_plural': '강의 태그',
                'db_table': 'a_psat_lecture_tag',
            },
        ),
        migrations.AlterModelOptions(
            name='problem',
            options={'ordering': ['-year', 'id'], 'verbose_name': '01_문제', 'verbose_name_plural': '01_문제'},
        ),
        migrations.AlterModelOptions(
            name='problemcollection',
            options={'ordering': ['user', 'order'], 'verbose_name': '09_컬렉션', 'verbose_name_plural': '09_컬렉션'},
        ),
        migrations.AlterModelOptions(
            name='problemcollectionitem',
            options={'ordering': ['collection__user', 'collection', 'order'], 'verbose_name': '10_컬렉션 문제', 'verbose_name_plural': '10_컬렉션 문제'},
        ),
        migrations.AlterModelOptions(
            name='problemlike',
            options={'ordering': ['-id'], 'verbose_name': '03_즐겨찾기', 'verbose_name_plural': '03_즐겨찾기'},
        ),
        migrations.AlterModelOptions(
            name='problemmemo',
            options={'ordering': ['-id'], 'verbose_name': '06_메모', 'verbose_name_plural': '06_메모'},
        ),
        migrations.AlterModelOptions(
            name='problemopen',
            options={'ordering': ['-id'], 'verbose_name': '02_확인기록', 'verbose_name_plural': '02_확인기록'},
        ),
        migrations.AlterModelOptions(
            name='problemrate',
            options={'ordering': ['-id'], 'verbose_name': '04_난이도', 'verbose_name_plural': '04_난이도'},
        ),
        migrations.AlterModelOptions(
            name='problemsolve',
            options={'ordering': ['-id'], 'verbose_name': '05_정답확인', 'verbose_name_plural': '05_정답확인'},
        ),
        migrations.AlterModelOptions(
            name='problemtag',
            options={'verbose_name': '07_태그', 'verbose_name_plural': '07_태그'},
        ),
        migrations.AlterModelOptions(
            name='problemtaggeditem',
            options={'verbose_name': '08_태그 문제', 'verbose_name_plural': '08_태그 문제'},
        ),
        migrations.CreateModel(
            name='LectureComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', ckeditor.fields.RichTextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('hit', models.IntegerField(default=1, verbose_name='조회수')),
                ('is_active', models.BooleanField(default=True)),
                ('lecture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='a_psat.lecture')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reply_comments', to='a_psat.lecturecomment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='psat_lecture_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'a_psat_lecture_comment',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='LectureOpen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lecture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opens', to='a_psat.lecture')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='psat_lecture_opens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '강의 확인기록',
                'verbose_name_plural': '강의 확인기록',
                'db_table': 'a_psat_lecture_open',
            },
        ),
        migrations.CreateModel(
            name='LectureLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_liked', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('lecture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='a_psat.lecture')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='psat_lecture_likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'a_psat_lecture_like',
                'ordering': ['-id'],
                'constraints': [models.UniqueConstraint(fields=('user', 'lecture'), name='unique_psat_lecture_like')],
                'unique_together': {('user', 'lecture')},
            },
        ),
        migrations.CreateModel(
            name='LectureMemo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', ckeditor.fields.RichTextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('lecture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memos', to='a_psat.lecture')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lecture_memos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'a_psat_lecture_memo',
                'ordering': ['-id'],
                'constraints': [models.UniqueConstraint(fields=('user', 'lecture'), name='unique_psat_lecture_memo')],
            },
        ),
        migrations.CreateModel(
            name='LectureTaggedItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('content_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_lectures', to='a_psat.lecture')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_items', to='a_psat.lecturetag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='psat_tagged_lectures', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '태그된 강의',
                'verbose_name_plural': '태그된 강의',
                'db_table': 'a_psat_lecture_tagged_item',
                'constraints': [models.UniqueConstraint(fields=('tag', 'content_object', 'user'), name='unique_psat_lecture_tagged_item')],
            },
        ),
    ]