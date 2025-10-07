import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Student Travel Planner",
    page_icon="✈️",
    layout="centered",
)

# --- Gemini API Configuration ---
try:
    # Get the API key from Streamlit secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash') # Or 'gemini-pro'
except Exception as e:
    st.error(f"Error configuring the Gemini API: {e}")
    st.error("Please make sure your GOOGLE_API_KEY is set correctly in Streamlit's secrets.")
    st.stop()


def generate_itinerary_with_gemini(destination, budget, start_date, end_date, interests):
    """
    Generates a travel itinerary by calling the Gemini API.
    """
    # Calculate duration
    duration = (end_date - start_date).days + 1
    
    # --- Construct the prompt for the AI model ---
    prompt = f"""
    You are an expert travel planner specializing in creating budget-friendly itineraries for students.
    
    Generate a detailed, day-by-day travel itinerary based on the following details:
    
    - **Destination:** {destination}
    - **Total Budget:** ${budget} USD
    - **Travel Dates:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')} ({duration} days)
    - **Primary Interests:** {', '.join(interests)}
    
    Please follow these instructions:
    1.  **Structure:** Create a plan for each day.
    2.  **Budget Focus:** The itinerary must be realistic for the given budget. Prioritize free activities (parks, walking tours, free museum days), student discounts, and affordable local experiences.
    3.  **Content:** For each day, suggest activities for the morning, afternoon, and evening. Include a mix of activities based on the user's interests.
    4.  **Food & Transport:** Suggest cheap local food options (street food, local markets) and cost-effective transportation (public transit, walking).
    5.  **Formatting:** Use Markdown for clear formatting. Use headings for each day (e.g., "### Day 1: Arrival and Exploration"). Use bolding for key places.
    6.  **Tone:** Make the tone engaging, fun, and encouraging for a student traveler.
    7.  **Tips:** End with a "💡 Pro Tips for Students" section with 2-3 extra money-saving tips relevant to the destination.
    
    Generate the itinerary now.
    """
    
    try:
        # Call the Gemini API
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while generating the itinerary: {e}"


# --- Streamlit App Interface ---

st.title("🎓 AI Travel Planner for Students")
st.markdown("Get a personalized, budget-friendly travel itinerary powered by Google Gemini! 🤖")


st.markdown("### Tell us about your trip:")

# --- User Inputs ---
destination = st.text_input("📍 Where do you want to go?", placeholder="e.g., Paris, Tokyo, Rome")

col1, col2 = st.columns(2)
with col1:
    budget = st.number_input("💰 What's your total budget (in USD)?", min_value=100, step=50, value=500)
with col2:
    # Use a date range selector
    date_range = st.date_input(
        "🗓️ Select your travel dates",
        (datetime.today(), datetime.today() + timedelta(days=7)),
        min_value=datetime.today()
    )

# Unpack dates, handle case where user selects only one day
start_date = date_range[0]
end_date = date_range[1] if len(date_range) > 1 else start_date

interests = st.multiselect(
    "🎯 What are your interests?",
    ["History", "Food", "Hiking", "Nightlife", "Art & Culture", "Nature", "Shopping","beaches"],
    default=["History", "Food"]
)

# --- Generate Button and Output ---
if st.button("✨ Generate Itinerary", type="primary"):
    # --- Input Validation ---
    if not destination or not interests or not date_range:
        st.error("Please fill in all the fields to generate your itinerary.")
    elif start_date > end_date:
        st.error("Your travel start date must be before the end date.")
    else:
        # --- Show a spinner and generate the output ---
        with st.spinner("🤖 Contacting the AI travel expert... Please wait."):
            generated_itinerary = generate_itinerary_with_gemini(destination, budget, start_date, end_date, interests)
        
        st.success("Your personalized itinerary is ready!")
        st.markdown(generated_itinerary)