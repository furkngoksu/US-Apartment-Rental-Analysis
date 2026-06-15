# 🇺🇸 US Apartment Rental Market Analysis

> [!NOTE]
> This project was developed as a term project for the **YZV311 - Data Mining** course at Istanbul Technical University (ITU) together with [Deniz Topal](https://github.com/Deniztpl).

An interactive data visualization and analysis dashboard built with **Python, Dash, and Plotly** to explore apartment rental listings across the United States.

---

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Dash-00897B?style=for-the-badge&logo=dash&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-3F51B5?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white" />
</p>

---

## 🚀 Key Features

This project consists of two main stages:

### 1. Data Cleaning & Exploratory Analysis (`data_cleaning.ipynb`)
- **Outlier Detection**: Employs Z-scores to identify and filter out pricing and square-footage anomalies.
- **Data Standardization**: Cleans up datatypes, parses timestamps, and structures geospatial location data.
- **Preprocessing Pipeline**: Exports a lightweight, optimized dataset (`data/rents_cleaned.csv`) for maximum dashboard load speed.

### 2. Interactive Dashboard Web Application (`app.py`)
- **Multi-parameter Filtering**: Filter live charts by State, City, Bedroom count, Price Range, and Square Footage.
- **Rich Data Visualizations**:
  - **USA Choropleth Map**: Displays average rental prices state-by-state.
  - **Temporal Trends Bar Chart**: Showcases average price movements over time with a integrated **3-month rolling average** line.
  - **Correlation Heatmap**: Highlights statistical correlations between price, bedroom/bathroom counts, and size.
  - **Interactive Scatter Plot**: Plots Price vs. Square Footage to analyze value distribution.
  - **Geospatial Map (Folium)**: Provides zoomable, cluster-mapped marker flags for regional listings.
  - **Top Locations Chart**: Ranks cities and states based on custom filters.

---

## 📂 Project Structure

```
├── assets/                  # Dashboard layout stylesheets and visual assets
├── data/
│   └── rents_cleaned.csv    # Cleaned, structured dataset (~14.7 MB)
├── app.py                   # Main Dash web application
├── data_cleaning.ipynb      # Jupyter notebook containing data engineering pipelines
├── requirements.txt         # List of Python dependencies
└── README.md                # Project documentation
```

---

## 🛠️ Installation & Setup

Follow these steps to run the dashboard locally:

### 1. Clone the Repository
```bash
git clone https://github.com/furkngoksu/US-Apartment-Rental-Analysis.git
cd US-Apartment-Rental-Analysis
```

### 2. Install Dependencies
Make sure you have Python 3.8+ installed. Run:
```bash
pip install -r requirements.txt
```

### 3. (Optional) Re-run Data Preprocessing
The pre-cleaned dataset is already included in `data/`. If you wish to run the preprocessing pipeline yourself, download the raw **Apartment for Rent Classified 100K** dataset from Kaggle, place the raw CSV as `data/apartments_for_rent_classified_100K.csv` and run:
```bash
jupyter notebook data_cleaning.ipynb
```

### 4. Run the Dashboard
Start the local Dash server:
```bash
python app.py
```

### 5. Open in Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:8070
```

---

## 📊 Dataset Reference
This project utilizes data based on the **Apartment for Rent Classified** dataset containing rental listings in the United States, providing real-world insights into rental market trends.
