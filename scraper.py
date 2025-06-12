import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import uuid
from urllib.parse import urljoin

st.title("🛠️ Product Scraper")
st.write("กดปุ่มด้านล่างเพื่อดึงข้อมูลสินค้า (ชื่อ + รูปภาพ) จาก 39 หน้า")

if st.button("เริ่มดึงข้อมูล"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    all_products = []
    os.makedirs("images", exist_ok=True)

    progress = st.progress(0)

    for page in range(1, 40):
        url = f'https://hsc-spareparts.com/products/{page}.html'
        st.write(f"📄 กำลังดึงหน้า {page}...")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            st.warning(f"❌ หน้า {page} มีปัญหา: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        product_blocks = soup.select('div.col-md-3.col-sm-4.col-xs-6')

        if not product_blocks:
            st.info(f"ℹ️ หน้า {page} ไม่มีสินค้า")
            continue

        for block in product_blocks:
            img = block.find('img')
            name = block.find('p')

            image_url = img['src'] if img and 'src' in img.attrs else 'N/A'
            full_image_url = urljoin(url, image_url)
            product_name = name.text.strip() if name else 'N/A'
            image_filename = f"{uuid.uuid4().hex}_{os.path.basename(full_image_url)}"

            # ดาวน์โหลดรูปภาพ
            try:
                img_data = requests.get(full_image_url, headers=headers).content
                with open(os.path.join("images", image_filename), 'wb') as f:
                    f.write(img_data)
            except Exception as e:
                st.warning(f"⚠️ โหลดรูปไม่ได้: {full_image_url} - {e}")
                image_filename = 'N/A'

            all_products.append({
                'Product Name': product_name,
                'Image URL': full_image_url,
                'Image File': image_filename
            })

        progress.progress(page / 39)

    df = pd.DataFrame(all_products)
    st.success("✅ ดึงข้อมูลเสร็จแล้ว!")

    # แสดงตาราง
    st.dataframe(df)

    # แสดงตัวอย่างรูปภาพ
    st.subheader("🔍 ตัวอย่างสินค้า")
    for product in all_products[:5]:
        image_path = os.path.join("images", product['Image File'])
        if os.path.exists(image_path):
            st.image(image_path, caption=product['Product Name'])

    # ปุ่มดาวน์โหลด CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 ดาวน์โหลด CSV", csv, "products.csv", "text/csv")
