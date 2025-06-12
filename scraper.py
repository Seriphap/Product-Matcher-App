import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin

st.title("🔍 ดึงข้อมูลสินค้าทั้งหมด (39 หน้า)")

base_url = "https://hsc-spareparts.com/products/"
headers = {'User-Agent': 'Mozilla/5.0'}

# XPath template สำหรับแต่ละสินค้าในหน้า
def get_product_xpaths(index):
    image_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[1]/a/img'
    name_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[2]/a'
    return image_xpath, name_xpath

if st.button("เริ่มดึงข้อมูลสินค้า"):
    all_products = []

    try:
        for page in range(1, 40):  # 1 ถึง 39
            url = f"{base_url}{page}.html"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tree = html.fromstring(response.content)

            for i in range(1, 21):  # พยายามดึง 20 รายการต่อหน้า
                image_xpath, name_xpath = get_product_xpaths(i)
                image_element = tree.xpath(image_xpath)
                name_element = tree.xpath(name_xpath)

                if not image_element or not name_element:
                    continue  # ข้ามถ้าไม่มีข้อมูล

                image_url = urljoin(url, image_element[0].get('src'))
                product_name = name_element[0].text_content().strip()

                all_products.append((product_name, image_url))

        st.success(f"✅ ดึงข้อมูลสำเร็จทั้งหมด {len(all_products)} รายการ")
        for name, img in all_products:
            st.image(img, caption=name, use_column_width=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")





