import csv
import random
from faker import Faker

fake = Faker()
rows = 100_000  # number of records in file
filename = "example_large.csv"

with open(filename, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "author", "isbn", "publication_year"])

    for _ in range(rows):
        title = fake.sentence(nb_words=4)
        author = fake.name()
        isbn = "".join([str(random.randint(0, 9)) for _ in range(13)])
        year = random.randint(1900, 2024)
        writer.writerow([title, author, isbn, year])

print(f"{rows} rows written to {filename}")
