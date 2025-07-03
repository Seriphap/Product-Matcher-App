import streamlit as st
import pandas as pd
from pymongo import MongoClient
from urllib.parse import quote_plus
from rapidfuzz import fuzz
import xlsxwriter
from io import BytesIO
from PIL import Image


st.title("📦 Product Viewer (Image URL Version)")

username = "sssseriphap"
password = "ieTSQt7QOin0oxNQ"

# 🔄 Load data from MongoDB
if username and password and st.sidebar.button("🔄 Load Products from MongoDB Atlas"):
    try:
        encoded_password = quote_plus(password)
        mongo_uri = f"mongodb+srv://{username}:{encoded_password}@cluster0.hnvlg44.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(mongo_uri)
        db = client["productDB"]
        collection = db["products"]

        products = []
        for doc in collection.find():
            products.append({
                "name": doc.get("name", ""),
                "image_url": doc.get("image_url", "")
            })

        st.session_state.all_products = products
        st.success(f"✅ Loaded {len(products)} products from MongoDB Atlas")

    except Exception as e:
        st.sidebar.error(f"❌ Failed to load data: {e}")

# 🔍 Search and Display
if "all_products" in st.session_state and st.session_state.all_products:
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

    # 🖼️ Product Gallery
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

