import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        file_path = options['file_path']
        ingredients = []
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')
            for entry in reader:
                measure_unit = Ingredient(measure_unit=entry[1])[0]
                ingredient = Ingredient(name=entry[0], measure_unit=measure_unit)
                ingredients.append(ingredient)
                self.stdout.write(f"Entry {entry[0]}, {entry[1]} was parsed")

                if len(ingredients) > 999:
                    Ingredient.objects.bulk_create(ingredients)
                    self.stdout.write(f"{len(ingredients)} entries were bulk created")
                    ingredients = []

        if ingredients:
            Ingredient.objects.bulk_create(ingredients)
            self.stdout.write(f"{len(ingredients)} entries were bulk created")

        self.stdout.write("Process finished")
