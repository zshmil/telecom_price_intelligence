import re
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import datetime
import concurrent.futures
from urllib.parse import urljoin, urlparse


today = datetime.datetime.now()
url = 'https://www.kamaze.co.il'


def get_companies_links():
    """
    Fetches the URLs of different companies listed on the website.
    Returns:
        list: A list of URLs for the companies.
    """

    resp = requests.get(''.join([url, '/Compare/1/Cellular']), timeout=15)
    resp.raise_for_status()
    soup = bs(resp.text, 'html.parser')

    companies_anc = soup.select('div.companybox.in-row')
    companies_arr = []
    for c in companies_anc:
        link = c.find('a', href=True)
        if link:
            companies_arr.append(link['href'])

    # Fallback for pages where the original companybox class has changed.
    if not companies_arr:
        for link in soup.find_all('a', href=True):
            if re.search(r'/Companies/\d+/[^/]+/Cellular/?$', link['href'], re.I):
                companies_arr.append(link['href'])

    companies_arr = list(dict.fromkeys(companies_arr))
    if not companies_arr:
        raise ValueError('No company links found. Check the website HTML selectors.')

    return companies_arr


def fetch_url(company_url):
    """
    Fetches HTML content from a given URL.
    Args:
        company_url (str): The URL to fetch the content from.
    Returns:
        str: HTML content of the page, or None if the request fails.
    """

    try:
        response = requests.get(urljoin(url, company_url), timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f'Error fetching {company_url}: {e}')
        return None


def get_company_data(html_content, company_url):
    """
    Retrieves rate plan data for a specific company.
    Args:
        html_content (str): HTML content of the company page.
        company_url (str): URL of the company page.
    Returns:
        list: A list of dictionaries with rate plan details.
    """

    company_data = []
    soup = bs(html_content, 'html.parser')
    desc_html = soup.find_all(name='article', attrs={'class': 'topitem'})

    # Example: /Companies/6383/Partner/Cellular -> Partner
    path_parts = urlparse(company_url).path.strip('/').split('/')
    carrier = path_parts[-2] if len(path_parts) >= 2 else company_url

    for desc in desc_html:
        name = desc.find('h3', class_='topitem-caption-heading')
        if not name:
            continue

        description = desc.find(name='p', attrs={'class': 'topitem-caption-desc'})
        rate_plan_name = name.get_text(' ', strip=True)
        rate_plan_desc = description.get_text(' ', strip=True) if description else ''
        rate_plan_details = desc.find_all(name='span', attrs={'class': 'topitem-feature-label'})
        rate_plan_tariff = desc.find('span', attrs={'class': 'topitem-pricebox-price'})
        rate_plan_tariff_text = rate_plan_tariff.get_text(' ', strip=True) if rate_plan_tariff else ''

        minutes_match = next((
            match for detail in rate_plan_details
            if (match := re.search(r'עד\s+(\d+)\s+דקות שיחה', detail.get_text(' ', strip=True)))
        ), None)
        data_match = re.search(r"\d+\s*GB|\d+\s*ג['׳]?יגה", rate_plan_desc, re.I)
        price_match = re.search(r'\d+(?:[.,]\d{1,2})?', rate_plan_tariff_text)

        company_data.append({
            'carrier': carrier,
            'rate_plan_name': ''.join(char for char in rate_plan_name if char.isprintable()),
            'rate_plan_desc': rate_plan_desc,
            'rate_plan_details': [span.get_text(' ', strip=True) for span in rate_plan_details],
            'international_calling_minutes': minutes_match.group(1) if minutes_match else None,
            'data_volume': data_match.group() if data_match else None,
            'price': price_match.group().replace(',', '.') if price_match else None
        })

    return company_data


def get_rate_plan_list():
    """
    Aggregates rate plan data from all companies listed on the website.
    Company pages are downloaded concurrently to reduce collection time.
    Returns:
        list: A consolidated list of dictionaries with rate plan details.
    """

    companies_urls = get_companies_links()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        html_contents = list(executor.map(fetch_url, companies_urls))

    plans = []
    for content, company_url in zip(html_contents, companies_urls):
        if content:
            plans.extend(get_company_data(content, company_url))

    if not plans:
        raise ValueError('No rate plans found. Check the website HTML selectors.')

    return plans


def get_df():
    """
    Converts the collected rate plan data into a pandas DataFrame.
    """

    plans = get_rate_plan_list()
    df = pd.DataFrame(plans)
    return df


def set_price_column_type_to_numeric(df):
    """
    Converts the price column in the DataFrame to a numeric type.
    """

    df['price'] = pd.to_numeric(df.price, errors='coerce')
    return df


def add_execution_date_column(df):
    """
    Adds an execution date column to the DataFrame.
    """

    df = df.assign(run_date=today.strftime('%Y-%m-%d'))
    return df


def split_list_to_cloums(df):
    """
    Splits a list within a single DataFrame column into multiple columns.
    The original function name is preserved for compatibility.
    """

    list_length = df['rate_plan_details'].apply(len).max()
    new_cols = pd.DataFrame(df['rate_plan_details'].tolist(), index=df.index).iloc[:, :list_length]
    new_cols.columns = [f'element_{i}' for i in range(len(new_cols.columns))]
    return new_cols


def join_columns_broken_from_list(df, new_cols):
    """
    Joins the newly created columns from a list back to the main DataFrame.
    """

    df = df.join(new_cols)
    return df


def select_df_columns(df):
    """
    Selects and orders specific columns in the DataFrame.
    """

    # A plan may have fewer than five features.
    for col in ['element_1', 'element_4']:
        if col not in df.columns:
            df[col] = None

    df = df[['run_date', 'carrier', 'rate_plan_name', 'element_1', 'element_4',
             'international_calling_minutes', 'data_volume', 'price']]
    return df


def set_index(df):
    """
    Sets the run_date column as the DataFrame index.
    """

    df = df.set_index('run_date')
    return df


def rename_columns_name(df):
    """
    Renames the columns to the names used in the original report.
    """

    df = df.rename(columns={
        'element_1': 'period',
        'element_4': 'promotion'
    })
    return df


def get_final_df():
    """
    Orchestrates the creation of the final DataFrame.
    """

    df = get_df()
    new_cols = split_list_to_cloums(df)

    df = (df.pipe(set_price_column_type_to_numeric)
            .pipe(add_execution_date_column)
            .pipe(join_columns_broken_from_list, new_cols=new_cols)
            .pipe(select_df_columns)
            .pipe(set_index)
            .pipe(rename_columns_name)
         )
    return df


if __name__ == '__main__':
    try:
        df = get_final_df()
        print(df)
    except Exception as exception:
        print(exception)
        raise
