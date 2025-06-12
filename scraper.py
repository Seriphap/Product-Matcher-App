import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin

st.title("🔍 ดึงข้อมูลสินค้า (XPath)")

url = "https://hsc-spareparts.com/products/1.html"
headers = {'User-Agent': 'Mozilla/5.0'}

image_xpath = '//*[@id="plist"]/div[3]/div[1]/div[1]/a/img'
name_xpath = '//*[@id="plist"]/div[3]/div[1]/div[2]/a'

if st.button("เริ่มดึงข้อมูลสินค้า"):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tree = html.fromstring(response.content)

        image_element = tree.xpath(image_xpath)
        name_element = tree.xpath(name_xpath)

        image_url = urljoin(url, image_element[0].get('src')) if image_element else 'N/A'
        product_name = name_element[0].text_content().strip() if name_element else 'N/A'

        st.success("✅ ดึงข้อมูลสำเร็จแล้ว")
        st.write(f"**ชื่อสินค้า:** {product_name}")
        st.image(image_url, caption=product_name)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")




