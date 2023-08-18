"""Check CSfloat for deals and send the user emails when any are found."""
__author__ = 'Jack Farrell'
__version__ = '1.0.1'

import schedule
import time
from helpers import create_session, get_single_email_info, \
    get_multiple_email_info, printf, send_email, get_auction_email_info, \
    check_is_in_timeframe

# Settings
# Guns to search for (★ = knives & guns)
ALLOWED_GUNS = ['AWP', 'AK-47', 'M4A1-S', 'M4A4', 'Desert Eagle', 'USP-S', '★']
MINIMUM_PRICE = 1000  # Minimum price of skins (in cents)
MAXIMUM_PRICE = 50000  # Maximum price of skins (in cents)
MINIMUM_DISCOUNT = 23.5  # Minium percent discount from Steam Market price
REQUEST_INTERVAL = 30  # Interval (in seconds) to request skin listings
AUCTION_REQUEST_INTERVAL = 50  # Interval to check auctions (in minutes)
AUCTION_REQUEST_HOURS = 1  # Hours to check out for auction listings
REQUEST_CHECKPOINT = 30  # Number of requests before user is updated
REQUEST_LIMIT = 49  # Number of listings to API request (after initial)
WELL_WORNS = False  # Include well-worn skins
SOUVENIRS = False  # Include souvenir skins
RECIPIENT_EMAILS = ['jackfarrell860@gmail.com']  # Emails to send updates to
BASE_API_URL = 'https://csfloat.com/api/v1/listings?'

interested_listings = []  # Track the sessions listings the bot finds
# Track the floats of interested listings (to catch relistings)
interested_listings_floats = []
# Give the user periodic updates on the session
session_information = {'Requests': 0, 'Deals': 0}


def main() -> None:
    """Request CSfloat API at a given interval."""
    try:
        print("You can press CTRL + C at any point to close the program.")
        schedule.every(REQUEST_INTERVAL).seconds.do(request_listings)
        schedule.every(AUCTION_REQUEST_INTERVAL).minutes.do(request_auctions)
        # Send initial request
        request_listings()
        request_auctions()
        # Request perpetually
        while True:
            schedule.run_pending()
            time.sleep(1)
    # Handle program close
    except KeyboardInterrupt:
        exit_handler()
        print('\nGoodbye!')


def request_listings() -> None:
    """Request skin listings from CSfloat."""
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
    # Get listing data
    session = create_session()
    # base_url = 'https://csfloat.com/api/v1/listings?type=buy_now'
    # Don't include request limit on first request
    if session_information['Requests'] != 1:
        variable_url = (f'type=buy_now&min_price={MINIMUM_PRICE}'
                        f'&max_price={MAXIMUM_PRICE}&sort_by=most_recent'
                        f'&limit={REQUEST_LIMIT}')
    else:
        variable_url = (f'type=buy_now&min_price={MINIMUM_PRICE}'
                        f'&max_price={MAXIMUM_PRICE}&sort_by=most_recent')
    url = BASE_API_URL + variable_url
    response = session.get(url)
    listings = response.json()
    # Filter listings
    for listing in listings:
        is_interesting_listing = check_is_interesting_listing(listing)
        if is_interesting_listing:
            listing_float = listing['item']['float_value']
            if listing_float not in interested_listings_floats:
                interested_listings_floats.append(listing_float)
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


def request_auctions(hours: int = AUCTION_REQUEST_HOURS) -> None:
    """Check auction listings."""
    interested_auctions = []
    # Get listing data
    expiring_auctions = []
    page = 0
    end_of_auctions = False
    # Determine how many pages of listings we need
    while end_of_auctions is False:
        # Get one page of listings at a time
        url = ('https://csfloat.com/api/v1/listings?type=auction'
               f'&sort_by=expires_soon'
               f'&max_price={MAXIMUM_PRICE}&page={page}')
        session = create_session()
        response = session.get(url)
        page_listings = response.json()
        # Add to global listings
        for listing in page_listings:
            expiring_auctions.append(listing)
        # Check if this is the last necessary page
        last_listing_expires_at = (page_listings[-1]
                                   ['auction_details']['expires_at'])
        is_soon = check_is_in_timeframe(
            last_listing_expires_at, AUCTION_REQUEST_HOURS)
        if is_soon is False:
            end_of_auctions = True
        else:
            page += 1
    # Filter listings
    for listing in expiring_auctions:
        # Stop looking once past given timeframe
        expires_at = listing['auction_details']['expires_at']
        expires_soon = check_is_in_timeframe(expires_at,
                                             AUCTION_REQUEST_HOURS)
        if expires_soon is False:
            break
        is_interesting_listing = check_is_interesting_listing(listing)
        if is_interesting_listing:
            interested_auctions.append(listing)
    # Update if new auctions were found
    if len(interested_auctions) > 0:
        email_info = get_auction_email_info(interested_auctions)
        # Send the email
        subject = email_info['subject']
        body = email_info['body']
        send_email(subject, body, RECIPIENT_EMAILS)
        return
    return


def check_is_interesting_listing(listing):
    """Check if a listing fits the given parameters."""
    # Assume listing is not a deal and does not fit skin requirements
    is_deal = False
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
            is_deal = True
    if is_deal:
        # Check if desired skin
        for allowed_gun in ALLOWED_GUNS:
            if allowed_gun in item_name:
                fits_skin_reqs = True
        if fits_skin_reqs:
            if WELL_WORNS is False:
                well_worn = item['wear_name'] == 'Well-Worn'
                if well_worn:
                    fits_skin_reqs = False
            if SOUVENIRS is False:
                souvenir = item['is_souvenir'] == 'true'
                if souvenir:
                    fits_skin_reqs = False
    # Add to interested listings if all reqs are met
    if fits_skin_reqs and is_deal:
        return True
    else:
        return False


def exit_handler():
    """Give user option to check auctions while the bot is off."""
    check_offline_auctions = input(
        '\nDo you want me to check upcoming'
        'auctions while you are away? (yes, no): ')
    if check_offline_auctions.lower() == "yes":
        hours = input('\nHow many hours will you be away?: ')
        request_auctions(int(hours))
    return


if __name__ == '__main__':
    main()
