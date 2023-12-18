# Trade

## Overview

Welcome to the Trade app! This program periodically checks csfloat.com for new deals and alerts users when interesting deals are identified via email. Customize email settings and search parameters to tailor the app to your preferences.

[CSFloat](https://csfloat.com/)

## Getting Started

1. Clone the Trade app repository from [GitHub](https://github.com/yourusername/trade-app).
2. Install the necessary dependencies.
3. Run "python trade.py" to run the bot. You can specify a ceiling price point in dollars with an argument if you wish.
4. You will periodically receive emails with links to the item as well as links to the PriceEmpire page to review the prices.


## Customize Parameters

Alter the settings at the top of trade.py file to tailor the skins to your liking. Notable, you can alter the allowed guns array to specify the skins you wish to search for as well as the maximium and minimum price to include.

Alter the RECIPIENT_EMAILS array to choose who to send the emails to.


## Example Email

Subject: Potential Deal Identified: Bowie Knife | Autotronic (Field-Tested)

Beep Boop,

I identified a potential deal on csfloat. Check out the Bowie Knife | Autotronic (Field-Tested) by following this link: https://csfloat.com/item/634875524782621563

You may be able to check a target price here: https://pricempire.com/item/csgo/skin/bowie-knife-autotronic-field-tested

Best,
Jack's Bot <3


## Auction

The bot will check for new listings as well as expiring auctions. When you shut the bot off it will ask you how many hours out to check interesting auctions. You might for example check auctions expiring in the next 12 hours and place auto bids on those items.
