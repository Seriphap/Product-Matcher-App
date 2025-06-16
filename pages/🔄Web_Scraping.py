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

st.title("🔍 Scrape All Products and Export")

base_url = "https://hsc-spareparts.com/products/"
headers = {'User-Agent': 'Mozilla/5.0'}

def get_product_xpaths(index):
    image_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[1]/a/img'
    name_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[2]/a'
    return image_xpath, name_xpath

if "all_products" not in st.session_state:
    st.session_state.all_products = []

if st.sidebar.button("🚀 Start Scraping"):
    try:
        all_products = []
        for page in range(1, 40):
            url = f"{base_url}{page}.html"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tree = html.fromstring(response.content)

            for i in range(1, 21):
                image_xpath, name_xpath = get_product_xpaths(i)
                image_element = tree.xpath(image_xpath)
                name_element = tree.xpath(name_xpath)

                if not image_element or not name_element:
                    continue

                image_url = urljoin(url, image_element[0].get('src'))
                product_name = name_element[0].text_content().strip()

                all_products.append({"name": product_name, "image_url": image_url})

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
    for i in range(0, len(filtered_products), 5):
        cols = st.columns(5)
        for j in range(5):
            if i + j < len(filtered_products):
                with cols[j]:
                    st.image(filtered_products[i + j]["image_url"], caption=filtered_products[i + j]["name"], width=120)

    # 📥 ปุ่มใน Sidebar (ทำงานเมื่อกดเท่านั้น)
    if st.sidebar.button("📥 Download CSV"):
        csv = pd.DataFrame(filtered_products).to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("📥 Download CSV", data=csv, file_name="products.csv", mime="text/csv")

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
            label="📥 Download Excel",
            data=output,
            file_name="products_with_images.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.sidebar.markdown("### 🔐 MongoDB Login")
    mongo_user = st.sidebar.text_input("Username")
    mongo_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("☁️ Upload to MongoDB"):
        try:
            client = MongoClient(f"mongodb+srv://{mongo_user}:{mongo_pass}@cluster0.hnvlg44.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # Replace with your actual connection string
            db = client["product_db"]
            collection = db["products"]

            for product in filtered_products:
                try:
                    img_data = requests.get(product["image_url"]).content
                    encoded_image = base64.b64encode(img_data).decode('utf-8')

                    collection.insert_one({
                        "name": product["name"],
                        "image_url": product["image_url"],
                        "image_base64": encoded_image
                    })
                except Exception as e:
                    st.warning(f"⚠️ Failed to upload image for {product['name']}: {e}")

            st.sidebar.success("✅ Uploaded to MongoDB!")

        except Exception as e:
            st.sidebar.error(f"❌ MongoDB Error: {e}")

    




