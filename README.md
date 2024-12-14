# Comprehensive SEO Analysis Tool

This tool provides in-depth SEO analysis for websites, including competitor analysis and keyword research.

## Features

- Complete on-page SEO analysis
- Technical SEO audit
- Competitor analysis
- Keyword density analysis
- Content quality assessment
- Mobile-friendliness check
- Image optimization check
- Meta tags analysis
- Domain information
- Internal and external link analysis

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the analysis using:
```bash
python main.py [URL] [KEYWORD]
```

Example:
```bash
python main.py https://n8n.io "n8n"
```

The tool will:
1. Analyze the provided URL
2. Search for top competitors
3. Perform comprehensive SEO analysis
4. Generate a detailed report in JSON format

## Analysis Components

### On-Page Analysis
- Title tag optimization
- Meta description analysis
- Heading structure
- Content quality and length
- Keyword density
- Image optimization

### Technical Analysis
- URL structure
- Mobile responsiveness
- Domain information
- Internal/external links
- Page load speed indicators

### Competitor Analysis
- Top 5 competing pages for the keyword
- Comparison of key metrics
- Content length analysis
- Meta tag comparison

## Output

The tool generates a JSON file containing:
- Overall SEO score
- Key findings and recommendations
- Detailed analysis results
- Competitor comparison
- Technical metrics

## Requirements

- Python 3.7+
- Internet connection
- Required packages listed in requirements.txt
