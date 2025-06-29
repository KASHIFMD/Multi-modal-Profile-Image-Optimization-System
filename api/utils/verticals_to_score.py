from app.config import db_config_dev, db_config_prod_slave

from flask import Flask, jsonify
import mysql.connector
import json, sys

connection_dev = mysql.connector.connect(**db_config_dev)
connection_prod = mysql.connector.connect(**db_config_prod_slave)
# if connection_dev.is_connected():
#     # cursor = connection_dev.cursor()
#     cursor = connection_dev.cursor(dictionary=True)

# Take docid from imgrel_verticals table based on given vertical
def get_docids_verticals(vertical, limit = 1000, offset=0):
    # offset = 1000*offset
    print("OFFSET: ", offset)

    # limit = 1000
    if(vertical):
        select_query = f"""
            SELECT docid, vertical, categories
            FROM imgrel_verticals
            WHERE vertical = %s LIMIT {limit} OFFSET {offset};
        """
    else:
        select_query = f"""
            SELECT docid, vertical, categories
            FROM imgrel_verticals LIMIT {limit} OFFSET {offset};
        """

    try:
        # Execute the query
        cursor = connection_dev.cursor(dictionary=True)
        if(vertical):
            cursor.execute(select_query, (vertical,))
        else:
            cursor.execute(select_query)
        rows = cursor.fetchall()

        print("len(result): ", len(rows))
        # print("rows: ", rows)
        return rows, None  # Return rows and no error
    except Exception as e:
        print(f"Error executing query: {e}")
        return None, str(e)  # Return None and the error message



# Fetch all pids of given list of docids
def get_pids_cat_details(docids):
    # select_query = """
    #     SELECT product_id, product_url, docid
    #     FROM tbl_catalogue_details
    #     WHERE docid IN (%s);
    # """
    select_query_template = """
        SELECT product_id, product_url, docid, contractid
        FROM tbl_catalogue_details
        WHERE docid IN ({placeholders});
    """
    pids = []
    try:
        # Convert the list of docids into a tuple of strings for the SQL query
        docid_values = tuple(docid['docid'] for docid in docids)
        # print("docid_values: ", docid_values)
        print("len(docid_values): ", len(docid_values))

        # Dynamically generate placeholders based on the number of docids
        placeholders = ','.join(['%s'] * len(docid_values))
        select_query = select_query_template.format(placeholders=placeholders)
        # print("select_query: ", select_query)

        # Execute the query with parameterized inputs
        cursor = connection_prod.cursor(dictionary=True)
        cursor.execute(select_query, docid_values)
        rows = cursor.fetchall()

        print("Query executed successfully!")
        print("len(rows): ", len(rows))

        for row in rows:
            # print(row['product_id'], row["product_url"], row['docid'])
            pids.append({
                "product_id": row["product_id"], 
                "product_url": row["product_url"], 
                "docid": row["docid"],
                "contractid": row["contractid"]
            })

        return pids, None  # Return rows and no error
    except Exception as e:
        print(f"Error executing query: {e}")
        return None, str(e)  # Return None and the error message


if __name__ == "__main__":
    # Fetch the next batch of docids
    # batch_size = 10
    vertical = "bridal"
    ind  = 0
    while(ind<18):
        offset = 1000*ind
        limit = 1000
        rows, error = get_docids_verticals(vertical, limit, offset)
        if error:
            print(f"Error: vertical = {vertical}")
            print(f"Error fetching docids: {error}")

        pids, err = get_pids_cat_details(rows)
        if(err):
            print(f"Error (get_pids_cat_details): {err}")
            sys.exit(1)  # Exit with status code 1 (indicating an error)

        # Prepare the INSERT query
        insert_query = """
            INSERT INTO imgrel_scores (product_id, updated_datetime, contractid)
            VALUES (%s, CURRENT_TIMESTAMP, %s)
            ON DUPLICATE KEY UPDATE
                updated_datetime = CURRENT_TIMESTAMP,
                contractid = VALUES(contractid)
        """

                # product_url = VALUES(product_url),
                # docid = VALUES(docid),
        try:
            # Open a cursor and execute the query in batch
            with connection_dev.cursor() as cursor:
                # Prepare data for batch insert
                data = [
                    (pid['product_id'], pid['contractid'])
                    for pid in pids
                ]

                # Execute batch insert
                cursor.executemany(insert_query, data)

                # Commit the transaction
                connection_dev.commit()

            print("Data inserted/updated successfully!")

        except Exception as e:
            # Rollback in case of an error
            connection_dev.rollback()
            print(f"Error inserting data into imgrel_scores: {e}")
            sys.exit(1)  # Exit with status code 1
        
        print("### ind: ", ind)
        ind+=1