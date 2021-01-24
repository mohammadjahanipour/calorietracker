import psycopg2

conn = psycopg2.connect(
    database='bank',
    user='django',
    sslmode='require',
    sslrootcert='certs/ca.crt',
    sslkey='certs/client.root.key',
    sslcert='certs/client.root.crt',
    port=26257,
    host='108.61.165.82'
)

print("Working")
