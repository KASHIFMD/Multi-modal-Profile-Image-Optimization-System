import csv
import mysql.connector

db_config_dev = {
    'host': "192.168.13.90",
    'database': "db_product",
    'port': 3306,
    "user": "web_app",
    "password": "!5@uGuST1($7FrEe1Ndi@"
}

csv_file_path = 'tbl_catalogue_details_filtered_500.csv'
table_name = 'imgrel_scores'

try:
    # Establish database connection
    mydb = mysql.connector.connect(**db_config_dev)
    mycursor = mydb.cursor()

    # Open and read the CSV file
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        updated_count = 0

        for row in csv_reader:
            product_id = row.get('product_id')
            text = row.get('text')

            if product_id and text:
                # Prepare the SQL query to update the table
                sql = f"""
                    UPDATE {table_name}
                    SET desc_llama32 = %s
                    WHERE product_id = %s
                """
                values = (text, product_id)

                # Execute the query
                mycursor.execute(sql, values)
                mydb.commit()
                updated_count += mycursor.rowcount

        print(f"Successfully updated {updated_count} rows in the table '{table_name}'.")

except mysql.connector.Error as err:
    print(f"Error connecting to MySQL or executing query: {err}")
except FileNotFoundError:
    print(f"Error: CSV file not found at '{csv_file_path}'")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Close the database connection
    if mydb and mydb.is_connected():
        mycursor.close()
        mydb.close()
        print("Database connection closed.")