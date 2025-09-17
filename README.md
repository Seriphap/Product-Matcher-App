# 📦 Product Matcher App

## 🏷️ Topic

The **Product Matcher App** is a Streamlit-based tool designed to help users **scrape, view, and compare product information (name, image, etc.) from competitor websites**. It enables efficient product matching by product name (with fuzzy search) and lays the groundwork for advanced matching using images or NLP-based similarity. The app is ideal for e-commerce analytics, price comparison, and competitive analysis.

---

## 🚀 Streamlit App

- **Live Demo:**  
  [Streamlit Cloud App](https://appuct-matcher-app-6sh3ctcpq6zw3ygzyzjphw.streamlit.app/)
- Features a sidebar for workflow navigation, scraping controls, MongoDB authentication, and file export.
- Main pages:
  - **Web Scraping**: Scrape product details (name, image) from specified websites and categories.
  - **Product Viewer**: Interactively browse and search products with image previews and fuzzy search.
  - **MongoDB Integration**: Securely upload/download products to/from MongoDB Atlas for persistent storage.

---

## 🗂️ App Structure

```
Product-Matcher-App/
│
├── App_structure.txt         # English/Thai outline of modules and workflow
├── README.md                 # Project documentation
├── 🤔Product_Preview.py      # Main product viewer UI (image search, MongoDB load)
└── pages/
    ├── 🔄Web_Scraping_1.py   # Web scraping from hsc-spareparts.com
    ├── 🔄Web_Scraping_2-1.py # Web scraping (Alibaba) with export & MongoDB
    ├── 🔄Web_Scraping_2-2.py # Alternative scraping workflow (Alibaba)
    └── 🔄Web_Scraping_2-3.py # All-in-one scraping, matching, export, MongoDB
```

**Core Modules:**
- **Web Scraping**: Extract product name, images from multiple e-commerce sources.
- **Database**: Store/export products in MongoDB, SQLite, or DataFrame.
- **Input/Matching**: User can search by name (fuzzy/NLP) or in future upload an image for visual matching.
- **UI**: Streamlit interface for scraping, searching, exporting, and data management.

---

## 🐍 Python Libraries Used

- `streamlit` — UI and interactivity
- `requests`, `lxml` — Web scraping
- `pandas`, `xlsxwriter` — Data manipulation and export
- `PIL` (Pillow) — Image processing
- `rapidfuzz` — Fast fuzzy string matching for product name similarity
- `pymongo`, `gridfs` — MongoDB Atlas storage (image and data persistence)
- `io`, `base64` — File and image handling
- `random`, `time` — Scraping delay/randomization for anti-bot protection

---

## 📊 Visualization & UI Features

- **Product Gallery**: Grid display of scraped products (names and images).
- **Fuzzy Search**: Search box to find products with similar names (partial match using RapidFuzz).
- **File Export**: Export filtered results as CSV or Excel (with image URLs).
- **MongoDB Integration**: Upload/download product data and images to/from MongoDB Atlas securely.
- **Image Previews**: Show product images directly in the UI.

---

## 🧠 Model & Matching Logic

- **Text-based Matching**: Fuzzy string matching on product names using RapidFuzz.
- **Planned/Commented Future**:
  - NLP embeddings or CLIP/image embeddings for advanced semantic and visual similarity search.
- **Scraping Logic**: Robust scraping from paginated competitor product lists (configurable by category or page range).

---

## 🔍 Insights from Using This App

- **Competitive Product Analysis**: Understand the breadth and type of products offered by competitors.
- **Fast Product Matching**: Quickly find similar products by name (even if spelling or word order varies).
- **Data Pipeline**: Export or persist product data for further analysis, price tracking, or integration into BI tools.
- **Workflow Automation**: Streamline the process of product catalog comparison and enrichment.

---

## 💡 Typical Insights

- *"Which competitor products are most similar to ours by name or appearance?"*
- *"How many unique products are scraped this week compared to last?"*
- *"Are new products appearing in the competitor’s catalog?"*
- *"Which scraped products lack good images or have duplicate names?"*

---

## 📥 How to Use

1. **Start the app** with `streamlit run 🤔Product_Preview.py` or any `pages/🔄Web_Scraping_*.py`.
2. **Select a scraping workflow** and configure page/category as needed.
3. **Scrape products** — product names and images will be loaded and previewed.
4. **Search/filter** in the UI for similar names (optionally enable fuzzy search).
5. **Export** results or **upload to MongoDB** for persistence and advanced analytics.

---

## 📝 Note

- The app is extensible for NLP/image-based matching in the future.
- Ensure you have correct MongoDB Atlas credentials for data upload.
- The scraping targets and logic may need occasional updates as competitor websites change structure.
