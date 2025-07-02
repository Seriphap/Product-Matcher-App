import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin, quote_plus
import pandas as pd
from io import BytesIO
from PIL import Image
import xlsxwriter
from pymongo import MongoClient
from gridfs import GridFS
from rapidfuzz import fuzz
import time
import random


st.title("🔍 Scrape Alibaba Products and Export")

base_url = "https://fslidingfeng.en.alibaba.com/productgrouplist-822252468-"
headers = {'User-Agent': 'Mozilla/5.0'}

if "all_products" not in st.session_state:
    st.session_state.all_products = []

# Sidebar options
mode = st.sidebar.radio("📄 Select scraping mode", ["Select page range", "Auto scrape all pages"])

if mode == "Select page range":
    FromPage = st.sidebar.text_input("From Page", value="1")
    ToPage = st.sidebar.text_input("To Page", value=f"{FromPage}")


# Scraping logic
if st.sidebar.button("🚀 Start Scraping"):
    try:
        all_products = []

        if mode == "Select page range":
            for page in range(int(FromPage), int(ToPage) + 1):
                url = f"{base_url}{page}/Blow_Molding_Machines.html
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                time.sleep(random.uniform(2.5, 4.5))

                tree = html.fromstring(response.content)
                product_xpath = '//*[@id="8919138061"]/div/div/div/div/div[2]/div'
                product_elements = tree.xpath(product_xpath)

                for product in product_elements:
                    raw_html = html.tostring(product, encoding='unicode')
                    all_products.append({"raw_html": raw_html})

        else:  # Auto scrape all pages
            page = 1
            while True:
                url = f"{base_url}{page}/Blow_Molding_Machines.html
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                time.sleep(random.uniform(2.5, 4.5))

                tree = html.fromstring(response.content)
                product_xpath = '//*[@id="8919138061"]/div/div/div/div/div[2]/div/div'
                product_elements = tree.xpath(product_xpath)

                if not product_elements:
                    break

                for product in product_elements:
                    raw_html = html.tostring(product, encoding='unicode')
                    all_products.append({"raw_html": raw_html})

                page += 1
                time.sleep(random.uniform(2.5, 4.5))

        st.session_state.all_products = all_products
        st.success(f"✅ Scraped {len(all_products)} products")

    except Exception as e:
        st.error(f"❌ Error occurred: {e}")

# Function to extract name and image URL from raw HTML
def extract_name_and_image(raw_html):
    try:
        tree = html.fromstring(raw_html)
        name = ''.join(tree.xpath('.//div[1]//text()')).strip()
        image_url = tree.xpath('.//a/div/img/@src')
        image_url = image_url[0] if image_url else ""
        return name, image_url
    except:
        return "", ""

# Display and export
if st.session_state.all_products:
    st.markdown("### 🔎 Search Product Name")
    search_query = st.text_input("Enter keyword to filter products")
    fuzzy_option = st.checkbox("🔍 Enable Fuzzy Search (similar words)", value=False)

    if search_query:
        if fuzzy_option:
            filtered_products = [
                p for p in st.session_state.all_products
                if fuzz.partial_ratio(search_query.lower(), extract_name_and_image(p["raw_html"])[0].lower()) > 70
            ]
        else:
            filtered_products = [
                p for p in st.session_state.all_products
                if search_query.lower() in extract_name_and_image(p["raw_html"])[0].lower()
            ]
    else:
        filtered_products = st.session_state.all_products

    st.markdown("### 🖼️ Product Gallery")
    for i in range(0, len(filtered_products), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(filtered_products):
                with cols[j]:
                    st.markdown(filtered_products[i + j]["raw_html"], unsafe_allow_html=True)

    # Export to CSV
    if st.sidebar.button("📥 Download CSV"):
        export_data = []
        for item in filtered_products:
            name, image_url = extract_name_and_image(item["raw_html"])
            export_data.append({"name": name, "image_url": image_url})
        csv = pd.DataFrame(export_data).to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Save CSV File", data=csv, file_name="products.csv", mime="text/csv")

    # Export to Excel
    if st.sidebar.button("📥 Download Excel"):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Products")

        worksheet.write("A1", "Product Name")
        worksheet.write("B1", "Image URL")
        worksheet.write("C1", "Image")

        row = 1
        for item in filtered_products:
            name, image_url = extract_name_and_image(item["raw_html"])
            worksheet.write(row, 0, name)
            worksheet.write(row, 1, image_url)

            try:
                img_response = requests.get(image_url, stream=True, timeout=10)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    img.thumbnail((100, 100))
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    worksheet.insert_image(row, 2, name + ".png", {
                        'image_data': img_byte_arr,
                        'x_scale': 1,
                        'y_scale': 1
                    })
            except:
                pass
            row += 1

        workbook.close()
        output.seek(0)
        st.sidebar.download_button(
            label="Save Excel File",
            data=output,
            file_name="products_with_images.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# MongoDB Upload
st.sidebar.markdown("### ☁️ MongoDB Atlas Upload")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if username and password and st.sidebar.button("☁️ Upload to MongoDB Atlas"):
    try:
        encoded_password = quote_plus(password)
        mongo_uri = f"mongodb+srv://{username}:{encoded_password}@cluster0.hnvlg44.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(mongo_uri)
        db = client["productDB"]
        collection = db["products"]
        fs = GridFS(db)

        # Clear old data
        collection.delete_many({})
        db.fs.files.delete_many({})
        db.fs.chunks.delete_many({})

        for item in st.session_state.all_products:
            name, image_url = extract_name_and_image(item["raw_html"])
            img_response = requests.get(image_url, stream=True, timeout=10)
            if img_response.status_code == 200:
                img_bytes = BytesIO(img_response.content)
                image_id = fs.put(img_bytes, filename=name + ".png")

                collection.insert_one({
                    "name": name,
                    "image_url": image_url,
                    "image_file_id": image_id
                })

        st.sidebar.success("✅ Uploaded products and images to MongoDB Atlas")

    except Exception as e:
        st.sidebar.error(f"❌ Upload failed: {e}")


