import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import uuid
from urllib.parse import urljoin

st.title("🛠️ Product Scraper (Column-Row Structure)")
st.write("ดึงข้อมูลสินค้า (ชื่อ + รูปภาพ) จากเว็บไซต์ hsc-spareparts.com โดยใช้โครงสร้าง column/row")

if st.button("เริ่มดึงข้อมูล"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    all_products = []
    os.makedirs("images", exist_ok=True)

    progress = st.progress(0)
    total_pages = 39

    for page in range(1, total_pages + 1):
        url = f'https://hsc-spareparts.com/products/{page}.html'
        st.write(f"📄 กำลังดึงหน้า {page}...")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            st.warning(f"❌ หน้า {page} มีปัญหา: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        plist = soup.find('div', id='plist')
        if not plist:
            st.warning(f"⚠️ ไม่พบ div#plist ในหน้า {page}")
            continue
        product_container = plist.find_all('div')[2] if len(plist.find_all('div')) >= 3 else None
        if not product_container:
            st.warning(f"⚠️ ไม่พบ container หลักในหน้า {page}")
            continue

        for col in product_container.find_all('div', recursive=False):
            for row in col.find_all('div', recursive=False):
                a_tag = row.find('a')
                img_tag = a_tag.find('img') if a_tag else None
                name_tag = a_tag.find('p') if a_tag else None

                image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
                full_image_url = urljoin(url, image_url) if image_url else 'N/A'
                product_name = name_tag.text.strip() if name_tag else 'N/A'
                image_filename = f"{uuid.uuid4().hex}_{os.path.basename(full_image_url)}" if image_url else 'N/A'

                # ดาวน์โหลดรูปภาพ
                if image_url:
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

        progress.progress(page / total_pages)

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

