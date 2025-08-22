import sqlite3

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('URdb.sqlite')
cursor = conn.cursor()


# Create table with UserName, mail (unique), and Password columns
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        UserName TEXT NOT NULL,
        mail TEXT NOT NULL UNIQUE,
        Password TEXT NOT NULL
    )
''')

# Commit changes and close connection
conn.commit()
conn.close()
