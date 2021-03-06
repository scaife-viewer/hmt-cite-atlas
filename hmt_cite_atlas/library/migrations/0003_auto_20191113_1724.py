# Generated by Django 2.2.6 on 2019-11-13 17:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_auto_20191105_2057'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('urn', models.CharField(max_length=255, unique=True)),
                ('position', models.IntegerField()),
                ('idx', models.IntegerField(help_text='0-based index')),
                ('citelibrary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to='library.CITELibrary')),
                ('ctscatalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to='library.CTSCatalog')),
            ],
            options={
                'ordering': ['idx'],
            },
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('urn', models.CharField(max_length=255, unique=True)),
                ('text_content', models.TextField(blank=True, null=True)),
                ('position', models.IntegerField()),
                ('idx', models.IntegerField(help_text='0-based index')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='library.Book')),
                ('citelibrary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='library.CITELibrary')),
                ('ctscatalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='library.CTSCatalog')),
            ],
            options={
                'ordering': ['idx'],
            },
        ),
        migrations.CreateModel(
            name='Scholion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('urn', models.CharField(max_length=255, unique=True)),
                ('position', models.IntegerField()),
                ('idx', models.IntegerField(help_text='0-based index')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scholia', to='library.Book')),
                ('citelibrary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scholia', to='library.CITELibrary')),
                ('ctscatalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scholia', to='library.CTSCatalog')),
            ],
            options={
                'verbose_name_plural': 'Scholia',
                'ordering': ['idx'],
            },
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('urn', models.CharField(max_length=255, unique=True)),
                ('text_content', models.TextField(blank=True, null=True)),
                ('position', models.IntegerField()),
                ('idx', models.IntegerField(help_text='0-based index')),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='library.Book')),
                ('citelibrary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='library.CITELibrary')),
                ('ctscatalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='library.CTSCatalog')),
                ('scholion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='library.Scholion')),
            ],
            options={
                'ordering': ['idx'],
            },
        ),
        migrations.DeleteModel(
            name='CTSDatum',
        ),
    ]
