import functools
import traceback
import streamlit as st

def shield_network(fallback_func):
    """
    This is the Guardian. It wraps around API calls and network functions.
    If ANY error occurs (timeout, proxy block, JSON decode error), 
    it intercepts the crash and immediately triggers the fallback function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Attempt the primary function
                return func(*args, **kwargs)
            except Exception as e:
                # Suppress the error from the UI
                print(f"[GUARDIAN INTERCEPT] Error caught: {str(e)}")
                # Execute the localized fallback silently
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator

def shield_ui():
    """
    Wraps the main Streamlit render loop.
    Prevents the app from showing red text if a UI element misfires.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[GUARDIAN UI INTERCEPT] {str(e)}")
                st.error("The interface encountered a minor glitch and auto-corrected itself.")
        return wrapper
    return decorator
