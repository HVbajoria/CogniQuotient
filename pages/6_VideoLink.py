import requests
import streamlit as st

# Azure Bing Search API endpoint and key
BING_API_ENDPOINT = 'https://api.bing.microsoft.com/'+"/v7.0/search"
BING_API_KEY = os.environ['BING_API_KEY'] # Replace this with your actual Bing API key

st.set_page_config( 
     page_title="CogniQuotient", 
     page_icon="🏫",
     initial_sidebar_state="expanded", 
 ) 


if 'username' not in st.session_state:
    st.session_state["username"]="User"
# Custom CSS style for the app
st.markdown(
    """
    <style>
    .container {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        padding: 2rem;
    }
    .title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
    }
    .subheader {
        font-size: 1.2rem;
        margin-bottom: 1rem;
        font-weight: bold;
        margin-top: 3rem;
    }
    .video-description {
        margin-bottom: 1rem;
    }
    video {
        width: 80%;
        max-width: 800px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit app
def main():

    def gradient_text(text, color1, color2):
        gradient_css = f"""
        background: -webkit-linear-gradient(left, {color1}, {color2});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 42px;
        """
        return f'<span style="{gradient_css}">{text}</span>'
    
    def gradient(text, color1, color2):
        gradient_css = f"""
        background: -webkit-linear-gradient(left, {color2}, {color1});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 22px;
        font-style: italic;
        """
        return f'<span style="{gradient_css}">{text}</span>'


    color1 = "#0d3270"
    color2 = "#0fab7b"
    text = "VideoLink"

    styled_text = gradient_text(text, color1, color2)
    st.write(f"<div style='text-align: center;'>{styled_text}</div>", unsafe_allow_html=True)
    styled_text = gradient("Prompt to Find Best Videos", color1, color2)
    st.write(f"<div style='text-align: center;'>{styled_text}</div>", unsafe_allow_html=True)
    st.subheader("Weclome "+st.session_state["username"]+" 👋")

    # Get the user's topic input
    user_input = st.text_input('Enter a topic:', key="topic_input")

    # Get the number of results the user wants
    num_results = st.number_input('Number of Results', min_value=1, max_value=10, value=5, step=1)

    if user_input:
        search_results = bing_search(user_input, num_results)
        display_results(search_results, num_results)


# Function to query Azure Bing Search API
def bing_search(query, num):
    headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
    num =int(num)
    params = {
        'q': query,
        'count': num,  # Number of search results to retrieve
        'responseFilter': 'Videos',  # Filter results to videos only
        'mkt': 'en-US'
    }
    response = requests.get(BING_API_ENDPOINT, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('videos', {}).get('value', [])
    else:
        st.error(f"Error occurred during the search. Status Code: {response.status_code}")
        st.error(response.json())
        return []


# Function to display search results
def display_results(results, num):
    if not results:
        st.warning('No results found.')
    else:
        c=0
        for result in results:
            if c == num:
                break
            c+=1
            st.write(f"<div class='subheader'>{result['name']}</div>", unsafe_allow_html=True)
            description = result.get('description', 'Description not available.')
            st.write(f"<div class='video-description'>{description}</div>", unsafe_allow_html=True)
            st.video(result['contentUrl'])


if __name__ == '__main__':
    main()
footer="""<style>

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤️ by <a style='display: inline; text-align: center;' href="https://www.linkedin.com/in/harshavardhan-bajoria/" target="_blank">Harshavardhan Bajoria</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)
