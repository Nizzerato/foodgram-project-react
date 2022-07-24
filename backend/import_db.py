"""The script for database filling by ingredients."""

import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Working with the database."""

    help = 'Uploading Ingredients data-set'

    def handle(self, *args, **options):
        """Handle the file which has data."""
        with open(
                'data/ingredients.json', encoding='utf-8'
        ) as json_file:
            ingredients = json.load(json_file)
            for ingredient in ingredients:
                name = ingredient['name']
                measure_unit = ingredient['measurement_unit']
                Ingredient.objects.create(
                    name=name,
                    measure_unit=measure_unit
                )


app = Command()
app.handle()
print("Ингредиенты загружены в базу!")
