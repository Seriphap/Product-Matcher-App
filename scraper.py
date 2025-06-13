import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin
import pandas as pd

st.title("🔍 Scrape All Products (39 Pages)")

base_url = "https://hsc-spareparts.com/products/"
headers = {'User-Agent': 'Mozilla/5.0'}

# XPath template for each product on the page
def get_product_xpaths(index):
    image_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[1]/a/img'
    name_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[2]/a'
    return image_xpath, name_xpath

if st.button("Start Scraping Products"):
    all_products = []

    try:
        for page in range(1, 40):  # Pages 1 to 39
            url = f"{base_url}{page}.html"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tree = html.fromstring(response.content)

            for i in range(1, 21):  # Try to extract 20 products per page
                image_xpath, name_xpath = get_product_xpaths(i)
                image_element = tree.xpath(image_xpath)
                name_element = tree.xpath(name_xpath)

                if not image_element or not name_element:
                    continue

                image_url = urljoin(url, image_element[0].get('src'))
                product_name = name_element[0].text_content().strip()

                all_products.append({"name": product_name, "image_url": image_url})

        st.success(f"✅ Successfully scraped {len(all_products)} products")

        # Display in 5 columns
        for i in range(0, len(all_products), 5):
            cols = st.columns(5)
            for j in range(5):
                if i + j < len(all_products):
                    with cols[j]:
                        st.image(all_products[i + j]["image_url"], caption=all_products[i + j]["name"], width=120)

        # Create DataFrame and download button
        df = pd.DataFrame(all_products)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Product Data as CSV",
            data=csv,
            file_name='products_dataset.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")







