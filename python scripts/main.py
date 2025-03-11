import streamlit as st
import pandas as pd
from scrape import scrape_website
from bs4 import BeautifulSoup

st.title("Indeed Job Scraper")
job_search_keyword = st.text_input("Enter a Job Title: ")
location_keyword = st.text_input("Enter a Location: ")
num_pages = st.number_input("Enter number of pages to scrape", min_value=1, max_value=20, value=3, step=1)  # Default: 3 pages

pagination_url = "https://sg.indeed.com/jobs?q={}&l={}&radius=10&start={}"

# Debug mode toggle
debug_mode = st.checkbox("Enable Debug Mode")

def extract_job_listings(html_content):
    """Extract job listing data from Indeed's current HTML structure"""
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    
    # Find all job cards with the current class structure
    job_cards = soup.select('div.job_seen_beacon')
    
    if debug_mode:
        st.write(f"Found {len(job_cards)} job cards")
    
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
            
        # Extract company name - updated selector
        company_elem = card.select_one('span[data-testid="company-name"]')
        if company_elem:
            job_data['company'] = company_elem.get_text(strip=True)
        else:
            job_data['company'] = "N/A"
            
        # Extract location - updated selector
        location_elem = card.select_one('div[data-testid="text-location"]')
        if location_elem:
            job_data['location'] = location_elem.get_text(strip=True)
        else:
            job_data['location'] = "N/A"
            
        salary_elem = card.select_one('.salary-snippet-container [data-testid="attribute_snippet_testid"]')
        if salary_elem:
            job_data['salary'] = salary_elem.get_text(strip=True)
        else:
            job_data['salary'] = "N/A"

        # Extract job snippet/description - updated selector
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
            
        # No clear date posted element in this HTML sample, so use a placeholder
        job_data['date_posted'] = "Not specified"
        
        # Extract job ID for reference
        if link_elem and 'data-jk' in link_elem.attrs:
            job_data['job_id'] = link_elem['data-jk']
        elif link_elem and 'id' in link_elem.attrs:
            job_data['job_id'] = link_elem['id'].replace('job_', '')
        else:
            job_data['job_id'] = "N/A"
        
        jobs.append(job_data)
        
    return jobs

if st.button("Scrape Site"):
    st.write("Scraping the website")

    all_jobs = []  # Store all job postings as structured data
    
    progress_bar = st.progress(0)
    
    for page_no in range(num_pages):  # Loop through pages
        url = pagination_url.format(job_search_keyword, location_keyword, page_no * 10)
        st.write(f"Scraping page {page_no + 1} of {num_pages}...")  # Display progress
        
        # Update progress bar
        progress_bar.progress((page_no + 1) / num_pages)
        
        try:
            html_content = scrape_website(url)
            
            # Debug option
            if debug_mode:
                st.subheader(f"HTML Analysis for Page {page_no + 1}")
                
                # Count job cards for debugging
                soup = BeautifulSoup(html_content, 'html.parser')
                job_cards = soup.select('div.job_seen_beacon')
                st.write(f"Found {len(job_cards)} job cards in HTML")
                
                # Sample of first job card HTML if available
                if job_cards:
                    with st.expander("Sample of first job card HTML"):
                        st.code(str(job_cards[0]), language="html")
                
                # Allow download of the full HTML
                st.download_button(
                    label=f"Download Full HTML for Page {page_no + 1}",
                    data=html_content,
                    file_name=f"indeed_page_{page_no + 1}.html",
                    mime="text/html"
                )
            
            jobs_on_page = extract_job_listings(html_content)
            all_jobs.extend(jobs_on_page)
            st.write(f"Found {len(jobs_on_page)} jobs on page {page_no + 1}")
        except Exception as e:
            st.error(f"Error scraping page {page_no + 1}: {str(e)}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            continue

    if all_jobs:
        # Convert to DataFrame
        jobs_df = pd.DataFrame(all_jobs)
        
        # Display DataFrame columns for debugging
        if debug_mode:
            st.subheader("DataFrame Columns")
            st.write(jobs_df.columns.tolist())
            
            st.subheader("Data Sample (First Row)")
            st.write(jobs_df.iloc[0] if len(jobs_df) > 0 else "No data")
        
        # Save to CSV
        jobs_df.to_csv("scraped_jobs.csv", index=False)
        
        # Store in session state
        st.session_state.jobs_df = jobs_df
        
        # Display as table
        st.subheader(f"Found {len(all_jobs)} Job Listings")
        st.dataframe(jobs_df)
        
        # Add filters if we have enough data
        if len(all_jobs) > 0 and 'company' in jobs_df.columns and 'location' in jobs_df.columns:
            with st.expander("Filter Results"):
                col1, col2 = st.columns(2)
                
                with col1:
                    companies = ['All'] + sorted(jobs_df['company'].unique().tolist())
                    company_filter = st.selectbox("Filter by Company", companies)
                
                with col2:
                    locations = ['All'] + sorted(jobs_df['location'].unique().tolist())
                    location_filter = st.selectbox("Filter by Location", locations)
            
            # Apply filters
            filtered_df = jobs_df.copy()
            if company_filter != 'All':
                filtered_df = filtered_df[filtered_df['company'] == company_filter]
            if location_filter != 'All':
                filtered_df = filtered_df[filtered_df['location'] == location_filter]
            
            # Display filtered data
            st.dataframe(filtered_df)
        
        # Add download button
        st.download_button(
            label="Download CSV",
            data=jobs_df.to_csv(index=False).encode('utf-8'),
            file_name='scraped_jobs.csv',
            mime='text/csv',
        )
        
        st.success(f"Scraping complete! Data saved to `scraped_jobs.csv`")
    else:
        st.error("No jobs found. Try different search terms or increase the number of pages.")
