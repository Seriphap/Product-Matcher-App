import streamlit as st
import requests
from lxml import html
from urllib.parse import urljoin
import pandas as pd
from io import BytesIO
from PIL import Image
import xlsxwriter

st.title("🔍 Scrape All Products and Export")

base_url = "https://hsc-spareparts.com/products/"
headers = {'User-Agent': 'Mozilla/5.0'}

def get_product_xpaths(index):
    image_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[1]/a/img'
    name_xpath = f'//*[@id="plist"]/div[3]/div[{index}]/div[2]/a'
    return image_xpath, name_xpath

if st.button("Start Scraping"):
    all_products = []

    try:
        for page in range(1, 40):  # Pages 1 to 39
            url = f"{base_url}{page}.html"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            tree = html.fromstring(response.content)

            for i in range(1, 21):  # Up to 20 products per page
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

        # CSV download
        df = pd.DataFrame(all_products)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV [Product Name, Image URL]",
            data=csv,
            file_name='products_dataset.csv',
            mime='text/csv'
        )

        # Excel with images
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Products")

        worksheet.write("A1", "Product Name")
        worksheet.write("B1", "Image URL")
        worksheet.write("C1", "Image")

        row = 1
        for product in all_products:
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
        
        st.download_button(
            label="📥 Download Excel [Product Name, Image URL and Image Preview]",
            data=output,
            file_name="products_with_images.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"An error occurred: {e}")








