import mysql.connector

# Source database configuration
# Database connection details
# db_config_dev = {
#     'host':"192.168.13.90",
#     'database': "db_product",
#     'port': 3306,
#     "user": "web_app",
#     "password": "!5@uGuST1($7FrEe1Ndi@"
# }

db_config = {
    'host': "172.29.182.162",
    'database': "imgrel",
    'port': 3306,
    'user': "imgrel",
    'password': "passWord@00"
}


def replicate_table(source_config, target_config, table_name):
    try:
        # Connect to the source database
        source_conn = mysql.connector.connect(**source_config)
        source_cursor = source_conn.cursor(dictionary=True)

        # Fetch the table schema
        source_cursor.execute(f"SHOW CREATE TABLE {table_name}")
        schema_result = source_cursor.fetchone()
        create_table_query = schema_result['Create Table']

        # Connect to the target database
        target_conn = mysql.connector.connect(**target_config)
        target_cursor = target_conn.cursor()

        # Drop the table if it exists in the target database
        target_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Create the table in the target database
        target_cursor.execute(create_table_query)

        # Fetch all data from the source table
        source_cursor.execute(f"SELECT * FROM {table_name}")
        rows = source_cursor.fetchall()
        if rows:
            # Generate an insert query
            columns = ", ".join(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(rows[0]))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            # Insert data into the target table
            target_cursor.executemany(insert_query, [tuple(row.values()) for row in rows])
            target_conn.commit()

        print(f"Table '{table_name}' replicated successfully!")

    except mysql.connector.Error as e:
        print(f"Error: {e}")

    finally:
        # Close all connections
        if source_cursor:
            source_cursor.close()
        if source_conn:
            source_conn.close()
        if target_cursor:
            target_cursor.close()
        if target_conn:
            target_conn.close()

# Replicate the imgrel_scores table
replicate_table(db_config_dev, db_config, "imgrel_scores")
