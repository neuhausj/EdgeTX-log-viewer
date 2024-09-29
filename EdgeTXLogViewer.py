#!/usr/bin/env python

"""EdgeTXLogViewer.py: Upload your EdgeTX logs and display a summary of all flights and a curve if a flight is selected"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import time
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode


def getFlightTime(duration):
    flightTime = duration.total_seconds()
    if flightTime < 60:
        flightTime = time.strftime("%-Ss", time.gmtime(flightTime))
    elif flightTime < 3600:
        flightTime = time.strftime("%-Mm%Ss", time.gmtime(flightTime))
    else:
        flightTime = time.strftime("%-Hh%Mm%Ss", time.gmtime(flightTime))
    return flightTime

def aggrid_interactive_table(df: pd.DataFrame):
    options = GridOptionsBuilder.from_dataframe(df)

    options.configure_side_bar()
    options.configure_selection("single")
    options.configure_column("Filename", width=200)
    options.configure_column("Flight time", width=60)
    options.configure_column("Launch height (m)", width=100)
    options.configure_column("Max altitude (m)", width=90)
    options.configure_column("Min RSSI1 (dB)", width=75)
    options.configure_column("Min RSSI2 (dB)", width=75)
    options.configure_column("Min RQly (%)", width=70)
    options.configure_column("Max TPWR (mW)", width=90)

    selection = AgGrid(
        df,
        width="100%",
        gridOptions=options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        height=min(34 + len(df) * 28, 400)
    )

    return selection

def displayFlightGraph(df, conf):
    # Create duration field
    position = df.columns.get_loc('datetime')
    df['duration'] = df.iloc[1:, position] - df.iat[0, position]+ pd.to_datetime('1970/01/01')
    
    # Create stats
    #st.write(df.agg({"Alt(m)":['max'], "1RSS(dB)":['min'], "2RSS(dB)":['min'], "RQly(%)":['min'], "TPWR(mW)":['max'], "1RSS(dB)":['min']}))
    
    # Flight stats
    duration = pd.to_timedelta(df["datetime"].max() - df["datetime"].min(), unit='s')
    #st.write("Flight time = ", getFlightTime(duration))
    
    # Create graph
    layout = dict(
        hoversubplots="axis",
        hovermode="x",
        grid=dict(rows=5, columns=1),
        height=700
    )
    
    data = [
        go.Scatter(x=df["duration"] , y=df[conf['Altitude']], mode='lines', name=conf['Altitude'], yaxis="y1",xaxis="x"),
        go.Scatter(x=df["duration"] , y=df[conf['VSpd']], mode='lines', name=conf['VSpd'], yaxis="y2",xaxis="x"),
        go.Scatter(x=df["duration"] , y=df[conf['RQly']], mode='lines', name=conf['RQly'], yaxis="y3",xaxis="x"),
        go.Scatter(x=df["duration"] , y=df[conf['RSSI1']], mode='lines', name=conf['RSSI1'], yaxis="y4",xaxis="x"),
        go.Scatter(x=df["duration"] , y=df[conf['RSSI2']], mode='lines', name=conf['RSSI2'], yaxis="y4",xaxis="x"),
        go.Scatter(x=df["duration"] , y=df[conf['Antenna']], mode='lines', name=conf['Antenna'], yaxis="y5",xaxis="x"),
    ]
    
    fig = go.Figure(data=data, layout=layout)
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    # Find peaks
    #peaks = df.loc[df["Alt(m)"] == df["Alt(m)"].rolling(30, center=True).max()]
    #st.write(peaks[["Alt(m)","duration"]])

    # Display max altitude reach
    maxAlt = df[conf['Altitude']].max()
    launchAlt = df[conf['Altitude']].head().max()
    if df.iloc[df[conf['Altitude']].idxmax()]["duration"] != df.iloc[df[conf['Altitude']].head(10).idxmax()]["duration"]:
        fig.add_annotation(x=df.iloc[df[conf['Altitude']].idxmax()]["duration"] ,
                            y=maxAlt, showarrow=True,
                            text="max = "+str(maxAlt)+"m")
        fig.add_annotation(x=df.iloc[df[conf['Altitude']].head(10).idxmax()]["duration"] ,
                            y=launchAlt, showarrow=True,
                            text="launch = "+str(launchAlt)+"m")
    else:
        fig.add_annotation(x=df.iloc[df[conf['Altitude']].idxmax()]["duration"] ,
                            y=maxAlt, showarrow=True,
                            text="max = launch = "+str(maxAlt)+"m")
        
    fig.update_layout(hovermode='x unified', xaxis_tickformat="%H:%M:%S", yaxis_fixedrange=True)
    fig.update_xaxes(showspikes=True, spikemode="across")

    st.plotly_chart(fig, use_container_width=True)

def loadConfigEdgeTx():
    conf = {'Date': 'Date',
            'Time': 'Time',
            'Altitude' : 'Alt(m)',
            'RSSI1': '1RSS(dB)',
            'RSSI2': '2RSS(dB)',
            'RQly': 'RQly(%)',
            'TPwr': 'TPWR(mW)',
            'VSpd': 'VSpd(m/s)',
            'Antenna': 'Antenna'
            }
    return conf
def loadConfigEthos():
    conf = {'Date': 'Date',
            'Time': 'Time',
            'Altitude' : 'Altitude(m)',
            'RSSI1': 'Rx RSSI1(dB)',
            'RSSI2': 'Rx RSSI2(dB)',
            'RQly': 'Rx Quality(%)',
            'TPwr': 'Tx Power(mW)',
            'VSpd': 'VSpeed(m/s)',
            'Antenna': 'Antenna'
            }
    return conf


def startViewer():
    st.set_page_config(layout="wide")
    st.title("EdgeTX log viewer")

    radioType = st.radio("What's your radio?", ["EdgeTx", "Ethos"], index=1)
    if radioType == 'EdgeTx':
        conf = loadConfigEdgeTx()
    else:
        conf = loadConfigEthos()


    print()
    

    with st.form("my-form", clear_on_submit=True):
            uploaded_files = st.file_uploader("upload file", accept_multiple_files=True)
            submitted = st.form_submit_button("submit")
    if len(uploaded_files)>0:
        # Summary
        st.write("Summary of my " + str(len(uploaded_files)) + " flights:")
        dfSummary=[]
        df1=[]
        df2=[]
        for file in uploaded_files:
            df1 = pd.read_csv(file, dtype={conf['Date']: str, conf['Time']: str}) # open csv file(s)
            df1['datetime'] = pd.to_datetime(df1.pop(conf['Date']) + ' ' + df1.pop(conf['Time']), format="%Y-%m-%d %H:%M:%S.%f") # merge date time column
            
            df2.append(df1)
            
            # Flight stats
            duration = pd.to_timedelta(df1["datetime"].max() - df1["datetime"].min(), unit='s')
            launchHeight = df1[conf['Altitude']].head(10).max() # highest value in the first 10s
            newRow = {'Filename':file.name,
                      'Flight time':getFlightTime(duration), 
                      'Launch height (m)':launchHeight, 
                      'Max altitude (m)':df1[conf['Altitude']].max(), 
                      'Min RSSI1 (dB)':df1[conf['RSSI1']].min(), 
                      'Min RSSI2 (dB)':df1[conf['RSSI2']].min(), 
                      'Min RQly (%)':df1[conf['RQly']].min(), 
                      'Max TPWR (mW)':df1[conf['TPwr']].max()
                      }
            dfSummary.append(newRow)
            
        # Display flights summary
        data = pd.DataFrame(dfSummary)

        selection = aggrid_interactive_table(data)

        # Display flight graph only when 1 flight is selected
        if selection.grid_state is not None:
            if "rowSelection" in selection.grid_state:
                st.write("Flight graph")
                displayFlightGraph(df2[int(selection.selected_rows_id[0])], conf)

if __name__ == '__main__':
    startViewer()
