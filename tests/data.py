KNOWN_ISBN = "9780132350884"  # Clean Code (ISBN-13)

# Shape of https://openlibrary.org/api/books?bibkeys=ISBN:...&format=json&jscmd=data
OPENLIBRARY_FIXTURE = {
    f"ISBN:{KNOWN_ISBN}": {
        "title": "Clean Code",
        "authors": [{"name": "Robert C. Martin"}],
        "publish_date": "August 2008",
        "subtitle": "A Handbook of Agile Software Craftsmanship",
        "cover": {"large": "https://covers.openlibrary.org/b/id/12345-L.jpg"},
        "number_of_pages": 431,
    }
}
