import sqlite3

# Connect to database
conn = sqlite3.connect('backend/facebook_dashboard.db')
cursor = conn.cursor()

# Get table schema
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()

print('Users table schema:')
print('ID | Name | Type | NotNull | Default | PK')
print('-' * 50)
for col in columns:
    print(f'{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}')

# Check if GA4 columns exist
column_names = [col[1] for col in columns]
ga4_columns = ['ga4_access_token', 'ga4_refresh_token', 'ga4_expires_at']

print('\nGA4 columns check:')
for col in ga4_columns:
    exists = col in column_names
    print(f'{col}: {"✅ EXISTS" if exists else "❌ MISSING"}')

conn.close()