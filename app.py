import pandas as pd
import re
from collections import Counter
from wordcloud import WordCloud
import plotly
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import base64
from io import BytesIO
import os
import pkg_resources
import gunicorn

print("pandas version:", pd.__version__)
print("wordcloud version:", pkg_resources.get_distribution("Wordcloud").version)
print("plotly version:", plotly.__version__)
print("dash version:", dash.__version__)

stop_words = set([
    'is', 'the', 'and', 'for', 'or', 'of', 'to', 'in', 'a', 'an', 'that', 'it', 'on', 'with', 'as', 'this', 'by', 'from', 'at', 'but', 'not',
    'no', 'hashtags', '2024','5','w', 'too','vs','you','its','car','are','just','what','why','about','were','they'
])

def preprocess_data(df):
    print("Preprocessing data")
    # Check if the necessary columns are present
    required_columns = ['view_count', 'like_count', 'dislike_count', 'title', 'hashtags', 'channel', 'video_url', 'subscriber_count', 'description', 'duration']
    for column in required_columns:
        if column not in df.columns:
            print(f"Error: Column '{column}' not found in DataFrame")
            return None
    
    df['view_count'] = df['view_count'].fillna(0).astype(int)
    df['like_count'] = df['like_count'].fillna(0).astype(int)
    df['dislike_count'] = df['dislike_count'].fillna(0).astype(int)
    df['subscriber_count'] = df['subscriber_count'].fillna(0).astype(int)
    
    # Convert duration to total minutes
    def convert_duration(duration):
        try:
            minutes, seconds = map(int, duration.split(':'))
            return minutes + seconds / 60
        except:
            return 0  # Handle cases where the duration is not in the expected format

    df['duration'] = df['duration'].fillna('0:00').apply(convert_duration)
    
    # Aggregate by video title, summing views and averaging duration
    agg_df = df.groupby('title').agg({
        'view_count': 'sum',
        'like_count': 'sum',
        'dislike_count': 'sum',
        'duration': 'mean',
        'hashtags': 'first',
        'channel': 'first',
        'video_url': 'first',
        'subscriber_count': 'first',
        'description': 'first'
    }).reset_index()
    
    agg_df['Total Interactions'] = agg_df['view_count'] + agg_df['like_count'] + agg_df['dislike_count']
    # Add 'Net Likes' column
    agg_df['Net Likes'] = agg_df['like_count'] - agg_df['dislike_count']
    # Drop duplicate entries for users based on the highest subscriber count
    agg_df = agg_df.sort_values(by='subscriber_count', ascending=False).drop_duplicates(subset='channel', keep='first')
    
    # Categorize duration into 3-minute intervals
    bins = range(0, int(agg_df['duration'].max()) + 3, 3)
    labels = [f'{i}-{i+3}' for i in bins[:-1]]
    agg_df['duration_category'] = pd.cut(agg_df['duration'], bins=bins, labels=labels, right=False, ordered=True)
    
    # Aggregate the view counts by duration intervals
    duration_view_counts = agg_df.groupby('duration_category')['view_count'].sum().reset_index()
    
    return agg_df, duration_view_counts




data_directory = os.path.join(os.path.dirname(__file__), 'data')

# Read the preprocessed CSV files from the data directory
categories = {
    'sports': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_sports.csv'))),
    'health': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_health.csv'))),
    'entertainment': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_entertainment.csv'))),
    'education': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_education.csv'))),
    'automotive': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_automotive.csv'))),
    'business': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_business.csv'))),
    'news': preprocess_data(pd.read_csv(os.path.join(data_directory, 'dash_csv_news.csv')))
}

categories = {k: v for k, v in categories.items() if v is not None}

def calculate_word_frequencies(titles):
    all_titles = ' '.join(titles.dropna().tolist())
    all_titles = re.sub(r'[^\w\s]', '', all_titles).lower()
    words = all_titles.split()
    words = [word for word in words if word not in stop_words]
    word_freq = Counter(words)
    return word_freq

def generate_wordcloud_image(word_freq, most_common_word):
    def color_func(word, *args, **kwargs):
        return 'red' if word == most_common_word else 'white'

    wordcloud = WordCloud(
        width=1600,  
        height=800,  
        background_color='rgba(0,0,0,0)',  
        mode='RGBA',  
        color_func=color_func
    ).generate_from_frequencies(word_freq)
    
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def get_logo_base64(logo_path):
    with open(logo_path, 'rb') as f:
        logo_img = f.read()
    return base64.b64encode(logo_img).decode()

