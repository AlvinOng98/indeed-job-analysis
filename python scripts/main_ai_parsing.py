import streamlit as st
from scrape import (
    scrape_website,
    split_dom_content,
    clean_body_content,
    extract_body_content
)
from parse import parse_with_ollama

st.title("Indeed Job Scraper")
job_search_keyword = st.text_input("Enter a Job Title: ")
location_keyword = st.text_input("Enter a Location: ")
num_pages = st.number_input("Enter number of pages to scrape", min_value=1, max_value=20, value=3, step=1)  # Default: 3 pages

pagination_url = "https://sg.indeed.com/jobs?q={}&l={}&radius=10&start={}"


if st.button("Scrape Site"):
    st.write("Scraping the website")

    all_cleaned_content = [] # Store all job postings

    for page_no in range(num_pages):  # Loop through pages
        url = pagination_url.format(job_search_keyword, location_keyword, page_no * 10)
        st.write(f"Scraping page {page_no + 1}...")  # Display progress
        
        result = scrape_website(url)
        body_content = extract_body_content(result)
        cleaned_content = clean_body_content(body_content)

        all_cleaned_content.append(cleaned_content)  # Store scraped content

    # Save to a text file
    with open("scraped_jobs.txt", "w", encoding="utf-8") as file:
        for job in all_cleaned_content:
            file.write(job + "\n\n")  # Add spacing between job postings

    st.session_state.dom_content = "\n\n".join(all_cleaned_content)

    with st.expander("View DOM content"):
        st.text_area("DOM Content", cleaned_content, height=300)

    st.success(f"Scraping complete! Data saved to `scraped_jobs.txt`")    

if "dom_content" in st.session_state:
     parse_description = st.text_area("Describe what you want to parse?")

     if st.button("Parse Content"):
         if parse_description:
             st.write("Parsing the content")
             dom_chunks = split_dom_content(st.session_state.dom_content)
             result = parse_with_ollama(dom_chunks, parse_description)
             st.write(result)
