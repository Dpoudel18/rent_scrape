import requests
from bs4 import BeautifulSoup
import csv
import re
import json
import time

# Base URL of Craigslist apartment listings in Pittsburgh
base_url = 'https://pittsburgh.craigslist.org/search/apa#search=1~gallery~0~0'

# Create a CSV file to store the data
with open('craigslist_apartments_final.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(['Name', 'Type', 'Price', 'Neighborhood', 'Address', 'Latitude', 'Longitude', 
                     'Bedrooms', 'Bathrooms', 'Sq. Footage', 'Rent Period', 'Laundry', 
                     'Parking', 'Link to Listing'])

    page_number = 0
    listings_found = True

    while listings_found:
        # URL of the current page
        url = f'{base_url}?s={page_number * 120}'  # Craigslist shows 120 listings per page
        print(f"Scraping page {page_number + 1}: {url}")

        # Send a request to get the content of the webpage
        response = requests.get(url)
        html_content = response.content

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all apartment listings
        listings = soup.find_all('li', class_='cl-static-search-result')

        # Check if there are any listings on the current page
        if not listings:
            listings_found = False
            break  # Stop the loop if no more listings are found

        # Loop through each listing to extract the required information
        for listing in listings:
            # Extract the link to the individual apartment page
            link_tag = listing.find('a')
            if link_tag:
                link = link_tag['href']
            else:
                link = 'Link not available'

            # Fetch the individual apartment page
            listing_response = requests.get(link)
            listing_soup = BeautifulSoup(listing_response.content, 'html.parser')

            # Extract name of the listing
            name = listing_soup.find('title').get_text() if listing_soup.find('title') else 'N/A'

            # Extract data from the structured ld+json script (if it exists)
            ld_json_data = listing_soup.find('script', type='application/ld+json', id="ld_posting_data")
            if ld_json_data and ld_json_data.string:
                try:
                    data = json.loads(ld_json_data.string)
                    neighborhood = data.get('address', {}).get('addressLocality', 'N/A')
                    latitude = data.get('latitude', 'N/A')
                    longitude = data.get('longitude', 'N/A')
                    bedrooms = data.get('numberOfBedrooms', 'N/A')
                    bathrooms = data.get('numberOfBathroomsTotal', 'N/A')
                    apartment_type = data.get('@type', 'N/A') 
                except json.JSONDecodeError:
                    address = neighborhood = latitude = longitude = bedrooms = bathrooms = 'N/A'
            else:
                address = neighborhood = latitude = longitude = bedrooms = bathrooms = 'N/A'

            # Extract price
            price = listing_soup.find('span', class_='price').get_text() if listing_soup.find('span', class_='price') else 'N/A'

            # Extract address
            address = listing_soup.find('h2', class_='street-address').get_text() if listing_soup.find('h2', class_='street-address') else 'N/A'

            # Extract square footage (define housing_info and add handling)
            housing_info = listing_soup.find('span', class_='housing')
            sq_ft = 'N/A'
            if housing_info:
                sq_ft_match = re.search(r'(\d+)ft', housing_info.text)
                if sq_ft_match:
                    sq_ft = sq_ft_match.group(1)

            # Extract rent period from the <a> tag
            rent_period_elem = listing_soup.find('div', class_='attr rent_period')
            rent_period = rent_period_elem.find('a').get_text() if rent_period_elem and rent_period_elem.find('a') else 'N/A'

            laundry = "N/A"
            parking = "N/A"

            # Loop through the 'attr' divs to find laundry and parking info
            attrs = listing_soup.find_all('div', class_='attr')

            for attr in attrs:
                a_tag = attr.find('a')
                if a_tag:
                    href = a_tag['href']
                    text = a_tag.get_text().strip()

                    # Check for laundry information
                    if 'laundry' in href:
                        laundry = text
                    # Check for parking information
                    if 'parking' in href:
                        parking = text

            # Write the data into the CSV file
            writer.writerow([name, apartment_type, price, neighborhood, address, latitude, longitude, 
                             bedrooms, bathrooms, sq_ft, rent_period, laundry, parking, link])

        # Increment the page number to move to the next page
        page_number += 1

        # Optional: Add a delay between requests to avoid overwhelming the server
        time.sleep(1)

# Test the CSV output
print("Data written to craigslist_apartments_final.csv successfully.")