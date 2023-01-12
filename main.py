import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.dash import no_update
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from math import sqrt
from typing import *

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = 'Automatyka'

def round_num(x):
    if x > 1 or x < -1:
        x = "%.2F " % x
    else:
        x = "%.2e" % x
    return x

app.layout = html.Div([
    html.H1(children=[html.Br(), html.P(children="Mathematical Model of an Automatical Regulation in a Boiler")]),
    html.P(),

    #podgrzewacz
    html.Div(id="block", children=[

    ]),

        html.Div(className='sliders', children=[ html.Br(),
            html.Div(className="temperature", children=["T [30 - 70 °C]: ", dcc.Input(className='slider', id='T', min=30, max=70, value=50, step=1, type='number'), html.Br(),]),
                html.Div(className="parameters", children=[
                    html.Div(className="data", children=[
                        "Boiler Power [3.5 - 7.0 kW]: ", dcc.Input(className='slider', id='P', min=3.5, max=7, value=5, step=0.1, type='number'), html.Br(),
                        "Boiler Volume [1 - 4 l]: ", dcc.Input(className='slider', id='V', min=1, max=4, value=2, step=0.1, type='number'), html.Br(),
                        "Incoming Water Temperature [18-20 °C]: ", dcc.Input(className='slider', id='Tw', min=18, max=20, value=20, step=0.1, type='number'), html.Br(),
                        "Water Flow Rate [1.85 - 2.15 l/min]: ", dcc.Input(className='slider', id='dw', min=1.85, max=2.15, value=2, step=0.01, type='number'), html.Br(),
                        "Maximum Boiler Voltage [220 - 240 V]: ", dcc.Input(className='slider', id='Umax', min=220, max=240, value=230, step=0.1, type='number'), html.Br(),
                        "Simulation Time [10 - 60 min]: ", dcc.Input(className='slider', id='t', min=10, max=60, value=30, step=1, type='number'), html.Br(),
                        "Sample Taking Time [0.01 - 1 s]: ", dcc.Input(className='slider', id='sample_time', min=0.01, max=1, value=0.1, step=0.01, type='number'), html.Br(),
                        "Proportional [0 - 100]: ", dcc.Input(className='slider', id='kp', min=0, max=100, value=0.0011, step=0.00001, type='number'), html.Br(),
                        "Integral [0 - 10]: ", dcc.Input(className='slider', id='Ti', min=0, max=10, value=0.6, step=0.01, type='number'), html.Br(),
                        "Derivative [0 - 10]: ", dcc.Input(className='slider', id='Td', min=0, max=10, value=0.12, step=0.01, type='number'), html.Br(),
                    ]),
                ]),
            html.Div(id='loading', children=[
                dbc.Button("Show Graph", id='submit-button-state', n_clicks=0),
                dbc.Alert("WRONG NUMBERS, YOU IDIOT!", color="danger", id="alert-auto", is_open=False, duration=10000)
            ])
        ]),

    html.Div(className="regulation_block", children=[
        html.Div(className="regulation", children=[
            "Regulation Time: ", html.Output(id="time"), html.Br(),
            "Overshoot: ", html.Output(id="overshoot"), html.Br(),
            "Constatnt error: ", html.Output(id="error"), html.Br(), #TO CHECK !!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
            "Regulation Prescision: ", html.Output(id="prescision"), html.Br(),
            "Regulation value: ", html.Output(id="value")
        ]),
    ]),

    html.Div(className="graph_display", children=[
        dcc.Loading(id='loading_icon', type='circle', children=[dcc.Graph(id='the_graph')])
    ]),

])

@app.callback(
    Output('the_graph', 'figure'),
    Output('alert-auto', 'is_open'),
    Output('time', 'children'),
    Output('overshoot', 'children'),
    Output('error', 'children'),
    Output('prescision', 'children'),
    Output('value', 'children'),
    [Input('submit-button-state', 'n_clicks')],
    [State('alert-auto', 'is_open'),
    State('T', 'value'),
    State('P', 'value'),
    State('V', 'value'),
    State('Tw', 'value'),
    State('dw', 'value'),
    State('kp', 'value'),
    State('Ti', 'value'),
    State('Td', 'value'),
    State('Umax', 'value'),
    State('t', 'value'),
    State('sample_time', 'value')])

