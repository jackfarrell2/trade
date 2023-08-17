"""Helper functions related to CSGO trading."""
import requests
from datetime import datetime
import smtplib


def send_email(subject: str, body: str, recipients: list) -> None:
    """Send an email to desired users."""
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        # Establish secure connection
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        # Login
        smtp.login('jackcsgotrading@gmail.com', 'semerhfciausaemm')
        # Send email
        msg = f'Subject: {subject}\n\n{body}'
        for email in recipients:
            smtp.sendmail('jackcsgotrading@gmail.com', email, msg)


def create_session():
    """Create a session to make API requests."""
    s = requests.Session()
    return s


def get_single_email_info(listing: dict) -> dict:
    """Format an email for a single new listing."""
    listing_item = listing.get('item')
    name = listing_item['market_hash_name']
    pricempire_link = get_pricempire_link(name)
    # Strip odd characters for email subject & body
    name = name.replace('★ ', '')
    name = name.replace('™', '')
    # Create CSfloat link for item
    item_id = listing.get('id')
    item_link = f'https://csfloat.com/item/{item_id}'
    # Finalize subject & body
    subject = f'Potential Deal Identified: {name}'
    body = ('Beep Boop,\n\nI identified a potential deal on csfloat. '
            f'Check out the {name} by following this link: {item_link}\n\n')
    body = body + pricempire_link + "Best,\nJack's Bot <3"
    print(f'A potential deal was identified ({name}). Sending email out.')
    email_info = {'subject': subject, 'body': body}
    return email_info


def get_multiple_email_info(listings: list) -> dict:
    """Format an email for multiple new listings."""
    subject = 'Multiple Potential Deals Identified'
    body = ('Beep Boop,\n\nI identified multiple potential deals just listed '
            'on csfloat. Look them up now by following this link: '
            'https://csfloat.com/search?sort_by=most_recent\n\n')
    for listing in listings:
        listing_name = listing.get('item')['market_hash_name']
        pricempire_link = get_pricempire_link(listing_name)
        # Strip odd characters for email subject & body
        listing_name = listing_name.replace('★ ', '')
        listing_name = listing_name.replace('™', '')
        # Create CSfloat link for item
        listing_id = listing.get('id')
        listing_string = (f'-\n\n{listing_name}: https://csfloat.com/'
                          f'item/{listing_id}\n\n')
        body = body + listing_string + pricempire_link
    body = body + "\nBest,\nJack's Bot <3"
    print("Multiple potential deals identified. Sending email out.")
    email_info = {'subject': subject, 'body': body}
    return email_info


def get_pricempire_link(name: str) -> str:
    """Adjust name to fit pricempire link."""
    name = name.replace('|', '')
    name = name.replace('★', '')
    name = name.replace('™', '')
    name = name.replace('(', '')
    name = name.replace(')', '')
    name = name.strip()
    name = name.replace(' ', '-')
    name = name.replace('--', '-')
    name = name.lower()
    link = ("You may be able to check a target price here: "
            f"https://pricempire.com/item/csgo/skin/{name}\n\n")
    return link


def printf(*arg, **kwarg) -> None:
    """Print with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(timestamp, *arg, **kwarg)
