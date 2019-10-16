# Generated by Django 2.1.4 on 2018-12-14 08:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DC801User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.CharField(db_index=True, max_length=254, unique=True)),
                ('handle', models.CharField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_member', models.BooleanField(default=True, help_text='Designates whether this user is a paying member active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('confirmed_email', models.BooleanField(default=True, help_text='Designates whether this user confirmed there email confirmed.', verbose_name='confirmed')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(blank=True, max_length=254)),
                ('last_name', models.CharField(blank=True, max_length=254)),
                ('phone_number', models.CharField(blank=True, max_length=11)),
                ('confirmation_code', models.CharField(blank=True, max_length=33)),
                ('subscription_code', models.CharField(blank=True, max_length=254)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='BrainTree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='MemberLevel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('level', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=254)),
                ('description', models.CharField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='ResetPasswordCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.PositiveIntegerField()),
                ('used', models.BooleanField(default=False)),
                ('confirmation_code', models.CharField(blank=True, max_length=33)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=19)),
                ('payment_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='payment_date')),
                ('timestamp', models.PositiveIntegerField()),
                ('success', models.BooleanField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='dc801user',
            name='member_level',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='members.MemberLevel'),
        ),
        migrations.AddField(
            model_name='dc801user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]