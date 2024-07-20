from dash import html, dcc

def create_layout():
    return html.Div([
        html.Div(id='params-section', children='{"param1": "value1"}'),
        html.Div(id='message-section'),
        dcc.Graph(id='example-graph', figure={
            'data': [{'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Sample Data'}],
            'layout': {'title': 'Initial Graph'}
        })
    ])
