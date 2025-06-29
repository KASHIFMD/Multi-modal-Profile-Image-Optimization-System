import streamlit as st
import mysql.connector
from PIL import Image
import requests
from io import BytesIO

# Database Configuration
db_config_dev = {
    'host': "192.168.13.90",
    'database': "db_product",
    'port': 3306,
    "user": "web_app",
    "password": "!5@uGuST1($7FrEe1Ndi@"
}
# Function to fetch data from MySQL
def fetch_data_from_db():
    try:
        mydb = mysql.connector.connect(**db_config_dev)
        mycursor = mydb.cursor()
        query = """
            SELECT product_id, docid, product_url, desc_api, desc_llama32
            FROM imgrel_scores
            WHERE desc_api IS NOT NULL AND desc_llama32 IS NOT NULL LIMIT 100;
        """
        mycursor.execute(query)
        data = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        return data
    except mysql.connector.Error as err:
        st.error(f"Error connecting to MySQL or executing query: {err}")
        return []

# Function to display image from URL
def display_image_from_url(url):
    try:
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        st.image(image, use_container_width=True)
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading image from {url}: {e}")
        return False
    except Exception as e:
        st.error(f"Error opening image: {e}")
        return False

def main():
    st.title("Image Description Comparison")
    st.subheader("Comparing descriptions from API and LLaMA")

    data = fetch_data_from_db()

    if data:
        for row in data:
            product_id, docid, product_url, desc_api, desc_llama32 = row

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader(f"Product ID: {product_id}")
                st.write(f"Doc ID: {docid}")
                if product_url:
                    if display_image_from_url(product_url):
                        pass
                else:
                    st.warning("Product URL not available.")

            with col2:
                st.subheader("Description (API)")
                st.write(desc_api)

            with col3:
                st.subheader("Description (LLaMA)")
                st.write(desc_llama32)
            st.divider()
    else:
        st.info("No data found where both API and LLaMA descriptions are available.")

if __name__ == "__main__":
    main()