import pickle
import spotipy
import streamlit as st
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = "70a9fb89662f4dac8d07321b259eaad7"
CLIENT_SECRET = "4d6710460d764fbbb8d8753dc094d131"

# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager,
    requests_timeout=10,
    retries=3
)


import time

@st.cache_data(show_spinner=False, ttl=86400)
def get_song_details(song_name, artist_name):
    # Small delay to avoid bursting the Spotify API
    time.sleep(0.3)
    
    search_query = f"track:{song_name} artist:{artist_name}"
    
    details = {
        "name": song_name,
        "artist": artist_name,
        "album_cover_url": "https://i.postimg.cc/1RVn5H0r/social.png",
        "spotify_url": "#",
        "track_id": None
    }

    try:
        # First try strict search
        results = sp.search(q=search_query, type="track", limit=1)
        
        # If strict search fails, try a relaxed broad search
        if not results or not results["tracks"]["items"]:
            relaxed_query = f"{song_name} {artist_name}"
            results = sp.search(q=relaxed_query, type="track", limit=1)
            
    except Exception as e:
        print(f"Spotify API Error: {e}")
        results = None

    if results and results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        if track["album"]["images"]:
            details["album_cover_url"] = track["album"]["images"][0]["url"]
        if "spotify" in track["external_urls"]:
            details["spotify_url"] = track["external_urls"]["spotify"]
        # Update artist with exact Spotify artist name for better formatting
        details["artist"] = track["artists"][0]["name"]
        details["track_id"] = track["id"]
        
    return details


def recommend(song):
    index = music[music['song'] == song].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_songs = []
    
    for i in distances[1:6]:
        artist = music.iloc[i[0]].artist
        song_name = music.iloc[i[0]].song
        details = get_song_details(song_name, artist)
        recommended_songs.append(details)

    return recommended_songs


st.set_page_config(layout="wide", page_title="Music Recommender", page_icon="🎵")
st.title('🎵 Music Recommender System')

music = pickle.load(open('../df.pkl', 'rb'))
similarity = pickle.load(open('../similarity.pkl', 'rb'))

music_list = music['song'].values
selected_song = st.selectbox(
    "Type or select a song from the dropdown",
    music_list
)

if st.button('Show Recommendation'):
    with st.spinner("Fetching recommendations..."):
        # Fetch details for the selected song
        selected_song_artist = music[music['song'] == selected_song]['artist'].values[0]
        selected_details = get_song_details(selected_song, selected_song_artist)
        
        recommended_songs = recommend(selected_song)

        # Display the selected song
        st.subheader(f"Playing: {selected_song}")
        if selected_details.get("track_id"):
            iframe = f'<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/{selected_details["track_id"]}?utm_source=generator" width="100%" height="152" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'
            st.markdown(iframe, unsafe_allow_html=True)
        else:
            st.warning("Could not find a playable Spotify track for the selected song.")

        st.markdown("---")
        st.subheader("Recommended Songs")
            
        cols = st.columns(5)
        for i, col in enumerate(cols):
            song = recommended_songs[i]
            with col:
                if song.get("track_id"):
                    # Render the large Spotify iframe widget
                    iframe = f'<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/{song["track_id"]}?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'
                    st.markdown(iframe, unsafe_allow_html=True)
                else:
                    # Custom HTML fallback for Spotify-like card if track_id is missing
                    card_html = f"""
                    <div style="background-color: #181818; padding: 15px; border-radius: 8px; text-align: left; color: white;">
                        <img src="{song['album_cover_url']}" style="width: 100%; border-radius: 4px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: white;" title="{song['name']}">{song['name']}</div>
                        <div style="font-size: 14px; color: #b3b3b3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 10px;" title="{song['artist']}">{song['artist']}</div>
                        <div style="font-size: 12px; color: #ff4b4b;">Preview unavailable</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