def update_ousample_timeut(ticks, is_open, T_sesample_timeoint, pressure_sesample_timeoint, volume, incoming_water_temp, water_flow_rate, kp, ti, td, max_Voltage, simulation_time, sample_time):

    if ticks == 0:
        return no_update, is_open, no_update, no_update, no_update, no_update, no_update
    if (T_sesample_timeoint is None) or (pressure_sesample_timeoint is None) or (volume is None) or (incoming_water_temp is None) or (water_flow_rate is None) or (kp is None) or (ti is None) or (td is None) or (max_Voltage is None) or (simulation_time is None) or (sample_time is None):
        return no_update, not is_open, no_update, no_update, no_update, no_update, no_update

    water_flow = water_flow_rate/60000
    density = 1000
    heat_capacity = 4190
    U_minimum = 0
    U_maximum = max_Voltage

    Boiler_volume= volume / 1000  # [m3]  0.005<V<0.02
    resistance = U_maximum**2/(1000*pressure_sesample_timeoint)  # 0 < R < 50

    T_maksymalne = 80

    kp = kp
    Ti = ti
    Td = td

    timesim = simulation_time*60
    n = int(timesim / sample_time)
    size = n + 1

    T = [incoming_water_temp]
    U = [U_minimum]
    P = [U_minimum * U_minimum / resistance]

    # regulator PID
    e: List[float] = [0]
    u_min: float = 0
    u_max: float = 10
    u: List[float] = [0]
    u_unlimited: List[float] = [0]

    # model regulacyjny
    a = (U_maximum - U_minimum) / (u_max - u_min)
    b = U_minimum - u_min * a

    for x in range(n):
        e.append(T_sesample_timeoint - T[-1])
        u_unlimited.append((kp * (e[-1] + (sample_time / Ti) * sum(e) + (Td / sample_time) * (e[-1] - e[-2]))))
        u.append(max(u_min, min(u_max, u_unlimited[-1])))
        U.append(max(U_minimum, min(U_maximum, a * u[-1] + b)))
        P.append(U[-1] * U[-1] / resistance)
        T.append(max(incoming_water_temp, min(T_maksymalne, (sample_time / (Boiler_volume * density * heat_capacity)) * (water_flow * density * heat_capacity * (incoming_water_temp - T[-1]) + (U[-1] * U[-1] / resistance)) + T[-1])))

    for x in range(n, 1, -1):
        if (T[x] <= T_sesample_timeoint * 0.95 or T[x] >= T_sesample_timeoint * 1.05):
            czas_regulacji = x
            break

    czas_regulacji = czas_regulacji * sample_time / 60
    print("czas regulacji ", czas_regulacji)
    czas_regulacji = round_num(czas_regulacji)
    czas_regulacji = str(czas_regulacji + " min")

    przeregulowanie = (max(T) - T_sesample_timeoint) / T_sesample_timeoint * 100
    print("przeregulowanie", przeregulowanie, "%")
    przeregulowanie = round_num(przeregulowanie)
    przeregulowanie = str(przeregulowanie + " %")

    uchyb_ustalony = e[-1]
    print("Uchyb ustalony", uchyb_ustalony)
    uchyb_ustalony = round_num(uchyb_ustalony)

    dokladnosc_regulacji = sample_time * sum(map(abs, e))
    print("Wskaznik dokladnosci regulacji", dokladnosc_regulacji)
    dokladnosc_regulacji = round_num(dokladnosc_regulacji)

    koszty_regulacji = sample_time * sum(map(abs, u))
    print("Wskaznik kosztów regulacji", koszty_regulacji)
    koszty_regulacji = round_num(koszty_regulacji)

    # skalowanie
    n = [float(x * sample_time / 60) for x in range(size)]
    Tmax_list = [float(T_sesample_timeoint) for _ in range(size)]
    U_koncowe = sqrt(
        (T_sesample_timeoint - incoming_water_temp) * (water_flow * density * heat_capacity * resistance))
    Umax_list = [float(U_koncowe) for _ in range(size)]

    plot = make_subplots(rows=4, cols=1, subplot_titles=(
        "Zależność temperatury od czasu - T(t)", "Zależność sygnału sterującego (wielkości sterującej) od czasu - u(t)",
        "Zależność napięcia na grzałce (wielkości sterowanej) od czasu - U(t)", "Zależność mocy grzałki od czasu - P(t)"))

    plot.add_trace(go.Scatter(x=n, y=T, name="T"), row=1, col=1)
    plot.add_trace(go.Scatter(x=n, y=Tmax_list, name="T max", line=dict(dash='dash')), row=1, col=1)
    plot.update_xaxes(title_text="t [min]", row=1, col=1)
    plot.update_yaxes(title_text="T [°C]", range=[0, 85], row=1, col=1)

    plot.add_trace(go.Scatter(x=n, y=u, name="u"), row=2, col=1)
    plot.update_xaxes(title_text="t [min]", row=2, col=1)
    plot.update_yaxes(title_text="u [V]", range=[0, 12], row=2, col=1)

    plot.add_trace(go.Scatter(x=n, y=U, name="U"), row=3, col=1)
    plot.add_trace(go.Scatter(x=n, y=Umax_list, name="Umax"), row=3, col=1)
    plot.update_xaxes(title_text="t [min]", row=3, col=1)
    plot.update_yaxes(title_text="U [V]", range=[0, 250], row=3, col=1)

    plot.add_trace(go.Scatter(x=n, y=P, name="P"), row=4, col=1)
    plot.update_xaxes(title_text="t [min]", row=4, col=1)
    plot.update_yaxes(title_text="P [W]", range=[0, 7500], row=4, col=1)

    return plot, is_open, czas_regulacji, przeregulowanie, uchyb_ustalony, dokladnosc_regulacji, koszty_regulacji

if __name__ == '__main__':
    app.run_server(debug=True)