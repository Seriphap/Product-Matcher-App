import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin
import pandas as pd
from io import BytesIO
from PIL import Image
import xlsxwriter
import base64
from pymongo import MongoClient
from rapidfuzz import fuzz
import time
import random



st.title("🔍 Scrape All Products and Export")
base_url = "https://fslidingfeng.en.alibaba.com/productlist-"
headers = {'User-Agent': 'Mozilla/5.0'}

def get_product_xpaths(index):
    #image_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[1]/a/img'
    #name_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[2]/a'
    image_xpath = f'//*[@id="8919138061"]/div/div/div/div/div[2]/div/div[{index}]/a/div/img'
    name_xpath = f'//*[@id="8919138061"]/div/div/div/div/div[2]/div/div[{index}]/div[1]'

    return image_xpath, name_xpath

if "all_products" not in st.session_state:
    st.session_state.all_products = []
    
FromPage = st.sidebar.text_input("From Page", value=1)
ToPage = st.sidebar.text_input("To Page", value=FromPage)
if st.sidebar.button("🚀 Start Scraping"):
    try:
        all_products = []
        for page in range(int(FromPage), int(ToPage)+1):
            
            time.sleep(random.uniform(2.5, 4.5))
            url = f"{base_url}{page}.html?filter=null&sortType=modified-desc&isGallery=N"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            time.sleep(random.uniform(2.5, 4.5))
            tree = html.fromstring(response.content)

            for i in range(1, 17):
                image_xpath, name_xpath = get_product_xpaths(i)
                image_element = tree.xpath(image_xpath)
                name_element = tree.xpath(name_xpath) 
                if not image_element or not name_element:
                    continue

                image_url = urljoin(url, image_element[0].get('src'))
                product_name = name_element[0].text_content().strip()

                all_products.append({"name": product_name, "image_url": image_url})
            
            time.sleep(random.uniform(2.5, 4.5))
        st.session_state.all_products = all_products
        st.success(f"✅ Successfully scraped {len(all_products)} products")

    except Exception as e:
        st.error(f"An error occurred: {e}")

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

    # 🖼️ แสดงภาพทันที
    st.markdown("### 🖼️ Product Gallery")
    for i in range(0, len(filtered_products), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(filtered_products):
                with cols[j]:
                    st.image(filtered_products[i + j]["image_url"], caption=filtered_products[i + j]["name"], width=120)

    # 📥 ปุ่มใน Sidebar (ทำงานเมื่อกดเท่านั้น)
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

st.sidebar.markdown("### 🔐 MongoDB Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if username and password and st.sidebar.button("☁️ Upload to MongoDB Atlas"):
    try:
        from gridfs import GridFS
        from urllib.parse import quote_plus
        encoded_password = quote_plus(password)
        mongo_uri = f"mongodb+srv://{username}:{encoded_password}@cluster0.hnvlg44.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(mongo_uri)
        db = client["productDB"]
        collection = db["products"]
        fs = GridFS(db)

        # ล้างข้อมูลเก่า
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
  



    



