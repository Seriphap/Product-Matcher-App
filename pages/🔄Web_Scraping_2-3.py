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

st.title("🔍 Scrape All Products and Export")

# -------------------- CATEGORY SETUP --------------------
category_options = {
    "All": "https://fslidingfeng.en.alibaba.com/productlist-",
    "Blow Molding Machines": "https://fslidingfeng.en.alibaba.com/productgrouplist-822252468-",
    "Filler Capper Machines": "https://fslidingfeng.en.alibaba.com/productgrouplist-821937823-",
    "Labeler Rinsing Machines": "https://fslidingfeng.en.alibaba.com/productgrouplist-822009771-",
    "Bottle Washer Machines": "https://fslidingfeng.en.alibaba.com/productgrouplist-822274262-",
    "Wrapping Machines": "https://fslidingfeng.en.alibaba.com/productgrouplist-822158603-",
    "Packer Unpacker": "https://fslidingfeng.en.alibaba.com/productgrouplist-822019527-",
    "PET Water Bottle Spare Parts": "https://fslidingfeng.en.alibaba.com/productgrouplist-822081922-",
    "HSC Spare Parts": "https://fslidingfeng.en.alibaba.com/productgrouplist-822746774-"
}
selected_category = st.sidebar.selectbox("📂 Select Product Category", list(category_options.keys()))
base_url = category_options[selected_category]
headers = {'User-Agent': 'Mozilla/5.0'}

if selected_category == "All":
    endpath = ".html"
elif selected_category == "Blow Molding Machines":
    endpath = "/Blow_Molding_Machines.html"
elif selected_category == "Filler Capper Machines":
    endpath = "/Filler_Capper_Machines.html"
elif selected_category == "Labeler Rinsing Machines":
    endpath = "/Labeler_Rinsing_Machines.html"
elif selected_category == "Bottle Washer Machines":
    endpath = "/Bottle_Washer_Machines.html"
elif selected_category == "Wrapping Machines":
    endpath = "/Wrapping_Machines.html"
elif selected_category == "Packer_Unpacker":
    endpath = "/Packer_Unpacker.html"
elif selected_category == "PET Water Bottle Spare Parts":
    endpath = "/PET_Water_Bottle_Spare_Parts.html"
elif selected_category == "HSC Spare Parts":
    endpath = "/HSC_spare_parts.html"
else:
    endpath = ".html"

if "all_products" not in st.session_state:
    st.session_state.all_products = []

# -------------------- SCRAPING FUNCTIONS --------------------
def extract_product_columns(tree, product_container_xpath):
    all_columns = []
    rows = tree.xpath(product_container_xpath + '/div/div')
    for row_index, row in enumerate(rows, start=1):
        columns = row.xpath('./div')
        for col_index, col in enumerate(columns, start=1):
            all_columns.append({
                "row": row_index,
                "column": col_index,
                "element": col
            })
    return all_columns


def extract_image_and_name(col_element, base_url):
    image_element = col_element.xpath(
        './/img[contains(@class, "react-dove-image")]/@src | .//img/@src'
    )
    name_element = col_element.xpath('.//div[1]//text()')

    if not image_element or not name_element:
        return None

    image_url = image_element[0]
    if image_url.startswith("//"):
        image_url = "https:" + image_url
    elif image_url.startswith("/"):
        image_url = urljoin(base_url, image_url)

    product_name = ''.join(name_element).strip()

    return {
        "name": product_name,
        "image_url": image_url
    }



# -------------------- SCRAPING UI --------------------
FromPage = st.sidebar.text_input("From Page",value=1)
ToPage = st.sidebar.text_input("To Page",value=FromPage)

if st.sidebar.button("🚀 Start Scraping"):
    try:
        all_products = []
        for page in range(int(FromPage), int(ToPage) + 1):
            url = f"{base_url}{page}{endpath}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            time.sleep(random.uniform(2.5, 4.5))

            tree = html.fromstring(response.content)
            product_container_xpath = '//*[@id="8919138061"]/div/div/div/div/div[2]'
            columns = extract_product_columns(tree, product_container_xpath)

            for col in columns:
                result = extract_image_and_name(col["element"], url)
                if result:
                    all_products.append(result)

        st.session_state.all_products = all_products
        st.success(f"✅ Successfully scraped {len(all_products)} products")

    except Exception as e:
        st.error(f"An error occurred: {e}")

# -------------------- DISPLAY & EXPORT --------------------
if st.session_state.all_products:
    st.markdown("### 🔎 Search Product Name")
    search_query = st.text_input("Enter keyword to filter products")
    fuzzy_option = st.checkbox("🔍 Enable Fuzzy Search (similar words)", value=False)

    if search_query:
        if fuzzy_option:
            filtered_products = [
                p for p in st.session_state.all_products
                if fuzz.partial_ratio(search_query.lower(), p["name"].lower()) > 70
            ]
        else:
            filtered_products = [
                p for p in st.session_state.all_products
                if search_query.lower() in p["name"].lower()
            ]
    else:
        filtered_products = st.session_state.all_products

    st.markdown("### 🖼️ Product Gallery")
    for i in range(0, len(filtered_products), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(filtered_products):
                with cols[j]:
                    st.image(filtered_products[i + j]["image_url"], caption=filtered_products[i + j]["name"], width=120)

    if st.sidebar.button("📥 Download CSV"):
        csv = pd.DataFrame(filtered_products).to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Save CSV File", data=csv, file_name="products.csv", mime="text/csv")

    if st.sidebar.button("📥 Download Excel"):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Products")

        worksheet.write("A1", "Product Name")
        worksheet.write("B1", "Image URL")
        worksheet.write("C1", "Image")

        row = 1
        for product in filtered_products:
            worksheet.write(row, 0, product["name"])
            worksheet.write(row, 1, product["image_url"])

            try:
                img_response = requests.get(product["image_url"], stream=True, timeout=10)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    img.thumbnail((100, 100))
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    worksheet.insert_image(row, 2, product["name"] + ".png", {
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

# -------------------- MONGODB UPLOAD --------------------
st.sidebar.markdown("### 🔐 MongoDB Login")
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

        collection.delete_many({})
        db.fs.files.delete_many({})
        db.fs.chunks.delete_many({})

        for product in st.session_state.all_products:
            img_response = requests.get(product["image_url"], stream=True, timeout=10)
            if img_response.status_code == 200:
                img_bytes = BytesIO(img_response.content)
                image_id = fs.put(img_bytes, filename=product["name"] + ".png")

                collection.insert_one({
                    "name": product["name"],
                    "image_url": product["image_url"],
                    "image_file_id": image_id
                })

        st.sidebar.success("✅ Uploaded products and images to MongoDB Atlas")

    except Exception as e:
        st.sidebar.error(f"❌ Upload failed: {e}")
