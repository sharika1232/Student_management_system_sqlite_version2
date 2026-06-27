import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='root', database='student_management')
cur = conn.cursor()
cur.execute('SHOW COLUMNS FROM students')
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()
