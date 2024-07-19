import json
from sqlite3 import IntegrityError

import pandas as pd
import pytz
from dateutil import parser
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Update or create model instances from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str, help='The app label of the model')
        parser.add_argument('file_name', type=str, help='The path to the Excel file')

    def handle(self, *args, **options):
        app_label = options['app_label']
        file_name = options['file_name']

        self.stdout.write(f"Reading Excel file: {file_name}")

        try:
            data_frames = read_excel_sheets(file_name)
        except CommandError as e:
            self.stderr.write(str(e))
            return

        total_created = 0
        total_updated = 0

        for sheet_name, df in data_frames.items():
            self.stdout.write(f"================")
            self.stdout.write(f"Processing sheet: {sheet_name}")

            try:
                model = get_model(app_label, sheet_name)
            except CommandError as e:
                self.stderr.write(str(e))
                continue

            try:
                created, updated = update_model_instances(model, df)
                total_created += created
                total_updated += updated
                self.stdout.write(
                    f"{sheet_name}: Created {created} new instances, Updated {updated} existing instances")
            except Exception as e:
                self.stderr.write(f"Error processing sheet {sheet_name}: {e}")

        self.stdout.write(f"================")
        self.stdout.write(f"Total: Created {total_created} new instances, Updated {total_updated} existing instances")


def read_excel_sheets(file_path):
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        data_frames = {sheet_name: pd.read_excel(excel_file, sheet_name=sheet_name) for sheet_name in sheet_names}
        return data_frames
    except Exception as e:
        raise CommandError(f"Error reading Excel file: {e}")


def get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        raise CommandError(f"Model '{model_name}' not found in app '{app_label}'")


def update_model_instances(model, data_frame):
    update_list = []
    create_list = []
    existing_ids = set(model.objects.filter(id__in=data_frame['id']).values_list('id', flat=True))

    for _, row in data_frame.iterrows():
        instance_id = row['id']
        row_data = {}

        for field in data_frame.columns:
            value = row[field]
            if isinstance(value, str) and value.startswith('{'):
                try:
                    row_data[field] = json.loads(value)
                except json.JSONDecodeError as e:
                    print(f"ID {row['id']} JSONDecodeError: {e}")
                    print(f"Problematic JSON: {row[field]}")
            elif field != 'id':
                row_data[field] = get_aware_datetime_value(value)

        if instance_id in existing_ids:
            instance = model.objects.get(id=instance_id)
            needs_update = False
            for field in data_frame.columns:
                if field != 'id' and getattr(instance, field) != row_data[field]:
                    setattr(instance, field, row_data[field])
                    needs_update = True
            if needs_update:
                update_list.append(instance)
        else:
            create_list.append(model(**row_data))

    with transaction.atomic():
        try:
            if create_list:
                model.objects.bulk_create(create_list)

            if update_list:
                fields_to_update = [field for field in data_frame.columns if field != 'id']
                model.objects.bulk_update(update_list, fields_to_update)
        except IntegrityError as e:
            print(f"Transaction failed: {e}")

    return len(create_list), len(update_list)


def get_aware_datetime_value(value):
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            # Localize naive Timestamp to Seoul time and then convert to UTC
            seoul_tz = pytz.timezone('Asia/Seoul')
            dt = seoul_tz.localize(value.to_pydatetime())  # Convert Timestamp to naive datetime
            return dt.astimezone(pytz.UTC)
        return value

    if isinstance(value, str):
        try:
            dt = parser.parse(value)
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                # Localize naive datetime to Seoul time and then convert to UTC
                seoul_tz = pytz.timezone('Asia/Seoul')
                dt = seoul_tz.localize(dt)
                return dt.astimezone(pytz.UTC)
            return dt
        except (ValueError, TypeError):
            return value

    return value
