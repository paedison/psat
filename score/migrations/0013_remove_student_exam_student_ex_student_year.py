# Generated by Django 4.2.5 on 2023-10-05 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0012_alter_unit_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='exam',
        ),
        migrations.AddField(
            model_name='student',
            name='ex',
            field=models.CharField(choices=[('행시', '5급공채/행정고시'), ('외시', '외교원/외무고시'), ('칠급', '7급공채'), ('민경', '민간경력'), ('견습', '견습'), ('입시', '입법고시')], default='행시', max_length=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='year',
            field=models.IntegerField(choices=[(2004, '2004년'), (2005, '2005년'), (2006, '2006년'), (2007, '2007년'), (2008, '2008년'), (2009, '2009년'), (2010, '2010년'), (2011, '2011년'), (2012, '2012년'), (2013, '2013년'), (2014, '2014년'), (2015, '2015년'), (2016, '2016년'), (2017, '2017년'), (2018, '2018년'), (2019, '2019년'), (2020, '2020년'), (2021, '2021년'), (2022, '2022년'), (2023, '2023년')], default=2023),
            preserve_default=False,
        ),
    ]