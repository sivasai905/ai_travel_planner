import streamlit as st
import requests
from datetime import datetime, timedelta
import time # Needed for the exponential backoff retry

# Configuration
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
MAX_RETRIES = 5

st.set_page_config(layout="centered")
st.title("🎓 AI Student Travel Planner")
st.markdown("---")

# Load Gemini API key
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key:
    st.error("🚨 Gemini API key not found in `secrets.toml`. Please configure your key to run the app.")
    st.stop()

# --- User Inputs (Sidebar) ---
with st.sidebar:
    st.header("Plan Your Trip")
    destination = st.text_input("Destination (City, Country)", "Hyderabad, India")
    days = st.number_input("Number of Days", min_value=1, max_value=14, value=3)
    
    # Calculate default end date based on days
    default_end_date = datetime.today() + timedelta(days=days - 1)
    
    start_date = st.date_input("Start Date", datetime.today())
    end_date = st.date_input("End Date", default_end_date)
    
    # Update days if the date range is manually adjusted
    if (end_date - start_date).days + 1 != days:
        days = (end_date - start_date).days + 1
        st.info(f"Days updated to **{days}** based on your dates.")

    interests = st.multiselect(
        "Interests",
        ["Culture", "Shopping", "History", "Adventure", "Food", "Nature", "Art", "Sports"],
        default=["Culture", "History"]
    )
    budget = st.number_input("Budget (USD)", min_value=50, step=10, value=200)


# --- Generate Itinerary Function (FIXED and Robust) ---
def generate_itinerary_gemini(destination, days, interests, budget, start_date, end_date, api_key):
    """
    Calls the Google AI Gemini API with exponential backoff retry logic.
    """
    
    # The API key is added as a query parameter for authentication
    url = f"{API_URL}?key={api_key}"
    
    # --- PROMPT REVISION: Explicitly create day structures ---
    itinerary_structure = ""
    for i in range(1, days + 1):
        itinerary_structure += f"""
### Day {i}
-   **Morning:** [Fill in low-cost/free activity]
-   **Afternoon:** [Fill in cultural/interest activity]
-   **Evening:** [Fill in cheap food market/local hangout]
-   **Transport Tip:** [Fill in public transport advice]
-   **Estimated Daily Cost:** [Fill in rough daily budget]
"""
    
    prompt = f"""
You are an expert travel planner creating a detailed, budget-friendly itinerary for students.

Destination: {destination}
Days: {days}
Interests: {', '.join(interests)}
Budget: ${budget} (Total estimated cost)
Travel Dates: {start_date} to {end_date}

Generate the **{days}-day itinerary** below, strictly filling in the content for each of the pre-defined Day sections.

{itinerary_structure}

Conclude the itinerary with a final section titled '💰 Money-Saving Pro Tips' listing 3 actionable, specific budget tips for this destination. Format the entire response using Markdown for clear readability.
"""

    headers = {
        "Content-Type": "application/json"
    }
    
    # Corrected Payload Structure: using 'generationConfig' (not 'config')
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": { 
            "temperature": 0.7,
            "maxOutputTokens": 3000 
        }
    }
    
    # Implement Exponential Backoff Retry Logic
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            # Check for success (200) or permanent client errors (4xx other than 429)
            if response.status_code == 200:
                data = response.json()
                # Correct Response Parsing for generateContent
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return "Error: Could not parse a valid response text from the API."
            
            # Check for status codes that suggest retrying (e.g., 429 Rate Limit, 5xx Server Error)
            elif response.status_code in [429, 500, 503]:
                # Prepare for retry
                wait_time = 2 ** attempt
                if attempt < MAX_RETRIES - 1:
                    st.warning(f"Rate limit or server error ({response.status_code}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                continue
            
            else:
                # Handle permanent errors (e.g., 400 Bad Request, 401 Unauthorized)
                return f"🚨 API Error: Status Code {response.status_code}\n\n**Response Details:**\n{response.text}"

        except requests.exceptions.RequestException as e:
            # Handle connection errors
            wait_time = 2 ** attempt
            if attempt < MAX_RETRIES - 1:
                st.warning(f"Connection error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            continue

    # If all retries fail
    return f"🚨 API Error: Failed to connect after {MAX_RETRIES} attempts."

# --- Button & Output ---
st.markdown("---")
if st.button("🚀 Generate Itinerary", type="primary"):
    if days <= 0:
        st.error("Please enter a valid number of days.")
    else:
        with st.spinner(f"Contacting Gemini AI to plan your {days}-day trip to {destination}..."):
            result = generate_itinerary_gemini(
                destination, 
                days, 
                interests, 
                budget, 
                start_date, 
                end_date, 
                gemini_key
            )
        
        st.subheader(f"🗺️ Your {days}-Day Student Trip to {destination}")
        st.markdown(result)

st.markdown("---")
st.caption("Powered by Google Gemini 2.5 Flash")
