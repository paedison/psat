# Generated by Django 4.2.5 on 2023-12-10 06:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='primestudent',
            name='eoneo_score',
        ),
        migrations.RemoveField(
            model_name='primestudent',
            name='heonbeob_score',
        ),
        migrations.RemoveField(
            model_name='primestudent',
            name='jaryo_score',
        ),
        migrations.RemoveField(
            model_name='primestudent',
            name='psat_score',
        ),
        migrations.RemoveField(
            model_name='primestudent',
            name='sanghwang_score',
        ),
        migrations.AddField(
            model_name='primestudent',
            name='category',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.CreateModel(
            name='PrimeStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('score_eoneo', models.FloatField(blank=True, null=True)),
                ('score_jaryo', models.FloatField(blank=True, null=True)),
                ('score_sanghwang', models.FloatField(blank=True, null=True)),
                ('score_psat', models.FloatField(blank=True, null=True)),
                ('score_psat_avg', models.FloatField(blank=True, null=True)),
                ('score_heonbeob', models.FloatField(blank=True, null=True)),
                ('rank_total_eoneo', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_total_jaryo', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_total_sanghwang', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_total_psat', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_total_heonbeob', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_department_eoneo', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_department_jaryo', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_department_sanghwang', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_department_psat', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_department_heonbeob', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_ratio_total_eoneo', models.FloatField(blank=True, null=True)),
                ('rank_ratio_total_jaryo', models.FloatField(blank=True, null=True)),
                ('rank_ratio_total_sanghwang', models.FloatField(blank=True, null=True)),
                ('rank_ratio_total_psat', models.FloatField(blank=True, null=True)),
                ('rank_ratio_total_heonbeob', models.FloatField(blank=True, null=True)),
                ('rank_ratio_department_eoneo', models.FloatField(blank=True, null=True)),
                ('rank_ratio_department_jaryo', models.FloatField(blank=True, null=True)),
                ('rank_ratio_department_sanghwang', models.FloatField(blank=True, null=True)),
                ('rank_ratio_department_psat', models.FloatField(blank=True, null=True)),
                ('rank_ratio_department_heonbeob', models.FloatField(blank=True, null=True)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='score.primestudent')),
            ],
        ),
    ]