script_dir = os.path.dirname(__file__)
print(script_dir)
logo_path = os.path.join(script_dir, 'pngwing.com.png')
logo_base64 = get_logo_base64(logo_path)

app = Dash(__name__, external_stylesheets=[
    'https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;700&display=swap',
    'https://fonts.googleapis.com/css2?family=Anton&display=swap',
    '/assets/custom.css',
    '/assets/styles.css'
])

server = app.server

app.layout = html.Div(style={'backgroundColor': '#121212', 'color': 'white', 'padding': '20px', 'max-width': '100vw', 'overflow-x': 'hidden'}, children=[
    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '100%'}, children=[
        html.Img(src=f'data:image/png;base64,{logo_base64}', style={'height': '150px', 'marginRight': '20px'}),
        html.H1([
            "ANALYTICS ",
            html.Span("DASHBOARD", className='dashboard-red')
        ], className='anton-font', style={'fontSize': '48px', 'textAlign': 'center'})
    ]),
    html.Div([
        html.Div([
            dcc.Input(
                id='search-input',
                type='text',
                placeholder='Enter a keyword for relevant post search...',
                className='black-searchbox roboto-light',
                style={'width': '300px', 'color': '#ffffff', 'marginRight': '10px'}
            ),
            html.Button('Search', id='search-button', n_clicks=0, className='black-searchbox roboto-light', style={'color': '#ffffff'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px', 'flex': '1'}),
        html.Div([
            html.Label("Category of Media", className='roboto-light', style={'marginRight': '5px'}),
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label': cat.capitalize(), 'value': cat} for cat in categories.keys()],
                value='entertainment',
                clearable=False,
                className='black-dropdown roboto-light',
                style={'width': '180px', 'color': '#ffffff'}
            ),
            html.Label("Select Analysis Type", className='roboto-light', style={'marginLeft': '15px', 'marginRight': '5px'}),
            dcc.Dropdown(
                id='sort-dropdown',
                options=[
                    {'label': 'Engagement Metrics', 'value': 'Engagement Metrics'},
                    {'label': 'Trends', 'value': 'Trends'}
                ],
                value='Engagement Metrics',
                clearable=False,
                className='black-dropdown roboto-light',
                style={'width': '180px', 'color': '#ffffff'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'flex-end', 'marginBottom': '20px', 'flex': '1'})
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'width': '100%', 'max-width': '100%'}),
    html.Div(id='search-results', style={'marginTop': '20px', 'width': '100%', 'color': 'white'}),
    html.Div(id='graphs-container', className='roboto-light', children=[
        html.Div([
            dcc.Graph(id='bar-chart', style={'display': 'none', 'width': '75%', 'max-width': '100vw'}),
            dcc.Graph(id='subscriber-chart', style={'display': 'none', 'width': '75%', 'max-width': '100vw'}),
        ], className='graph-container', style={'width': '100%'}),
        html.Div([
            dcc.Graph(id='dot-like-chart', style={'display': 'none', 'width': '75%', 'max-width': '100vw'}),
            dcc.Graph(id='dot-dislike-chart', style={'display': 'none', 'width': '75%', 'max-width': '100vw'}),
        ], className='graph-container', style={'width': '100%'}),
        html.Div([
            html.Div(id='wordcloud-container', style={'display': 'none', 'margin': 'auto', 'width': '100%', 'height': '100px', 'max-width': '100vw'}),
            dcc.Graph(id='line-graph', style={'display': 'none', 'width': '75%', 'max-width': '100vw', 'height': '500px'})
        ], className='graph-container', style={'width': '100%'}),
    ], style={'width': '100%', 'padding': '10px', 'boxSizing': 'border-box', 'overflow': 'hidden'}),
    html.Div(id='additional-graphs', style={'marginTop': '20px', 'width': '100%'}, className='roboto-light')
])

@app.callback(
    [Output('bar-chart', 'figure'),
     Output('subscriber-chart', 'figure'),
     Output('dot-like-chart', 'figure'),
     Output('dot-dislike-chart', 'figure'),
     Output('wordcloud-container', 'children'),
     Output('bar-chart', 'style'),
     Output('subscriber-chart', 'style'),
     Output('dot-like-chart', 'style'),
     Output('dot-dislike-chart', 'style'),
     Output('wordcloud-container', 'style'),
     Output('additional-graphs', 'children'),
     Output('line-graph', 'figure'),
     Output('line-graph', 'style'),
     Output('search-results', 'children')],
    [Input('category-dropdown', 'value'), 
     Input('sort-dropdown', 'value'), 
     Input('search-button', 'n_clicks')],
    [State('search-input', 'value')]
)
def update_visualizations(selected_category, sort_by, n_clicks, search_value):
    print(f"Selected category: {selected_category}, sort by: {sort_by}")
    data, duration_view_counts = categories[selected_category]
    print(data.head())

    wordcloud_container = ''
    wordcloud_container_style = {'display': 'none'}
    fig = go.Figure()
    subscriber_fig = go.Figure()
    dot_like_fig = go.Figure()
    dot_dislike_fig = go.Figure()
    line_fig = go.Figure()
    additional_graphs_content = []
    bar_chart_style = {'display': 'none'}
    subscriber_chart_style = {'display': 'none'}
    dot_like_chart_style = {'display': 'none'}
    dot_dislike_chart_style = {'display': 'none'}
    wordcloud_container_style = {'display': 'none'}
    line_graph_style = {'display': 'none'}
    search_results_content = []

    if sort_by == 'Trends':
        if not data.empty:
            # Ensure correct order of categories
            categories_order = ['0-3', '3-6', '6-9', '9-12', '12-15', '15-18', '18-21', '21-24', '24-27', '27-30', '30-33', '33-36', '36-39']
            duration_view_counts['duration_category'] = pd.Categorical(duration_view_counts['duration_category'], categories=categories_order, ordered=True)
            duration_view_counts = duration_view_counts.dropna(subset=['duration_category'])
            
            # Create area chart for total view count by video duration intervals
            area_fig = px.area(duration_view_counts, x='duration_category', y='view_count', category_orders={'duration_category': categories_order})
            area_fig.update_traces(line=dict(color='grey'))
            area_fig.update_layout(
                xaxis=dict(title='Video Duration (minutes)', showgrid=False),
                yaxis=dict(title='View Count', showgrid=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                title=dict(
                    text='View Count vs. Video Duration',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                )
            )
            additional_graphs_content = [dcc.Graph(figure=area_fig)]

            # Word count
            word_freq = calculate_word_frequencies(data['title'])
            most_common_word = word_freq.most_common(1)[0][0]

            # Generate word cloud image
            wordcloud_src = f'data:image/png;base64,{generate_wordcloud_image(word_freq, most_common_word)}'
            wordcloud_container = html.Div(children=[
                html.Img(src=wordcloud_src, style={'display': 'block', 'max-width': '100%', 'height': 'auto', 'margin': '0 auto'})
            ], style={'display': 'block', 'text-align': 'center', 'margin': '0 auto'})
            wordcloud_container_style = {'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin': '20px auto', 'width': '0%', 'height': '400px'}

    else:
        if not data.empty:
            fig = px.bar(data.sort_values(by='Total Interactions', ascending=False).head(10),
                         x='Total Interactions', y='channel', orientation='h', title='Top 10 Users by Total Interactions', template="plotly_dark",
                         color_discrete_sequence=['red'])
            subscriber_fig = px.bar(data.sort_values(by='subscriber_count', ascending=False).head(10),
                                    x='subscriber_count', y='channel', orientation='h', title='Top 10 Users by Subscriber Count', template="plotly_dark",
                                    color_discrete_sequence=['blue'])
            dot_like_fig = px.scatter(data.sort_values(by='like_count', ascending=False).head(10), x='like_count', y='channel', size='like_count', title='Top 10 Users by Like Counts', 
                                      template="plotly_dark", color_discrete_sequence=['red'], size_max=20)
            dot_dislike_fig = px.scatter(data.sort_values(by='dislike_count', ascending=False).head(10),
                                         x='dislike_count', y='channel', size='dislike_count', title='Top 10 Users by Dislike Counts', 
                                         template="plotly_dark", color_discrete_sequence=['red'], size_max=20)
            fig.update_traces(marker=dict(color='red'), width=0.6) 
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, title=''),
                yaxis=dict(showgrid=False, zeroline=False, title=''),
                title=dict(
                    text='Top 10 Channels by Total Interactions',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                ),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.7)",  # Black background with 70% opacity
                    font_size=16,
                    font_family="Rockwell",
                    font_color="white"  # White font color
                )
            )
            subscriber_fig.update_traces(marker=dict(color='red'), width=0.6)
            subscriber_fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, title=''),
                yaxis=dict(showgrid=False, zeroline=False, title=''),
                title=dict(
                    text='Top 10 Channels by Subscriber Count',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                ),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.7)",  # Black background with 70% opacity
                    font_size=16,
                    font_family="Rockwell",
                    font_color="white"  # White font color
                )
            )
            dot_like_fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, title=''),
                yaxis=dict(showgrid=False, zeroline=False, title=''),
                title=dict(
                    text='Top 10 Users by Like Counts',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                ),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.7)",  # Black background with 70% opacity
                    font_size=16,
                    font_family="Rockwell",
                    font_color="white"  # White font color
                )
            )
            dot_dislike_fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, title=''),
                yaxis=dict(showgrid=False, zeroline=False, title=''),
                title=dict(
                    text='Top 10 Users by Dislike Counts',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                ),
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.7)",  # Black background with 70% opacity
                    font_size=16,
                    font_family="Rockwell",
                    font_color="white"  # White font color
                )
            )
            bar_chart_style = {'width': '75%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-bottom': '20px', 'boxSizing': 'border-box', 'padding': '10px'}
            subscriber_chart_style = {'width': '75%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-bottom': '20px', 'boxSizing': 'border-box', 'padding': '10px'}
            dot_like_chart_style = {'width': '75%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-bottom': '20px', 'boxSizing': 'border-box', 'padding': '10px'}
            dot_dislike_chart_style = {'width': '75%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-bottom': '20px', 'boxSizing': 'border-box', 'padding': '10px'}
            liked_users = data.groupby('channel')['Net Likes'].sum().reset_index()
            liked_users = liked_users.sort_values(by='Net Likes', ascending=False)
            line_fig = px.line(liked_users, x='channel', y='Net Likes', title='Channel Popularity by Net Like', template="plotly_dark")
            line_fig.update_layout(
                yaxis=dict(
                    title=dict(
                        text='Net Like Count',
                        font=dict(family='Anton', size=18),
                    ),
                    showgrid=False,  
                    zeroline=False 
                ),
                xaxis=dict(
                    title=dict(
                        text='Channel',
                        font=dict(family='Anton', size=18),
                    ),
                    showgrid=False,  
                    zeroline=False  
                ),
                title=dict(
                    text='Channel Popularity by Net Like',
                    font=dict(family='Anton', size=24),
                    x=0.5,
                    xanchor='center'
                ),
                plot_bgcolor='rgba(0,0,0,0)',  
                paper_bgcolor='rgba(0,0,0,0)',
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.7)",  # Black background with 70% opacity
                    font_size=16,
                    font_family="Rockwell",
                    font_color="white"  # White font color
                )
            )
            line_graph_style = {'display': 'block', 'margin-top': '20px', 'width': '95%', 'height': '500px'}
            
    if search_value:
        search_results = data[data['title'].str.contains(search_value, case=False, na=False) | data['description'].str.contains(search_value, case=False, na=False)]
        if not search_results.empty:
            search_results_content = html.Div([
                html.H4("Relevant Posts:", style={'fontFamily': 'Roboto', 'textAlign': 'center'}),
                html.Ul([html.Li([
                    html.P(f"Title: {row['title']}"),
                    html.P(f"Channel: {row['channel']}"),
                    html.A("Watch Video", href=row['video_url'], target="_blank")
                ]) for index, row in search_results.iterrows()])
            ], style={'marginTop': '20px'})
        else:
            search_results_content = html.Div([
                html.H4("Search Results", style={'fontFamily': 'Anton', 'textAlign': 'center'}),
                html.P("No Video Found", style={'textAlign': 'center'})
            ], style={'marginTop': '20px'})
    else:
        search_results_content = html.Div()

    return fig, subscriber_fig, dot_like_fig, dot_dislike_fig, wordcloud_container, bar_chart_style, subscriber_chart_style, dot_like_chart_style, dot_dislike_chart_style, wordcloud_container_style, additional_graphs_content, line_fig, line_graph_style, search_results_content

if __name__ == '__main__':
    app.run_server(debug=True)
