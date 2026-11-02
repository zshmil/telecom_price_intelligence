# Telecom Competitive Intelligence Automation

**From 90 minutes of manual research to an 8-second automated workflow.**

I originally built this Python workflow while working in marketing analytics at Partner Communications (formerly Orange Israel). The marketing team needed up-to-date information on competitors' mobile plans, prices, and promotions. Collecting that information meant manually calling competitors as prospective customers, checking offers, and compiling the findings into a report.

The process took **approximately 90 minutes each time**. I replaced the repetitive research and data-entry steps with a script that collected published plan details from a telecom price-comparison website, extracted the relevant fields, and prepared structured data for reporting. The original production workflow also emailed reports to marketing managers.

## The result

| | Before | After |
|---|---|---|
| Process | Manual competitor calls, price checks, and report preparation | Automated web collection, parsing, and reporting |
| Execution time | ~90 minutes | ~8 seconds |
| Time reduction | | **99.9%** |
| Speed improvement | | **675x faster** |
| Annual time saved | | **~375 hours**, assuming about 250 runs per year |

**These measurements describe the original business workflow**, not a new benchmark of this GitHub version. The code shared here is a simplified version of the extraction and transformation logic, without the original company's email-reporting integration.

## How the automation worked

1. **Discover competitors.** `get_companies_links()` finds mobile carrier pages on the comparison website.
2. **Collect data concurrently.** `ThreadPoolExecutor` downloads carrier pages in parallel, avoiding the delay of fetching each one separately.
3. **Extract plan details.** `BeautifulSoup` and regular expressions identify carrier names, plan names, prices, data allowances, international calling minutes, and selected promotional details.
4. **Prepare a usable dataset.** `pandas` standardizes prices, adds the collection date, and produces a structured table.
5. **Support historical analysis.** The DataFrame includes the run date, so its results can be saved as daily snapshots for pricing comparisons over time. In the original business workflow, historical pricing data supported competitive benchmarking and market trend analysis. This published script stops at producing the DataFrame.

The biggest time saving came from **removing the manual research process**. Parallel HTTP requests and automated parsing made the data collection itself fast, but the 8-second result should not be understood as a promise about today's website or network conditions.

## Technologies

Python · Requests · BeautifulSoup · pandas · Regular expressions · Concurrent futures · CSV

## Run the script

Install dependencies:

```bash
pip install requests beautifulsoup4 pandas
```

Run:

```bash
python telecom_price_intelligence.py
```

The script prints the resulting pandas DataFrame, including the collection date, carrier, plan, price, and selected plan details. It does not connect to GCP, email reports, or save historical snapshots automatically.

## Notes

- This version keeps the simple, function-based structure and pandas `.pipe()` transformations of the original script.
- The CSS selectors reflect the website layout used when the workflow was developed. **The current live website has not been verified**, so selectors may need updating.
- The `period` and `promotion` columns are based on feature positions in the original page layout; these may not remain consistent if the website changes.
- This repository does not include employer data, credentials, or internal integrations. Respect the website's terms and access restrictions before collecting live data.
