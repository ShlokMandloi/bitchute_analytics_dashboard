from dash import Output, Input, State
import plotly.graph_objects as go
import json

def make_standard_page_callback_params(graph_id, params_section_id, message_section_id):
    message_callback_output = Output(message_section_id, "children")
    params_json_callback_input = Input(params_section_id, "children")
    outputs = [Output(graph_id, "figure"), message_callback_output]
    inputs = [params_json_callback_input]
    states = [State(graph_id, "relayoutData"), State(graph_id, "figure")]
    return outputs, inputs, states

def register_callbacks(app):
    outputs, inputs, states = make_standard_page_callback_params('example-graph', 'params-section', 'message-section')

    @app.callback(
        outputs,
        inputs,
        states
    )
    def update_graph(params_json, relayout_data, figure):
        try:
            # Process params and update the graph
            params = json.loads(params_json)
            fig = go.Figure(data=figure['data'])
            # Apply any updates to the figure based on params and relayout_data
            # This is a placeholder for whatever logic you want to add
            message = "Graph updated successfully!"
        except Exception as e:
            fig = go.Figure()
            message = f"Error updating graph: {e}"
        return fig, message
