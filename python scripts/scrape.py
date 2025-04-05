from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from bs4 import BeautifulSoup

// SBR_WEBDRIVER = ''


def scrape_website(website):
    print("Launching Chrome...")

    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        driver.get(website)
        print('Waiting CAPTCHA to solve...')
        solve_res = driver.execute(
            'executeCdpCommand', 
            {
            'cmd': 'Captcha.waitForSolve',
            'params': {'detectTimeout': 10000},
            },
        )
        print('CAPTCHA solve status:', solve_res['value']['status'])
        print('Navigated! Scraping page content...')
        html = driver.page_source
        return html


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i: i + max_length] for i in range(0, len(dom_content), max_length)
    ]

def extract_job_listings(html_content):
    """Extract job listing data from Indeed's current HTML structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    
    # Find all job cards with the current class structure
    job_cards = soup.select('div.job_seen_beacon')
    
    print(f"Found {len(job_cards)} job cards")
    
    for card in job_cards:
        job_data = {}
        
        # Extract job title - updated selector
        title_elem = card.select_one('h2.jobTitle a span[title]')
        if not title_elem:
            title_elem = card.select_one('h2.jobTitle span[id^="jobTitle"]')
        if not title_elem:
            title_elem = card.select_one('h2.jobTitle a span')
            
        if title_elem:
            job_data['title'] = title_elem.get_text(strip=True)
        else:
            job_data['title'] = "N/A"
            
        # Extract company name 
        company_elem = card.select_one('span[data-testid="company-name"]')
        if company_elem:
            job_data['company'] = company_elem.get_text(strip=True)
        else:
            job_data['company'] = "N/A"
            
        # Extract location 
        location_elem = card.select_one('div[data-testid="text-location"]')
        if location_elem:
            job_data['location'] = location_elem.get_text(strip=True)
        else:
            job_data['location'] = "N/A"
            
        # Extract salary    
        salary_elem = card.select_one('.salary-snippet-container [data-testid="attribute_snippet_testid"]')
        if salary_elem:
            job_data['salary'] = salary_elem.get_text(strip=True)
        else:
            job_data['salary'] = "N/A"

        # Extract job snippet/description 
        snippet_elem = card.select_one('div[data-testid="jobsnippet_footer"]')
        if snippet_elem:
            # Clean up the text - remove list markers and extra whitespace
            description = snippet_elem.get_text(strip=True)
            description = description.replace('·', ' ').strip()
            job_data['description'] = description
        else:
            job_data['description'] = "No description available"
            
        # Extract job URL - updated selector
        link_elem = card.select_one('h2.jobTitle a.jcs-JobTitle')
        if link_elem and 'href' in link_elem.attrs:
            url = link_elem['href']
            # Make sure the URL is absolute
            if url.startswith('/'):
                job_data['url'] = "https://sg.indeed.com" + url
            else:
                job_data['url'] = url
        else:
            job_data['url'] = "N/A"
            
        # Extract job ID for reference
        if link_elem and 'data-jk' in link_elem.attrs:
            job_data['job_id'] = link_elem['data-jk']
        elif link_elem and 'id' in link_elem.attrs:
            job_data['job_id'] = link_elem['id'].replace('job_', '')
        else:
            job_data['job_id'] = "N/A"
        
        jobs.append(job_data)
        
    return jobs
