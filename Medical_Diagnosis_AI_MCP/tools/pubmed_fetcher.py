# https://pubmed.ncbi.nlm.nih.gov/?term=fever
import requests
from bs4 import BeautifulSoup

def fetch_pubmed_articles_with_metadata(query: str, max_results=3, use_mock_if_empty=True):
    '''- use_mock_if_empty -A boolean flag that decides whether to return fake/mock data when no real articles are found or an error occurs.
- Default = True because:
- It ensures the function always returns something (useful in demos, testing, or downstream code that expects structured data).
'''
    headers = {"User-Agent": "Mozilla/5.0"} #we give this header so that the site dont block thinking its an agent trying to fetch data

    # Step 1: Search PubMed website for paper --> entrez/eutils/esearch.fcgi
    #- Step 1: Search PubMed IDs
    # - Calls PubMed’s esearch API to find article IDs for the query
    # Esearch API-- Used to search a database (like PubMed) and retrieve a list of IDs that match a query.
    #- Output: A list of PubMed IDs (PMIDs) that match the query.
    #- Analogy: Think of it like a search engine — you type a keyword, and it gives you a list of article IDs.


    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"  
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    try:
        search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10).json()
        #- search_response is the JSON returned by PubMed (contains IDs and metadata about the search).
        '''search_response- The JSON object returned by PubMed’s esearch API.
{
  "esearchresult": {
    "count": "2",
    "idlist": ["12345", "67890"]
                   }
}
         '''
        id_list = search_response["esearchresult"]["idlist"]
        print("Found PubMed IDs:", id_list)
        if not id_list:
            raise ValueError("No IDs found for this query.")

        ids = ",".join(id_list)

        # Step 2: Fetch article summaries
        #Step 2: Fetch article metadata
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        #EFetch API -Used to fetch full details (metadata, abstracts, etc.) for specific IDs returned by ESearch. 
        fetch_params = {
            "db": "pubmed",
            "id": ids,
            "retmode": "xml"
        }
        fetch_response = requests.get(fetch_url, params=fetch_params, headers=headers, timeout=10)
        #- fetch_response is the raw HTTP response object (with .text containing XML).
        #- The timeout parameter tells the requests library how long (in seconds) to wait for a response from the server before giving up.



        soup = BeautifulSoup(fetch_response.text, "lxml")
        #- BeautifulSoup parses the XML into structured tags.
        articles_xml = soup.find_all("pubmedarticle")
        #- BeautifulSoup(..., "lxml") → parses that XML into a navigable tree of tags.

        print("Articles found in XML:", len(articles_xml))

        articles_info = [] # - Loops through each PubmedArticle will find article based on title,abstract,authors,date
        for article, pmid in zip(articles_xml, id_list):
            title_tag = article.find("articletitle")
            abstract_tag = article.find("abstract")
            date_tag = article.find("pubdate")
            author_tags = article.find_all("author")

            # Title
            title = title_tag.get_text(strip=True) if title_tag else "No title"

            # Abstract
            abstract = abstract_tag.get_text(separator=" ", strip=True) if abstract_tag else "No abstract available"

            # Authors
            authors = []
            for author in author_tags:
                last = author.find("lastname")
                fore = author.find("forename")
                if last and fore:
                    authors.append(f"{fore.get_text()} {last.get_text()}")
                elif last:
                    authors.append(last.get_text())
            authors = authors if authors else ["No authors listed"]

            # Publication Date
            pub_date = "No date"
            if date_tag:
                year = date_tag.find("year")
                month = date_tag.find("month")
                pub_date = f"{month.get_text()} {year.get_text()}" if year and month else year.get_text() if year else "No date"

            # PubMed Article URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            print(f"Article: {title}\n   - Authors: {authors}\n   - Date: {pub_date}\n   - URL: {url}\n")
           #- Builds a dictionary for each article and appends to articles_info.

            articles_info.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "publication_date": pub_date,
                "article_url": url
            })
        #fallback path -- If no articles are found or an error occurs:

        if not articles_info and use_mock_if_empty:
            print("No valid articles found, returning mock data.")
            return [{
                "title": "Simulated Study on Fever",
                "abstract": "This is a simulated abstract on the treatment of fever in adults.",
                "authors": ["John Doe", "Jane Smith"],
                "publication_date": "March 2024",
                "article_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
            }]
        return articles_info

    except Exception as e:
        print(f"Error during PubMed fetch: {e}")
        if use_mock_if_empty:
            return [{
                "title": "Simulated Study on Fever",
                "abstract": "This is a simulated abstract on the treatment of fever in adults.",
                "authors": ["John Doe", "Jane Smith"],
                "publication_date": "March 2024",
                "article_url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
            }]
        else:
            return [{"message": f"Error: {e}"}]

