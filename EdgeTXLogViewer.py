import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import time


def getFlightTime(duration):
    flightTime = duration.total_seconds()
    if flightTime < 60:
        flightTime = time.strftime("%Ss", time.gmtime(flightTime))
    elif flightTime < 3600:
        flightTime = time.strftime("%Mm%Ss", time.gmtime(flightTime))
    else:
        flightTime = time.strftime("%Hh%Mm%Ss", time.gmtime(flightTime))
    return flightTime




st.title("EdgeTX log viewer")

#uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
with st.form("my-form", clear_on_submit=True):
        uploaded_files = st.file_uploader("upload file", accept_multiple_files=True)
        submitted = st.form_submit_button("submit")
if uploaded_files is not None:
    # Summary
    st.write("Flights summary:")
    dfSummary=[]
    df1=[]
    df2=[]
    for file in uploaded_files:
        # Check if file already treated
        #if not any(d['Filename'] == file.name for d in dfSummary):
        df1 = pd.read_csv(file, parse_dates={'date':["Date","Time"]}) # open csv file(s) and merge date time column
        df2.append(df1)
        
        # Flight stats
        duration = pd.to_timedelta(df1["date"].max() - df1["date"].min(), unit='s')
        newRow = {'Filename':file.name,'Flight time':getFlightTime(duration), 'Max altitude':df1["Alt(m)"].max(), 'Min RSSI':df1["1RSS(dB)"].min(), 'Min RQly':df1["RQly(%)"].min(), 'Max TPWR':df1["TPWR(mW)"].max()}
        dfSummary.append(newRow)
        
    # Display flights summary
    data = pd.DataFrame(dfSummary)
    if len(data)>0: st.write(data)
    



    for i in range(len(uploaded_files)):
        df = df2[i] #pd.read_csv(uploaded_files[i], parse_dates={'date':["Date","Time"]}) # open csv file(s) and merge date time column
        
        # Create duration time
        position = df.columns.get_loc('date')
        df['duration'] = df.iloc[1:, position] - df.iat[0, position]+ pd.to_datetime('1970/01/01')
        
        # Create stats
        #st.write(df.agg({"Alt(m)":['max'], "1RSS(dB)":['min'], "2RSS(dB)":['min'], "RQly(%)":['min'], "TPWR(mW)":['max'], "1RSS(dB)":['min']}))
        
        # Flight stats
        duration = pd.to_timedelta(df["date"].max() - df["date"].min(), unit='s')
        #st.write("Flight time = ", getFlightTime(duration))
        
        # Create graph
        layout = dict(
            hoversubplots="axis",
            #title="Flight " + str(i) + " / duration = " + getFlightTime(duration),
            hovermode="x",
            grid=dict(rows=3, columns=1),
            height=700
        )
        data = [
            go.Scatter(x=df["duration"] , y=df['Alt(m)'], mode='lines', name='Alt(m)', yaxis="y1",xaxis="x"),
            go.Scatter(x=df["duration"] , y=df['VSpd(m/s)'], mode='lines', name='VSpd(m/s)', yaxis="y1",xaxis="x"),
            go.Scatter(x=df["duration"] , y=df['RQly(%)'], mode='lines', name='RQly(%)', yaxis="y2",xaxis="x"),
            go.Scatter(x=df["duration"] , y=df['1RSS(dB)'], mode='lines', name='1RSS(dB)', yaxis="y2",xaxis="x")
            #go.Scatter(x=df["duration"] + pd.to_datetime('1970/01/01'), y=df['Alt(m)'], mode='lines', name='Alt(m)', yaxis="y1",xaxis="x"),
            #go.Scatter(x=df["duration"] + pd.to_datetime('1970/01/01'), y=df['VSpd(m/s)'], mode='lines', name='VSpd(m/s)', yaxis="y1",xaxis="x"),
            #go.Scatter(x=df["duration"] + pd.to_datetime('1970/01/01'), y=df['RQly(%)'], mode='lines', name='RQly(%)', yaxis="y2",xaxis="x"),
            #go.Scatter(x=df["duration"] + pd.to_datetime('1970/01/01'), y=df['1RSS(dB)'], mode='lines', name='1RSS(dB)', yaxis="y2",xaxis="x")
        ]
        fig = go.Figure(data=data, layout=layout)

        # Find peaks
        #peaks = df.loc[df["Alt(m)"] == df["Alt(m)"].rolling(30, center=True).max()]
        #st.write(peaks[["Alt(m)","duration"]])

        # Display max altitude reach
        maxAlt = df["Alt(m)"].max()
        fig.add_annotation(x=df.iloc[df["Alt(m)"].idxmax()]["duration"] ,
                            y=maxAlt, showarrow=True,
                            text="max = "+str(maxAlt)+"m")

        fig.update_layout(hovermode='x unified', xaxis_tickformat="%H:%M:%S", yaxis_fixedrange=True)
        fig.update_xaxes(showspikes=True, spikemode="across")

        with st.expander("Flight " + str(i) + " / " + getFlightTime(duration)):
            st.plotly_chart(fig, use_container_width=True)
        