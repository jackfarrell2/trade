"""Check CSfloat for deals and send the user emails when any are found."""
__author__ = 'Jack Farrell'
__version__ = '1.0.1'

import schedule
import time
from helpers import create_session, get_single_email_info, \
    get_multiple_email_info, printf, send_email

# Settings
# Guns to search for (★ = knives & guns)
ALLOWED_GUNS = ['AWP', 'AK-47', 'M4A1-S', 'M4A4', 'USP-S', '★']
MINIMUM_PRICE = 1000  # Minimum price of skins (in cents)
MAXIMUM_PRICE = 50000  # Maximum price of skins (in cents)
MINIMUM_DISCOUNT = 24  # Minium percent discount from Steam Market price
REQUEST_INTERVAL = 31  # Interval (in seconds) to request skin listings
REQUEST_CHECKPOINT = 100  # Number of requests before user is updated
REQUEST_LIMIT = 20  # Number of listings to API request (after initial)
WELL_WORNS = False  # Include well-worn skins
SOUVENIRS = False  # Include souvenir skins
RECIPIENT_EMAILS = ['jackfarrell860@gmail.com']  # Emails to send updates to

interested_listings = []  # Track the sessions listings the bot finds
interested_listings_ids = []  # Track just the ids of the interested listings
# Give the user periodic updates on the session
session_information = {'Requests': 0, 'Deals': 0}


def main() -> None:
    """Request CSfloat API at a given interval."""
    schedule.every(REQUEST_INTERVAL).seconds.do(request_listings)
    request_listings()  # Send initial request
    # Request perpetually
    while True:
        schedule.run_pending()
        time.sleep(1)


def request_listings() -> None:
    """Request skins from CSfloat."""
    # Record number of interests before this request
    initial_interest_count = len(interested_listings)
    # Initial message to user
    if session_information['Requests'] == 0:
        print('Listening for deals...')
    # Update counts of requests this session
    session_information['Requests'] += 1
    # Print periodic updates to user
    # Check if this is a checkpoint
    checkpoint = session_information['Requests'] % REQUEST_CHECKPOINT == 0
    if checkpoint and session_information['Requests'] != 1:
        printf(f"{REQUEST_CHECKPOINT} requests completed. Total number of "
               "potential deals identified so far "
               f"is {session_information['Deals']}")
    # Get listing Data
    session = create_session()
    base_url = 'https://csfloat.com/api/v1/listings?type=buy_now'
    # Don't include request limit on first request
    if session_information['Requests'] != 1:
        variable_url = (f'&min_price={MINIMUM_PRICE}'
                        f'&max_price={MAXIMUM_PRICE}&sort_by=most_recent'
                        f'&limit={REQUEST_LIMIT}')
    else:
        variable_url = (f'&min_price={MINIMUM_PRICE}'
                        f'&max_price={MAXIMUM_PRICE}&sort_by=most_recent')
    url = base_url + variable_url
    response = session.get(url)
    listings = response.json()
    # Filter listings
    for listing in listings:
        # Assume listing is not a deal and does not fit skin requirements
        deal = False
        fits_skin_reqs = False
        listing_price = listing.get('price')  # Price on CSfloat
        item = listing.get('item')
        item_price = item['scm'].get('price')  # Price on Steam
        item_name = item['market_hash_name']
        # If discounted from Steam, check if deal
        if item_price > listing_price:
            # Calculate discount %
            difference = (1 - (listing_price / item_price)) * 100
            # Set to deal if discount % is high enough
            if difference > MINIMUM_DISCOUNT:
                deal = True
        # Filter guns by desired guns
        for allowed_gun in ALLOWED_GUNS:
            if allowed_gun in item_name:
                fits_skin_reqs = True
        # Filter out any well-worns or souvenirs if requested
        if fits_skin_reqs:
            well_worn = item['wear_name'] == 'Well-Worn'
            souvenir = item['is_souvenir'] == 'true'
            # Filter well-worn skins
            if WELL_WORNS is False:
                if well_worn:
                    fits_skin_reqs = False
            # Filter souvenir skins
            if SOUVENIRS is False:
                if souvenir:
                    fits_skin_reqs = False
        # Add to interested listings if all reqs are met
        if fits_skin_reqs and deal:
            listing_id = listing.get('id')
            if listing_id not in interested_listings_ids:
                interested_listings_ids.append(listing_id)
                interested_listings.append(listing)
    # Check if a new email is necessary
    new_listings_count = len(interested_listings) - initial_interest_count
    # No new listings this request
    if new_listings_count == 0:
        return  # No update needed
    # One new listing found this request
    elif new_listings_count == 1:
        # Grab the listing in question
        new_listing = interested_listings[-1]
        # Prep the email and update the session deal count
        email_info = get_single_email_info(new_listing)
        session_information['Deals'] += 1
    # Multiple new listings found this request (common on first request)
    elif new_listings_count > 1:
        # Prep the email
        interest_difference = (new_listings_count * -1)
        only_different_listings = interested_listings[interest_difference:]
        email_info = get_multiple_email_info(only_different_listings)
        # Update the session deal count
        session_information['Deals'] += (interest_difference * -1)

    # Send the email
    subject = email_info['subject']
    body = email_info['body']
    send_email(subject, body, RECIPIENT_EMAILS)
    return


if __name__ == '__main__':
    main()
