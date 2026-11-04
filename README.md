# Global Urban Intelligence
### Data Engineering, Environmental Analytics & Urban Intelligence

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Data Engineering](https://img.shields.io/badge/Domain-Data%20Engineering-orange)
![Analytics](https://img.shields.io/badge/Focus-Data%20Analytics-green)
![Status](https://img.shields.io/badge/Project-Development-blueviolet)

**Global Urban Intelligence** is an end-to-end data engineering and analytics project designed to collect, process, integrate, and analyze urban environmental data from multiple open data sources.

The project combines air quality, meteorological, and demographic indicators to explore environmental conditions across selected European and Mediterranean cities.

It demonstrates a reproducible workflow covering data ingestion, data quality, transformation, integration, exploratory analysis, statistical methods, and data visualization.

---

## 1. Project Overview

Urban environments face interconnected challenges involving air pollution, changing weather conditions, and population growth.

However, environmental datasets are often distributed across different platforms, APIs, geographical scales, and data formats.

This project addresses these challenges by building a modular pipeline that transforms heterogeneous datasets into a unified analytical dataset.

### Target Cities

| City | Country |
|---|---|
| Casablanca | Morocco |
| Rabat | Morocco |
| Paris | France |
| Madrid | Spain |
| Lisbon | Portugal |

### Main Objectives

- Collect environmental data from open APIs.
- Build a reproducible data ingestion pipeline.
- Assess data quality and identify missing or inconsistent values.
- Clean and standardize heterogeneous datasets.
- Engineer meaningful temporal and environmental features.
- Integrate datasets from multiple sources.
- Perform exploratory and statistical analysis.
- Generate informative visualizations.
- Translate analytical observations into evidence-based insights.

---

## 2. Research Questions

1. How do PM2.5 and PM10 concentrations differ across the selected cities?
2. How are pollution levels distributed across different locations and periods?
3. What relationships exist between air quality and meteorological variables?
4. How do temperature, humidity, wind speed, and precipitation relate to particulate concentrations?
5. Are there observable seasonal patterns in environmental conditions?
6. How do missing values, measurement anomalies, and inconsistent data formats affect analytical reliability?
7. What limitations arise when combining city-level environmental data with country-level demographic indicators?
8. What insights can be derived to support environmental monitoring and urban planning?

**Methodological principle:** Correlation does not imply causation. Statistical relationships are interpreted carefully and do not independently establish the causes of pollution.

---

## 3. Data Sources

| Domain | Source | Main Variables |
|---|---|---|
| Air Quality | [OpenAQ](https://openaq.org/) | PM2.5, PM10, monitoring stations, coordinates, timestamps |
| Meteorology | [Open-Meteo](https://open-meteo.com/) | Temperature, humidity, wind speed, wind direction, precipitation |
| Demographics | [World Bank Open Data](https://data.worldbank.org/) | Total population, population growth, urban population indicators |

### Data Provenance

Each dataset should preserve its source information:

- `OpenAQ`: air quality observations.
- `Open-Meteo`: meteorological observations.
- `World Bank`: demographic indicators.
- `SYNTHETIC_DEMO`: generated demonstration data.

When external APIs are unavailable, synthetic data can be used for pipeline testing and reproducibility. Synthetic observations must never be presented as real environmental measurements.

**Important:** Country-level population indicators must not be interpreted as city-level population statistics.

---

## 4. Data Engineering Architecture

```mermaid
flowchart TD
    A[OpenAQ API] --> D[Data Collection]
    B[Open-Meteo API] --> D
    C[World Bank API] --> D

    D --> E[Raw Data Storage]
    E --> F[Data Profiling]
    F --> G[Data Validation]
    G --> H[Data Cleaning]

    H --> I[Interim Data Storage]
    I --> J[Feature Engineering]
    J --> K[Data Integration]

    K --> L[Processed Analytical Dataset]

    L --> M[Exploratory Data Analysis]
    L --> N[Statistical Analysis]
    L --> O[Data Visualization]

    M --> P[Analytical Insights]
    N --> P
    O --> P

    P --> Q[Reports and Recommendations]
```

### Pipeline Stages

| Stage | Description |
|---|---|
| Data Collection | Extract data from APIs and generate demonstration datasets when required. |
| Raw Storage | Preserve original extracts and metadata. |
| Data Profiling | Examine schemas, data types, missing values, duplicates, and distributions. |
| Data Validation | Check expected columns, ranges, formats, and consistency. |
| Data Cleaning | Handle missing values, duplicates, inconsistent units, and invalid observations. |
| Transformation | Create temporal, seasonal, and environmental features. |
| Integration | Combine datasets using documented geographical and temporal keys. |
| Analytical Processing | Prepare the final dataset for statistical analysis and visualization. |
| Reporting | Generate charts, reports, and analytical observations. |

---

## 5. Repository Structure

```text
04-global-urban-intelligence/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── PROGRESS.md
├── run_pipeline.py
│
├── config/
│   ├── cities.json
│   └── settings.yaml
│
├── data/
│   ├── DATA_DICTIONARY.md
│   ├── raw/
│   ├── interim/
│   └── processed/
│
├── notebooks/
│   ├── 01-business-understanding.ipynb
│   ├── 02-data-collection.ipynb
│   ├── 03-data-profiling.ipynb
│   ├── 04-data-cleaning.ipynb
│   ├── 05-data-transformation.ipynb
│   ├── 06-data-integration.ipynb
│   ├── 07-exploratory-analysis.ipynb
│   ├── 08-statistical-analysis.ipynb
│   ├── 09-data-visualization.ipynb
│   └── 10-insights-and-recommendations.ipynb
│
├── src/
│   ├── data_collection/
│   ├── preprocessing/
│   ├── analysis/
│   └── visualization/
│
├── outputs/
│   ├── figures/
│   ├── reports/
│   └── datasets/
│
└── tests/
    ├── test_collection.py
    ├── test_cleaning.py
    ├── test_transformation.py
    └── test_pipeline.py
```

---

## 6. Visualization Gallery

The following gallery embeds the generated figures directly from `outputs/figures/`.

**Note:** Images appear on GitHub when the corresponding PNG files exist in the repository and have been pushed to GitHub.

### 6.1 Distribution Analysis

| Histogram | Histogram with KDE |
|---|---|
| ![PM2.5 Histogram](outputs/figures/01_pm25_histogram.png) | ![PM2.5 Histogram KDE](outputs/figures/02_pm25_histogram_kde.png) |
| **01 — PM2.5 Distribution** | **02 — PM2.5 Density Distribution** |

| Box Plot | Violin Plot |
|---|---|
| ![PM2.5 Boxplot](outputs/figures/03_pm25_boxplot.png) | ![PM2.5 Violin](outputs/figures/04_pm25_violin.png) |
| **03 — Statistical Dispersion** | **04 — Distribution Shape** |

| Density Curve | ECDF |
|---|---|
| ![PM2.5 Density](outputs/figures/05_pm25_density.png) | ![PM2.5 ECDF](outputs/figures/06_pm25_ecdf.png) |
| **05 — Density Comparison** | **06 — Empirical Cumulative Distribution** |

### 6.2 Comparative Analysis

| Mean PM2.5 | Grouped PM Comparison |
|---|---|
| ![Mean PM2.5 Bar Chart](outputs/figures/07_mean_pm25_barchart.png) | ![PM Grouped Bar](outputs/figures/08_pm_grouped_bar.png) |
| **07 — Average PM2.5 by City** | **08 — PM2.5 vs PM10** |

| Temperature Comparison | Cleveland Dot Plot |
|---|---|
| ![Temperature Horizontal Bar](outputs/figures/09_temperature_horizontal_bar.png) | ![PM2.5 Dot Plot](outputs/figures/10_pm25_dot_plot.png) |
| **09 — Temperature by City** | **10 — City Ranking** |

| Monthly Heatmap | Small Multiples |
|---|---|
| ![Monthly City Heatmap](outputs/figures/11_monthly_city_heatmap.png) | ![Small Multiples](outputs/figures/12_small_multiples.png) |
| **11 — City × Month Comparison** | **12 — Distribution by City** |

### 6.3 Relationships and Correlations

| Scatter Plot | Regression Analysis |
|---|---|
| ![Temperature PM2.5 Scatter](outputs/figures/13_scatter_temp_pm25.png) | ![Temperature PM2.5 Regression](outputs/figures/14_regression_temp_pm25.png) |
| **13 — Temperature vs PM2.5** | **14 — Regression Relationship** |

| Pair Plot | Bubble Chart |
|---|---|
| ![Variables Pairplot](outputs/figures/15_variables_pairplot.png) | ![Bubble Chart](outputs/figures/16_bubble_chart.png) |
| **15 — Pairwise Variable Relationships** | **16 — Multivariable Comparison** |

| Correlation Heatmap |
|---|
| ![Correlation Heatmap](outputs/figures/17_correlation_heatmap.png) |
| **17 — Correlation Matrix** |

### 6.4 Temporal Analysis

| Time Series | Multiple Time Series |
|---|---|
| ![PM2.5 Time Series](outputs/figures/18_timeseries_pm25.png) | ![Multiple Time Series](outputs/figures/19_multi_timeseries.png) |
| **18 — Daily PM2.5 Evolution** | **19 — Environmental Indicators Over Time** |

| Rolling Average | Seasonal Comparison |
|---|---|
| ![Rolling Average](outputs/figures/20_rolling_average.png) | ![Seasonal Comparison](outputs/figures/21_seasonal_comparison.png) |
| **20 — Moving Average Analysis** | **21 — Seasonal Pollution Patterns** |

| Calendar Heatmap |
|---|
| ![Calendar Heatmap](outputs/figures/22_calendar_heatmap.png) |
| **22 — Calendar-Based Pollution Patterns** |

### 6.5 Geographic and Advanced Analytics

| City Location Map | Geographic Comparison |
|---|---|
| ![City Map](outputs/figures/23_city_map.png) | ![Geographic Comparison](outputs/figures/25_geographic_comparison.png) |
| **23 — City Locations** | **25 — Geographic Comparison** |

| PCA Visualization | Cluster Regimes |
|---|---|
| ![PCA Visualization](outputs/figures/26_pca_visualization.png) | ![Cluster Visualization](outputs/figures/27_cluster_visualization.png) |
| **26 — Principal Component Analysis** | **27 — Environmental Clustering** |

| Urban Stress Index | Distribution Comparison |
|---|---|
| ![Radar Profile](outputs/figures/28_radar_profile.png) | ![Distribution Comparison](outputs/figures/29_distribution_comparison.png) |
| **28 — Multidimensional Urban Profile** | **29 — Distribution Comparison** |

### 6.6 Executive Dashboard

![Executive Dashboard](outputs/figures/30_dashboard_overview.png)

**30 — Executive Dashboard Overview**

The dashboard is designed to consolidate key environmental indicators and comparative views into one analytical interface.

### 6.7 Interactive Geographic Visualization

[**Open Interactive City Map (HTML)**](outputs/figures/24_city_map_interactive.html)

[**Open Interactive Executive Dashboard (HTML)**](outputs/figures/30_dashboard_interactive.html)

These HTML files can be opened locally in a browser. GitHub does not generally render interactive HTML files directly inside the README.

---

## 7. Exploratory Data Analysis

The exploratory analysis focuses on understanding the characteristics and relationships of the collected variables.

### Univariate Analysis

- Mean, median, standard deviation, and quantiles.
- Distribution shapes and skewness.
- Missing-value analysis.
- Outlier identification.
- Frequency distributions.

### Bivariate Analysis

- Pollution versus temperature.
- Pollution versus wind speed.
- Pollution versus humidity.
- Relationships between PM2.5 and PM10.
- Comparative analysis across cities.

### Temporal Analysis

- Daily and monthly patterns.
- Seasonal variations.
- Rolling averages.
- Long-term environmental trends.
- Periods with unusually high pollutant concentrations.

---

## 8. Statistical Analysis

| Method | Purpose |
|---|---|
| Descriptive Statistics | Summarize distributions and variability. |
| Pearson Correlation | Measure linear relationships. |
| Spearman Correlation | Evaluate monotonic relationships. |
| Hypothesis Testing | Examine differences between groups. |
| ANOVA | Compare means under appropriate assumptions. |
| Kruskal-Wallis | Compare distributions without requiring normality. |
| Confidence Intervals | Quantify uncertainty around estimates. |
| Linear Regression | Explore relationships between variables. |
| PCA | Reduce dimensionality when justified. |
| K-Means | Explore groups of similar environmental observations. |

Statistical assumptions, sample sizes, missingness, and potential biases must be evaluated before interpreting results.

---

## 9. Analytical Insights and Recommendations

The final analytical stage aims to transform statistical observations into understandable insights.

Examples of questions addressed include:

- Which cities show higher observed particulate concentrations?
- During which periods are pollution levels elevated?
- Which meteorological variables are associated with changes in pollutant concentrations?
- How reliable are comparisons given differences in monitoring coverage?
- What additional data would improve the analysis?

Potential recommendation areas include:

1. Improving air quality monitoring coverage.
2. Identifying periods of elevated pollution.
3. Supporting environmental monitoring programs.
4. Improving access to reliable urban environmental data.
5. Supporting evidence-based urban planning.

Recommendations must be based on actual findings and acknowledge the limitations of the available datasets.

---

## 10. Installation and Setup

### Prerequisites

- Python 3.11 or higher.
- Git.
- Visual Studio Code or another Python-compatible IDE.
- Internet connection for live API collection.

### Clone the Repository

```bash
git clone https://github.com/marwaneproo/global-urban-intelligence.git

cd global-urban-intelligence
```

### Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

---

## 11. Running the Project

If supported by the implemented pipeline:

### Offline Demonstration Mode

```bash
python run_pipeline.py --demo
```

### Live Data Collection Mode

```bash
python run_pipeline.py --live
```

### Run Tests

```bash
pytest -q
```

---

## 12. Jupyter Notebook Guide

| Notebook | Subject | Main Focus |
|---|---|---|
| 01 | Business Understanding | Problem definition and research questions. |
| 02 | Data Collection | API extraction and source documentation. |
| 03 | Data Profiling | Data quality, schemas, and missing values. |
| 04 | Data Cleaning | Standardization and data preparation. |
| 05 | Data Transformation | Feature engineering and temporal variables. |
| 06 | Data Integration | Dataset integration and join validation. |
| 07 | Exploratory Analysis | Univariate, bivariate, and temporal analysis. |
| 08 | Statistical Analysis | Statistical tests, correlations, and advanced methods. |
| 09 | Data Visualization | Visual exploration and chart generation. |
| 10 | Insights and Recommendations | Findings, interpretation, and recommendations. |

---

## 13. Data Quality and Reproducibility

The pipeline addresses:

- Missing values.
- Duplicate records.
- Invalid measurements.
- Inconsistent units.
- Incorrect timestamps.
- Inconsistent city identifiers.
- Data-source provenance.
- Temporal and geographical alignment.

Reproducibility principles:

- Preserve raw data whenever possible.
- Keep transformations modular.
- Document assumptions.
- Use fixed random seeds for synthetic demonstrations.
- Separate real and synthetic observations.
- Validate outputs before analysis.
- Avoid presenting synthetic values as observed facts.

---

## 14. Limitations

**Monitoring Coverage:** The number and distribution of monitoring stations can differ considerably between cities.

**Geographic Resolution:** Country-level demographic indicators cannot be used as direct substitutes for city-level population statistics.

**Data Availability:** External APIs may have different historical coverage, measurement frequencies, and availability conditions.

**Measurement Comparability:** Different monitoring technologies and collection practices may affect comparisons.

**Causal Interpretation:** Statistical associations between weather and pollution do not independently establish causal relationships.

---

## 15. Future Improvements

- Integration of Copernicus atmospheric datasets.
- Additional environmental indicators.
- More detailed geographical data.
- Advanced air quality forecasting.
- XGBoost-based predictive models.
- Temporal forecasting architectures.
- Automated data quality monitoring.
- GitHub Actions CI/CD integration.
- Interactive dashboards using Streamlit or Dash.
- Cloud-based data storage and orchestration.

---

## 16. Technologies

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Manipulation | Pandas, NumPy |
| Data Collection | REST APIs, Requests |
| Data Analysis | SciPy, Statsmodels, Scikit-learn |
| Visualization | Matplotlib, Seaborn, Plotly |
| Notebooks | Jupyter |
| Testing | Pytest |
| Version Control | Git, GitHub |

The actual dependencies and technologies used should be confirmed against `requirements.txt` and the implemented source code.

---

## 17. Author

**Marwane El Abbadi**

Data & AI Engineering Student

Interested in Data Engineering, Analytics, Machine Learning, and AI-powered data platforms.

GitHub: [@marwaneproo](https://github.com/marwaneproo)

Project Repository: [Global Urban Intelligence](https://github.com/marwaneproo/global-urban-intelligence)

---

## License

If an MIT `LICENSE` file is included in the repository, the project is distributed under the MIT License.

---

**From raw data to meaningful insights.**  
**From insights to better decisions.**