"""
blocklist.py

This file contains the blocklist for JWT tokens.it will be imported in app and the logout
resource so that the tokens can be added to the blocklist when a 
user logs out.
"""

BLOCKLIST = set()